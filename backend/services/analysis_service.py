from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.config.settings import get_settings
from backend.db.base import utcnow
from backend.db.models import AnalysisFinding, AnalysisRun, ConversationMessage, ConversationSession, FindingEvidence
from backend.domain.enums import AnalysisModuleKey, AnalysisStatus, FindingType, RiskLevel, TriggerSource
from backend.model_adapters.persona_analysis import invoke_persona_analysis
from backend.schemas.persona_analysis import (
    AnalysisResultData,
    EvidenceItem,
    FindingItem,
    PromptVersionSchema,
    RiskAssessment,
    SmartReply,
    StructuredAnalysisOutput,
    StructuredEvidenceInput,
    StructuredFindingInput,
    StructuredSmartReplyInput,
)
from backend.services.boundary_agent_service import maybe_run_boundary_agent
from backend.services.model_service import get_default_model_option, get_model_config, get_model_option
from backend.services.prompt_service import assemble_full_prompt, get_active_prompt_version, get_prompt_version_by_id
from backend.services.reference_kb_service import format_reference_hits, search_reference_chunks


MAX_ANALYSIS_MESSAGES = 120
MAX_ANALYSIS_TOTAL_CONTENT_CHARS = 12000
MAX_SINGLE_MESSAGE_CONTENT_CHARS = 600
HEAD_MESSAGE_PRESERVE_COUNT = 8


def create_pending_analysis(
    db: Session,
    *,
    session_obj: ConversationSession,
    model_key: str,
    prompt_version_id: str,
    trigger_source: TriggerSource,
    module_key: AnalysisModuleKey = AnalysisModuleKey.USER_PROFILE_AND_REPLY,
) -> AnalysisResultData:
    prompt_version = get_prompt_version_by_id(db, prompt_version_id)
    if prompt_version is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="未找到 Prompt 版本")

    model_option = get_model_option(model_key)
    model_config = get_model_config(model_key)
    messages = list(
        db.scalars(
            select(ConversationMessage)
            .where(ConversationMessage.session_id == session_obj.id)
            .order_by(ConversationMessage.message_index.asc())
        )
    )
    if not messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="当前会话没有可分析的消息，请先导入聊天记录。",
        )

    analysis_run = AnalysisRun(
        session_id=session_obj.id,
        prompt_version_id=prompt_version.id,
        provider_key=model_option.provider_key,
        model_key=model_option.model_key,
        trigger_source=trigger_source.value,
        module_key=module_key.value,
        analysis_status=AnalysisStatus.RUNNING.value,
        summary="正在执行分析。",
        risk_level=RiskLevel.UNKNOWN.value,
        risk_score=0,
    )
    session_obj.analysis_status = AnalysisStatus.RUNNING.value
    session_obj.latest_activity_at = utcnow()
    db.add(analysis_run)
    db.add(session_obj)
    db.commit()
    db.refresh(analysis_run)

    session_obj.latest_analysis_run_id = analysis_run.id
    db.add(session_obj)
    db.commit()
    db.refresh(session_obj)

    try:
        invocation_result = invoke_persona_analysis(
            settings=get_settings(),
            model_config=model_config,
            prompt_content=assemble_full_prompt(
                module_key, prompt_version.content),
            session_id=session_obj.id,
            analysis_input=_build_analysis_input(session_obj, messages),
        )
        structured_output = _normalize_output_for_module(
            invocation_result.structured_output,
            module_key,
        )
        _append_boundary_notes_if_needed(
            session_obj_id=session_obj.id,
            structured_output=structured_output,
            model_config=model_config,
            module_key=module_key,
        )
        structured_output.session_id = session_obj.id

        _persist_analysis_output(
            db,
            analysis_run=analysis_run,
            messages=messages,
            structured_output=structured_output,
        )
        analysis_run.analysis_status = AnalysisStatus.SUCCEEDED.value
        analysis_run.summary = structured_output.conversation_summary
        analysis_run.risk_level = structured_output.risk_assessment.level.value
        analysis_run.risk_score = structured_output.risk_assessment.score
        analysis_run.raw_response = invocation_result.raw_response
        analysis_run.error_message = None
        session_obj.analysis_status = AnalysisStatus.SUCCEEDED.value
        session_obj.latest_activity_at = utcnow()
        db.add(analysis_run)
        db.add(session_obj)
        db.commit()
    except HTTPException:
        raise
    except Exception as exc:
        analysis_run.analysis_status = AnalysisStatus.FAILED.value
        analysis_run.summary = "分析执行失败。"
        analysis_run.error_message = str(exc)
        session_obj.analysis_status = AnalysisStatus.FAILED.value
        session_obj.latest_activity_at = utcnow()
        db.add(analysis_run)
        db.add(session_obj)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"分析执行失败：{exc}",
        ) from exc

    return build_analysis_result(db, session_obj.id)


