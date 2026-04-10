import json

from backend.config.settings import clear_settings_cache
from backend.db.models import AnalysisFinding, FindingEvidence
from backend.db.session import clear_db_caches, get_session_factory
from backend.domain.enums import (
    AnalysisModuleKey,
    AnalysisStatus,
    FindingType,
    ResolutionStatus,
    RiskLevel,
    SeverityLevel,
    SourceType,
    SpeakerRole,
    TriggerSource,
)
from backend.schemas.persona_analysis import (
    StructuredAnalysisOutput,
    StructuredEvidenceInput,
    StructuredFindingInput,
    StructuredRiskAssessmentInput,
    StructuredSmartReplyInput,
)
from backend.services.analysis_service import create_pending_analysis
from backend.services.bootstrap_service import initialize_database, seed_defaults
from backend.services.conversation_service import import_text_as_session, get_session_or_404
from backend.services.model_service import get_default_model_option
from backend.services.prompt_service import get_active_prompt_version


def test_analysis_pipeline_persists_findings_and_evidences(tmp_path, monkeypatch) -> None:
    test_database_path = tmp_path / "persona-analysis-run.db"
    monkeypatch.setenv("LANG_MA_DATABASE_URL",
                       f"sqlite:///{test_database_path}")
    clear_settings_cache()
    clear_db_caches()
    initialize_database()

    session_factory = get_session_factory()

    def fake_invoke_persona_analysis(*, settings, model_config, prompt_content, session_id, analysis_input):
        del settings, model_config, prompt_content
        output = StructuredAnalysisOutput(
            session_id=session_id,
            conversation_summary="用户围绕套读与考研时间线展开咨询，重点关心毕业节点与学分规则。",
            parser_notes=[],
            persona_tags=[
                StructuredFindingInput(
                    title="考研导向",
                    summary="用户咨询目标明确指向套读后考研。",
                    reason="用户在开场即明确表达想套读并尽快考研。",
                    confidence=0.95,
                    evidences=[
                        StructuredEvidenceInput(
                            message_index=2,
                            speaker="缪函澄-电子科技大学计算机(缪)",
                            speaker_role=SpeakerRole.STUDENT,
                            timestamp="2025-09-03 11:41",
                            quote="老师，我现在是大一专科，想要直接转本套读，然后大三直接考研",
                        )
                    ],
                )
            ],
            pain_points=[
                StructuredFindingInput(
                    title="时间规划焦虑",
                    summary="用户不确定专科毕业、本科毕业和考研时间线是否能衔接。",
                    reason="用户一开始就提出大三直接考研的目标，后续持续追问可行性与注意事项。",
                    confidence=0.91,
                    severity=SeverityLevel.HIGH,
                    resolution_status=ResolutionStatus.PARTIALLY_RESOLVED,
                    evidences=[
                        StructuredEvidenceInput(
                            message_index=2,
                            speaker="缪函澄-电子科技大学计算机(缪)",
                            speaker_role=SpeakerRole.STUDENT,
                            timestamp="2025-09-03 11:41",
                            quote="老师，我现在是大一专科，想要直接转本套读，然后大三直接考研",
                        ),
                        StructuredEvidenceInput(
                            message_index=9,
                            speaker="缪函澄-电子科技大学计算机(缪)",
                            speaker_role=SpeakerRole.STUDENT,
                            timestamp="2025-09-03 11:57",
                            quote="细节上不知道有没有什么问题以及注意事项，所以来请教一下",
                        ),
                    ],
                )
            ],
            deal_closing_points=[],
            churn_points=[],
            high_frequency_points=[
                StructuredFindingInput(
                    title="前置学历与毕业申请规则",
                    summary="该会话命中了自考咨询中的典型流程型高频问题。",
                    reason="用户持续询问前置学历审核、学分要求和毕业申请时间。",
                    confidence=0.88,
                    evidences=[
                        StructuredEvidenceInput(
                            message_index=12,
                            speaker="缪函澄-电子科技大学计算机(缪)",
                            speaker_role=SpeakerRole.STUDENT,
                            timestamp="2025-09-03 11:58",
                            quote="我查询的是要学满学分才能申请，学分时只要课程及格就能拿满吗？",
                        )
                    ],
                )
            ],
            risk_assessment=StructuredRiskAssessmentInput(
                level=RiskLevel.MEDIUM,
                score=42,
                summary="当前存在中等沟通阻塞风险。",
                reason="用户目标比较激进，且对关键政策节点理解不足，如果解释不清容易产生误判。",
                evidences=[
                    StructuredEvidenceInput(
                        message_index=3,
                        speaker="缪函澄-电子科技大学计算机(缪)",
                        speaker_role=SpeakerRole.STUDENT,
                        timestamp="2025-09-03 11:42",
                        quote="为什么？",
                    )
                ],
            ),
            smart_replies=[
                StructuredSmartReplyInput(
                    style="专业型",
                    content="你的目标可以继续推进，但关键不是大三直接拿本科结果，而是按专科毕业、本科申毕、学位证和考研审核时间逐段去排。",
                    reason="用户当前最需要的是清晰时间线，而不是泛泛鼓励。",
                    evidences=[
                        StructuredEvidenceInput(
                            message_index=2,
                            speaker="缪函澄-电子科技大学计算机(缪)",
                            speaker_role=SpeakerRole.STUDENT,
                            timestamp="2025-09-03 11:41",
                            quote="老师，我现在是大一专科，想要直接转本套读，然后大三直接考研",
                        )
                    ],
                )
            ],
        )

        class Result:
            structured_output = output
            raw_response = json.dumps(output.model_dump(), ensure_ascii=False)

        return Result()

    monkeypatch.setattr(
        "backend.services.analysis_service.invoke_persona_analysis", fake_invoke_persona_analysis)

    with session_factory() as db:
        seed_defaults(db)
        import_result = import_text_as_session(
            db,
            raw_text="老师\n2025-01-01 10:00\n你好\n学生\n2025-01-01 10:01\n我现在是大一专科，想要直接转本套读，然后大三直接考研\n学生\n2025-01-01 10:02\n为什么？\n学生\n2025-01-01 10:03\n细节上不知道有没有什么问题以及注意事项，所以来请教一下\n学生\n2025-01-01 10:04\n我查询的是要学满学分才能申请，学分时只要课程及格就能拿满吗？",
            title="测试分析",
            folder_id=None,
            source_type=SourceType.PASTED_TEXT,
            original_file_name=None,
            mime_type="text/plain",
            auto_analyze=False,
            model_key=None,
            prompt_version_id=None,
        )
        assert import_result.parse_status.value == "parsed"

        session_obj = get_session_or_404(db, import_result.session.item_id)
        prompt_version = get_active_prompt_version(
            db, AnalysisModuleKey.FUNNEL_NODES)
        model_option = get_default_model_option()

        result = create_pending_analysis(
            db,
            session_obj=session_obj,
            model_key=model_option.model_key,
            prompt_version_id=prompt_version.id,
            trigger_source=TriggerSource.MANUAL_RERUN,
            module_key=AnalysisModuleKey.FUNNEL_NODES,
        )

        assert result.analysis_status == AnalysisStatus.SUCCEEDED
        # FUNNEL_NODES clears persona_tags
        assert len(result.persona_tags) == 0
        assert len(result.pain_points) == 1
        assert len(result.high_frequency_points) == 1
        assert result.risk_assessment.level.value == "unknown"  # FUNNEL_NODES clears risk
        # FUNNEL_NODES clears smart_replies
        assert len(result.smart_replies) == 0

        findings = db.query(AnalysisFinding).all()
        evidences = db.query(FindingEvidence).all()
        assert any(item.finding_type ==
                   FindingType.PAIN_POINT.value for item in findings)
        # FUNNEL_NODES always stores a RISK_REASON placeholder (unknown/0)
        risk_findings = [item for item in findings
                         if item.finding_type == FindingType.RISK_REASON.value]
        assert risk_findings, "RISK_REASON placeholder should be persisted"
        assert risk_findings[0].title == "unknown"
        # FUNNEL_NODES module clears smart_replies before persistence
        assert not any(item.finding_type ==
                       FindingType.SMART_REPLY.value for item in findings)
        assert len(evidences) >= 2

    clear_settings_cache()
    clear_db_caches()


