from backend.model_adapters.persona_analysis import _coerce_structured_payload
from backend.schemas.persona_analysis import StructuredAnalysisOutput


def test_coerce_structured_payload_repairs_common_schema_drift() -> None:
    raw_payload = {
        "session_id": "session-1",
        "conversation_summary": [],
        "pain_points": [
            {
                "reason": "学生对专业和毕业时间线存在明显焦虑。",
                "evidences": [{"message_index": 11, "content": "我是不想多读两年"}],
            }
        ],
        "high_frequency_points": [
            {
                "reason": "学生持续询问专业选择。",
                "evidences": [{"message_index": 14, "content": "有什么专业"}],
            }
        ],
        "risk_assessment": {
            "risk_level": "unknown",
            "reason": "本模块不输出风险评估",
        },
        "smart_replies": [
            {
                "reply_text": "先帮你把可选专业和毕业节奏拆开看。",
                "reason": "先稳住预期。",
            }
        ],
    }

    repaired = _coerce_structured_payload(raw_payload, fallback_session_id="fallback-session")
    output = StructuredAnalysisOutput.model_validate(repaired)

    assert output.session_id == "session-1"
    assert isinstance(output.conversation_summary, str)
    assert output.conversation_summary

    assert output.pain_points
    assert output.pain_points[0].title
    assert output.pain_points[0].summary
    assert output.pain_points[0].evidences
    assert output.pain_points[0].evidences[0].quote == "我是不想多读两年"

    assert output.high_frequency_points
    assert output.high_frequency_points[0].title
    assert output.high_frequency_points[0].summary

    assert output.risk_assessment.level.value == "unknown"
    assert output.risk_assessment.summary

    assert output.smart_replies
    assert output.smart_replies[0].content == "先帮你把可选专业和毕业节奏拆开看。"
