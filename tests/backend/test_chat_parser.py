import csv
from io import StringIO
from pathlib import Path

from backend.domain.enums import SpeakerRole
from backend.parsers.chat_parser import parse_chat_text


def test_parse_chat_text_extracts_messages_and_roles() -> None:
    raw_text = Path(
        "/home/hong/lang_ma_dashboard/tests/e2e/user_profile_example.md").read_text(encoding="utf-8")

    parse_result = parse_chat_text(raw_text)

    assert len(parse_result.messages) >= 8
    assert parse_result.role_summary[SpeakerRole.TEACHER] > 0
    assert parse_result.role_summary[SpeakerRole.STUDENT] > 0
    assert any(message.content for message in parse_result.messages)


def test_parse_chat_text_supports_wechat_csv_format() -> None:
    raw_text = Path(
        "/home/hong/lang_ma_dashboard/prompts/references/example_wechat.csv"
    ).read_text(encoding="utf-8")
    csv_reader = csv.DictReader(StringIO(raw_text))
    expected_text_messages = sum(
        1
        for row in csv_reader
        if str((row or {}).get("消息类型", "")).strip() == "文本"
        and str((row or {}).get("消息内容", "")).strip()
    )

    parse_result = parse_chat_text(raw_text)

    assert len(parse_result.messages) == expected_text_messages
    assert parse_result.role_summary[SpeakerRole.TEACHER] > 0
    assert parse_result.role_summary[SpeakerRole.STUDENT] > 0
    assert parse_result.messages[0].speaker_name == "桃子🍑｜谢东梅"
    assert parse_result.messages[0].timestamp_text == "2026-04-02 10:13:09"
    assert all(message.content != "[图片]" for message in parse_result.messages)
    assert all(message.content !=
               "撤回了一条消息" for message in parse_result.messages)