def build_analysis_result(
    db: Session,
    session_id: str,
    latest_run: AnalysisRun | None = None,
    module_key: AnalysisModuleKey | None = None,
) -> AnalysisResultData:
    session_obj = db.get(ConversationSession, session_id)
    if session_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="未找到会话")

    prompt_version = get_active_prompt_version(
        db, module_key or AnalysisModuleKey.USER_PROFILE_AND_REPLY)
    model_option = get_default_model_option()

    if latest_run is None:
        run_query = (
            select(AnalysisRun)
            .options(
                selectinload(AnalysisRun.findings).selectinload(
                    AnalysisFinding.evidences),
            )
            .where(AnalysisRun.session_id == session_id)
        )
        if module_key is not None:
            run_query = run_query.where(
                AnalysisRun.module_key == module_key.value)
        elif session_obj.latest_analysis_run_id:
            run_query = run_query.where(
                AnalysisRun.id == session_obj.latest_analysis_run_id)
        latest_run = db.scalar(
            run_query.order_by(AnalysisRun.created_at.desc())
        )

    if latest_run is not None:
        model_option = get_model_option(latest_run.model_key)
        if latest_run.prompt_version_id:
            prompt_version_model = get_prompt_version_by_id(
                db, latest_run.prompt_version_id)
            if prompt_version_model is not None:
                prompt_version = prompt_version_model

    findings_by_type: dict[str, list[FindingItem]] = defaultdict(list)
    smart_replies: list[SmartReply] = []
    risk_assessment = RiskAssessment(
        level=RiskLevel.UNKNOWN,
        score=0,
        summary="尚未生成风险评估。",
        reason="当前后端骨架仅完成数据结构与路由，LLM 分析流水线待接入。",
        evidences=[],
    )

    if latest_run is not None:
        for finding in latest_run.findings:
            evidences = [_evidence_to_schema(item)
                         for item in finding.evidences]
            if finding.finding_type == FindingType.SMART_REPLY.value:
                smart_replies.append(
                    SmartReply(
                        reply_id=finding.id,
                        style=finding.title,
                        content=finding.summary,
                        reason=finding.reason,
                        evidences=evidences,
                    )
                )
                continue

            if finding.finding_type == FindingType.RISK_REASON.value:
                risk_assessment = RiskAssessment(
                    level=RiskLevel(latest_run.risk_level),
                    score=latest_run.risk_score,
                    summary=finding.summary,
                    reason=finding.reason,
                    evidences=evidences,
                )
                continue

            findings_by_type[finding.finding_type].append(
                FindingItem(
                    finding_id=finding.id,
                    title=finding.title,
                    summary=finding.summary,
                    reason=finding.reason,
                    confidence=finding.confidence,
                    severity=finding.severity,
                    resolution_status=finding.resolution_status,
                    evidences=evidences,
                )
            )

    return AnalysisResultData(
        analysis_run_id=latest_run.id if latest_run else None,
        session_id=session_obj.id,
        analysis_status=AnalysisStatus(
            latest_run.analysis_status) if latest_run else AnalysisStatus.PENDING,
        model=model_option,
        prompt_version=PromptVersionSchema(
            prompt_version_id=prompt_version.id,
            tool_key=prompt_version.tool_key,
            task_key=prompt_version.task_key,
            version_label=prompt_version.version_label,
            version_note=prompt_version.version_note,
            content=prompt_version.content,
            is_active=prompt_version.is_active,
            created_at=prompt_version.created_at,
            updated_at=prompt_version.updated_at,
        ),
        persona_tags=findings_by_type[FindingType.PERSONA_TAG.value],
        pain_points=findings_by_type[FindingType.PAIN_POINT.value],
        deal_closing_points=findings_by_type[FindingType.DEAL_CLOSING_POINT.value],
        churn_points=findings_by_type[FindingType.CHURN_POINT.value],
        high_frequency_points=findings_by_type[FindingType.HIGH_FREQUENCY_POINT.value],
        risk_assessment=risk_assessment,
        smart_replies=smart_replies,
        summary=latest_run.summary if latest_run else "尚未触发分析。",
    )