def test_analysis_payload_is_compact_for_long_conversation(tmp_path, monkeypatch) -> None:
    test_database_path = tmp_path / "persona-analysis-compact-input.db"
    monkeypatch.setenv("LANG_MA_DATABASE_URL",
                       f"sqlite:///{test_database_path}")
    clear_settings_cache()
    clear_db_caches()
    initialize_database()

    session_factory = get_session_factory()
    captured_payload: dict[str, object] = {}

    def fake_invoke_persona_analysis(*, settings, model_config, prompt_content, session_id, analysis_input):
        del settings, model_config, prompt_content
        captured_payload["analysis_input"] = analysis_input
        output = StructuredAnalysisOutput(
            session_id=session_id,
            conversation_summary="长会话已裁剪为可分析片段。",
            parser_notes=[],
            persona_tags=[],
            pain_points=[],
            deal_closing_points=[],
            churn_points=[],
            high_frequency_points=[],
            risk_assessment=StructuredRiskAssessmentInput(
                level=RiskLevel.UNKNOWN,
                score=0,
                summary="证据不足",
                reason="输入为必要片段，当前不输出风险结论。",
                evidences=[],
            ),
            smart_replies=[],
        )

        class Result:
            structured_output = output
            raw_response = json.dumps(output.model_dump(), ensure_ascii=False)

        return Result()

    monkeypatch.setattr(
        "backend.services.analysis_service.invoke_persona_analysis", fake_invoke_persona_analysis)

    with session_factory() as db:
        seed_defaults(db)
        raw_lines: list[str] = []
        for index in range(1, 281):
            speaker = "老师A" if index % 2 else "学生B"
            timestamp = f"2025-01-01 10:{index % 60:02d}"
            content = f"第{index}条消息 " + ("信息" * 120)
            raw_lines.extend([speaker, timestamp, content])

        import_result = import_text_as_session(
            db,
            raw_text="\n".join(raw_lines),
            title="长会话",
            folder_id=None,
            source_type=SourceType.PASTED_TEXT,
            original_file_name=None,
            mime_type="text/plain",
            auto_analyze=False,
            model_key=None,
            prompt_version_id=None,
        )

        session_obj = get_session_or_404(db, import_result.session.item_id)
        prompt_version = get_active_prompt_version(
            db, AnalysisModuleKey.USER_PROFILE_AND_REPLY)
        model_option = get_default_model_option()

        create_pending_analysis(
            db,
            session_obj=session_obj,
            model_key=model_option.model_key,
            prompt_version_id=prompt_version.id,
            trigger_source=TriggerSource.MANUAL_RERUN,
            module_key=AnalysisModuleKey.USER_PROFILE_AND_REPLY,
        )

    analysis_input = captured_payload["analysis_input"]
    assert isinstance(analysis_input, dict)

    messages = analysis_input["messages"]
    assert isinstance(messages, list)
    assert messages
    assert "session_id" not in analysis_input
    assert "input_meta" not in analysis_input
    assert "speaker_name" not in messages[0]
    assert "timestamp" not in messages[0]
    assert "truncation_note" in analysis_input
    assert len(messages) < 280
    assert messages[0]["message_index"] == 1
    assert messages[-1]["message_index"] >= 250

    total_content_chars = sum(len(str(item["content"])) for item in messages)
    assert total_content_chars <= 12000

    clear_settings_cache()
    clear_db_caches()
