from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any

from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from backend.config.settings import ModelOptionConfig, Settings
from backend.schemas.persona_analysis import StructuredAnalysisOutput


JSON_BLOCK_PATTERN = re.compile(r"```(?:json)?\s*(\{.*\})\s*```", re.DOTALL)


@dataclass(slots=True)
class AnalysisInvocationResult:
    structured_output: StructuredAnalysisOutput
    raw_response: str


def invoke_persona_analysis(
    *,
    settings: Settings,
    model_config: ModelOptionConfig,
    prompt_content: str,
    session_id: str,
    analysis_input: dict,
) -> AnalysisInvocationResult:
    if model_config.provider_key != "openai_compatible":
        raise RuntimeError(
            f"当前仅实现 openai_compatible 模型调用，暂不支持：{model_config.provider_key}")
    if not settings.openai_api_key:
        raise RuntimeError("未配置 OpenAI 兼容 API Key")

    chat_model = ChatOpenAI(
        model_name=model_config.api_model_name or model_config.model_key,
        openai_api_key=settings.openai_api_key,
        openai_api_base=settings.openai_base_url,
        temperature=model_config.temperature or 0.2,
        max_tokens=model_config.max_tokens,
        request_timeout=180,
        max_retries=0,
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=prompt_content),
            (
                "human",
                "以下是本次分析的对话内容（仅包含人员与对话，时间戳等元数据由后端补充）。"
                "请只基于已提供内容分析，不得臆造未提供的事实；证据不足时返回空数组或 unknown。"
                "请严格按照系统要求只输出 JSON：\n{input_json}",
            ),
        ]
    )
    chain = prompt | chat_model
    response = chain.invoke({"input_json": json.dumps(
        analysis_input, ensure_ascii=False, indent=2)})
    raw_response = _extract_text_content(response.content)
    json_payload = _extract_json_payload(raw_response)
    json_payload = _coerce_structured_payload(
        json_payload,
        fallback_session_id=session_id,
    )
    structured_output = StructuredAnalysisOutput.model_validate(json_payload)
    return AnalysisInvocationResult(structured_output=structured_output, raw_response=raw_response)


def _extract_text_content(content: object) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        text_parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                text_parts.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                text_parts.append(item["text"])
        return "\n".join(part.strip() for part in text_parts if part.strip())
    return str(content).strip()


def _extract_json_payload(raw_response: str) -> dict:
    cleaned = raw_response.strip()
    if not cleaned:
        raise RuntimeError("模型未返回有效内容")

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    fenced_match = JSON_BLOCK_PATTERN.search(cleaned)
    if fenced_match:
        return json.loads(fenced_match.group(1))

    start_index = cleaned.find("{")
    end_index = cleaned.rfind("}")
    if start_index == -1 or end_index == -1 or end_index <= start_index:
        raise RuntimeError("模型未返回合法 JSON")
    return json.loads(cleaned[start_index:end_index + 1])


def _coerce_structured_payload(payload: Any, *, fallback_session_id: str) -> dict[str, Any]:
    source = payload if isinstance(payload, dict) else {}

    return {
        "session_id": _coerce_text(source.get("session_id"), fallback=fallback_session_id) or fallback_session_id,
        "conversation_summary": _coerce_text(
            source.get("conversation_summary", source.get("summary")),
            fallback="未提供会话摘要。",
        ),
        "parser_notes": _coerce_string_list(source.get("parser_notes")),
        "persona_tags": _coerce_findings(source.get("persona_tags")),
        "pain_points": _coerce_findings(source.get("pain_points")),
        "deal_closing_points": _coerce_findings(source.get("deal_closing_points")),
        "churn_points": _coerce_findings(source.get("churn_points")),
        "high_frequency_points": _coerce_findings(source.get("high_frequency_points")),
        "risk_assessment": _coerce_risk_assessment(source.get("risk_assessment")),
        "smart_replies": _coerce_smart_replies(source.get("smart_replies")),
    }


def _coerce_text(value: Any, *, fallback: str = "") -> str:
    if isinstance(value, str):
        text = value.strip()
        return text or fallback
    if isinstance(value, list):
        parts = [str(item).strip() for item in value if str(item).strip()]
        return "；".join(parts) if parts else fallback
    if value is None:
        return fallback
    text = str(value).strip()
    return text or fallback


def _coerce_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    single = _coerce_text(value)
    return [single] if single else []


def _coerce_confidence(value: Any) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return 0.7
    return max(0.0, min(confidence, 1.0))


def _coerce_int(value: Any, *, fallback: int | None = 0) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _coerce_evidences(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    evidences: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        quote = _coerce_text(
            item.get("quote", item.get("content", item.get("text"))),
            fallback="未提供原文证据。",
        )
        evidences.append(
            {
                "message_index": _coerce_int(item.get("message_index"), fallback=None),
                "speaker": _coerce_text(item.get("speaker"), fallback="") or None,
                "speaker_role": item.get("speaker_role"),
                "timestamp": _coerce_text(item.get("timestamp"), fallback="") or None,
                "quote": quote,
                "note": _coerce_text(item.get("note"), fallback="") or None,
            }
        )
    return evidences


def _coerce_findings(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    findings: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        summary = _coerce_text(
            item.get("summary", item.get("reason")), fallback="未提供摘要。")
        title = _coerce_text(item.get("title", item.get(
            "label")), fallback=summary[:30] or "未命名条目")
        findings.append(
            {
                "title": title,
                "summary": summary,
                "reason": _coerce_text(item.get("reason"), fallback=summary),
                "confidence": _coerce_confidence(item.get("confidence")),
                "severity": item.get("severity"),
                "resolution_status": item.get("resolution_status"),
                "evidences": _coerce_evidences(item.get("evidences", item.get("evidence"))),
            }
        )
    return findings


def _coerce_risk_assessment(value: Any) -> dict[str, Any]:
    source = value if isinstance(value, dict) else {}
    level = _coerce_text(source.get(
        "level", source.get("risk_level")), fallback="unknown")
    score = max(0, min(_coerce_int(source.get("score"), fallback=0), 100))
    summary = _coerce_text(source.get(
        "summary", source.get("reason")), fallback="未提供风险摘要。")
    return {
        "level": level,
        "score": score,
        "summary": summary,
        "reason": _coerce_text(source.get("reason"), fallback=summary),
        "evidences": _coerce_evidences(source.get("evidences", source.get("evidence"))),
    }


def _coerce_smart_replies(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    replies: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        content = _coerce_text(
            item.get("content", item.get("reply_text")), fallback="")
        if not content:
            continue
        replies.append(
            {
                "style": _coerce_text(item.get("style"), fallback="通用"),
                "content": content,
                "reason": _coerce_text(item.get("reason"), fallback="基于当前会话建议继续澄清需求。"),
                "evidences": _coerce_evidences(item.get("evidences", item.get("evidence"))),
            }
        )
    return replies