def _evidence_to_schema(evidence: FindingEvidence) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence.id,
        message_id=evidence.message_id,
        message_index=evidence.message_index,
        speaker=evidence.speaker,
        speaker_role=evidence.speaker_role,
        quote=evidence.quote,
        timestamp=evidence.timestamp_text,
        note=evidence.note,
    )


def _build_analysis_input(session_obj: ConversationSession, messages: list[ConversationMessage]) -> dict:
    teacher_name = next(
        (message.speaker_name for message in messages if message.speaker_role ==
         "teacher" and message.speaker_name),
        None,
    )
    student_name = next(
        (message.speaker_name for message in messages if message.speaker_role ==
         "student" and message.speaker_name),
        None,
    )

    compact_messages = [
        {
            "message_index": message.message_index,
            "speaker_role": message.speaker_role,
            "content": _trim_message_content(message.content),
        }
        for message in messages
        if message.content.strip()
    ]
    selected_messages, omitted_message_count = _select_messages_for_analysis(
        compact_messages)

    result: dict = {
        "teacher_name": teacher_name,
        "student_name": student_name,
        "messages": selected_messages,
    }
    if omitted_message_count > 0:
        result["truncation_note"] = (
            f"原始{len(compact_messages)}条消息已裁剪为{len(selected_messages)}条（保留首尾）"
        )
    return result


def _trim_message_content(content: str) -> str:
    normalized = content.strip()
    if len(normalized) <= MAX_SINGLE_MESSAGE_CONTENT_CHARS:
        return normalized

    omitted_chars = len(normalized) - MAX_SINGLE_MESSAGE_CONTENT_CHARS
    return f"{normalized[:MAX_SINGLE_MESSAGE_CONTENT_CHARS]}...(已截断 {omitted_chars} 字)"


def _select_messages_for_analysis(messages: list[dict[str, str | int | None]]) -> tuple[list[dict[str, str | int | None]], int]:
    if not messages:
        return [], 0

    total_content_chars = sum(len(str(item.get("content") or ""))
                              for item in messages)
    if len(messages) <= MAX_ANALYSIS_MESSAGES and total_content_chars <= MAX_ANALYSIS_TOTAL_CONTENT_CHARS:
        return messages, 0

    head_count = min(HEAD_MESSAGE_PRESERVE_COUNT,
                     len(messages), MAX_ANALYSIS_MESSAGES)
    head_messages = messages[:head_count]
    selected_tail: list[dict[str, str | int | None]] = []

    remaining_count_budget = MAX_ANALYSIS_MESSAGES - head_count
    remaining_chars_budget = MAX_ANALYSIS_TOTAL_CONTENT_CHARS - sum(
        len(str(item.get("content") or "")) for item in head_messages)

    for item in reversed(messages[head_count:]):
        if remaining_count_budget <= 0:
            break
        if remaining_chars_budget <= 0:
            break

        content = str(item.get("content") or "")
        if len(content) <= remaining_chars_budget:
            selected_tail.append(item)
            remaining_count_budget -= 1
            remaining_chars_budget -= len(content)
            continue

        if not selected_tail and remaining_chars_budget >= 80:
            truncated_item = dict(item)
            truncated_item["content"] = _trim_message_content(
                content[:remaining_chars_budget])
            selected_tail.append(truncated_item)
            remaining_count_budget -= 1
            remaining_chars_budget = 0
        break

    selected_messages = head_messages + list(reversed(selected_tail))
    omitted_message_count = max(0, len(messages) - len(selected_messages))
    return selected_messages, omitted_message_count


def _normalize_output_for_module(
    structured_output: StructuredAnalysisOutput,
    module_key: AnalysisModuleKey,
) -> StructuredAnalysisOutput:
    if module_key == AnalysisModuleKey.USER_PROFILE_AND_REPLY:
        structured_output.pain_points = []
        structured_output.deal_closing_points = []
        structured_output.churn_points = []
        structured_output.high_frequency_points = []
        structured_output.risk_assessment.level = RiskLevel.UNKNOWN
        structured_output.risk_assessment.score = 0
        structured_output.risk_assessment.summary = "本模块不输出风险评估。"
        structured_output.risk_assessment.reason = "当前运行模块为 user_profile_and_reply。"
        structured_output.risk_assessment.evidences = []
        return structured_output

    if module_key == AnalysisModuleKey.RISK_DETECTION:
        structured_output.persona_tags = []
        structured_output.pain_points = []
        structured_output.deal_closing_points = []
        structured_output.churn_points = []
        structured_output.high_frequency_points = []
        structured_output.smart_replies = []
        return structured_output

    if module_key == AnalysisModuleKey.FUNNEL_NODES:
        structured_output.persona_tags = []
        structured_output.smart_replies = []
        structured_output.risk_assessment.level = RiskLevel.UNKNOWN
        structured_output.risk_assessment.score = 0
        structured_output.risk_assessment.summary = "本模块不输出风险评估。"
        structured_output.risk_assessment.reason = "当前运行模块为 funnel_nodes。"
        structured_output.risk_assessment.evidences = []
        return structured_output

    # Unknown module: return output unchanged
    return structured_output


def _append_boundary_notes_if_needed(
    *,
    session_obj_id: str,
    structured_output: StructuredAnalysisOutput,
    model_config,
    module_key: AnalysisModuleKey,
) -> None:
    if not _is_boundary_ambiguous(structured_output, module_key):
        return

    query = _build_ambiguity_query(structured_output, module_key)
    chunks = search_reference_chunks(query, top_k=3)
    if chunks:
        structured_output.parser_notes.append(
            f"knowledge_hits={'; '.join(format_reference_hits(chunks))}"
        )

    agent_note = maybe_run_boundary_agent(
        settings=get_settings(),
        model_config=model_config,
        module_key=module_key.value,
        user_query=query,
    )
    if agent_note:
        structured_output.parser_notes.append(
            f"boundary_resolution[{session_obj_id}]={agent_note}"
        )


def _is_boundary_ambiguous(
    structured_output: StructuredAnalysisOutput,
    module_key: AnalysisModuleKey,
) -> bool:
    if module_key == AnalysisModuleKey.RISK_DETECTION:
        return structured_output.risk_assessment.level == RiskLevel.UNKNOWN

    if module_key == AnalysisModuleKey.USER_PROFILE_AND_REPLY:
        low_confidence = any(
            item.confidence < 0.6 for item in structured_output.persona_tags)
        return low_confidence or (not structured_output.persona_tags and not structured_output.smart_replies)

    if module_key == AnalysisModuleKey.FUNNEL_NODES:
        total_findings = (
            len(structured_output.pain_points)
            + len(structured_output.deal_closing_points)
            + len(structured_output.churn_points)
            + len(structured_output.high_frequency_points)
        )
        return total_findings == 0

    return False


def _build_ambiguity_query(
    structured_output: StructuredAnalysisOutput,
    module_key: AnalysisModuleKey,
) -> str:
    return (
        f"module={module_key.value}; summary={structured_output.conversation_summary}; "
        "请提供边界判定依据。"
    )


def _persist_analysis_output(
    db: Session,
    *,
    analysis_run: AnalysisRun,
    messages: list[ConversationMessage],
    structured_output: StructuredAnalysisOutput,
) -> None:
    message_by_index = {message.message_index: message for message in messages}
    sort_order = 0

    for finding in _flatten_findings(structured_output):
        sort_order += 1
        db.add(_build_finding_model(analysis_run.id,
               finding[0], finding[1], message_by_index, sort_order))

    risk_finding = AnalysisFinding(
        analysis_run_id=analysis_run.id,
        finding_type=FindingType.RISK_REASON.value,
        title=structured_output.risk_assessment.level.value,
        summary=structured_output.risk_assessment.summary,
        reason=structured_output.risk_assessment.reason,
        confidence=1.0,
        severity=None,
        resolution_status=None,
        sort_order=sort_order + 1,
    )
    db.add(risk_finding)
    db.flush()
    for evidence in structured_output.risk_assessment.evidences:
        db.add(_build_evidence_model(risk_finding.id, evidence, message_by_index))

    for reply_offset, smart_reply in enumerate(structured_output.smart_replies, start=sort_order + 2):
        reply_finding = AnalysisFinding(
            analysis_run_id=analysis_run.id,
            finding_type=FindingType.SMART_REPLY.value,
            title=smart_reply.style,
            summary=smart_reply.content,
            reason=smart_reply.reason,
            confidence=1.0,
            severity=None,
            resolution_status=None,
            sort_order=reply_offset,
        )
        db.add(reply_finding)
        db.flush()
        for evidence in smart_reply.evidences:
            db.add(_build_evidence_model(
                reply_finding.id, evidence, message_by_index))


def _flatten_findings(structured_output: StructuredAnalysisOutput) -> Iterable[tuple[FindingType, StructuredFindingInput]]:
    mapping = [
        (FindingType.PERSONA_TAG, structured_output.persona_tags),
        (FindingType.PAIN_POINT, structured_output.pain_points),
        (FindingType.DEAL_CLOSING_POINT, structured_output.deal_closing_points),
        (FindingType.CHURN_POINT, structured_output.churn_points),
        (FindingType.HIGH_FREQUENCY_POINT, structured_output.high_frequency_points),
    ]
    for finding_type, items in mapping:
        for item in items:
            yield finding_type, item


def _build_finding_model(
    analysis_run_id: str,
    finding_type: FindingType,
    finding: StructuredFindingInput,
    message_by_index: dict[int, ConversationMessage],
    sort_order: int,
) -> AnalysisFinding:
    finding_model = AnalysisFinding(
        analysis_run_id=analysis_run_id,
        finding_type=finding_type.value,
        title=finding.title,
        summary=finding.summary,
        reason=finding.reason,
        confidence=finding.confidence,
        severity=finding.severity.value if finding.severity else None,
        resolution_status=finding.resolution_status.value if finding.resolution_status else None,
        sort_order=sort_order,
    )
    return _attach_evidences(finding_model, finding.evidences, message_by_index)


def _attach_evidences(
    finding_model: AnalysisFinding,
    evidences: list[StructuredEvidenceInput],
    message_by_index: dict[int, ConversationMessage],
) -> AnalysisFinding:
    attached_evidences: list[FindingEvidence] = []
    for evidence in evidences:
        attached_evidences.append(_build_evidence_model(
            None, evidence, message_by_index))
    finding_model.evidences = attached_evidences
    return finding_model


def _build_evidence_model(
    finding_id: str | None,
    evidence: StructuredEvidenceInput,
    message_by_index: dict[int, ConversationMessage],
) -> FindingEvidence:
    matched_message = message_by_index.get(
        evidence.message_index) if evidence.message_index else None
    return FindingEvidence(
        finding_id=finding_id,
        message_id=matched_message.id if matched_message else None,
        message_index=evidence.message_index,
        speaker=evidence.speaker or (
            matched_message.speaker_name if matched_message else None),
        speaker_role=evidence.speaker_role.value if evidence.speaker_role else (
            matched_message.speaker_role if matched_message else None),
        quote=evidence.quote,
        timestamp_text=evidence.timestamp or (
            matched_message.timestamp_text if matched_message else None),
        note=evidence.note,
    )
