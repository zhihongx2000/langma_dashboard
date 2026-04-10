from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime
from io import StringIO
import re

from backend.domain.enums import SpeakerRole


TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}(?::\d{2})?$")
TEACHER_HINTS = (
    "同学",
    "您好",
    "你好呀",
    "你可以",
    "申请毕业",
    "服务费",
    "学位证",
    "可以参加",
    "规划很清晰",
    "全国的时间",
)
STUDENT_HINTS = (
    "老师",
    "我现在",
    "我想",
    "为什么",
    "我明白",
    "请教",
    "我查询",
    "我打算",
    "注意事项",
    "[捂脸]",
)


@dataclass(slots=True)
class ParsedMessage:
    message_index: int
    speaker_role: SpeakerRole
    speaker_name: str | None
    timestamp_text: str | None
    timestamp_at: datetime | None
    content: str
    raw_content: str
    parse_note: str | None = None


@dataclass(slots=True)
class ParseResult:
    messages: list[ParsedMessage]
    parser_notes: list[str] = field(default_factory=list)
    role_summary: dict[SpeakerRole, int] = field(default_factory=dict)


@dataclass(slots=True)
class _MessageCandidate:
    speaker_name: str | None
    timestamp_text: str | None
    content: str
    raw_content: str
    parse_note: str | None = None


def _is_timestamp(value: str) -> bool:
    return bool(TIMESTAMP_PATTERN.match(value))


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    for pattern in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value, pattern)
        except ValueError:
            continue
    return None


def _normalize_wechat_timestamp(date_text: str, time_text: str) -> str | None:
    date_value = date_text.strip()
    time_value = time_text.strip()
    if not date_value and not time_value:
        return None
    if date_value and time_value:
        return f"{date_value} {time_value}"
    return date_value or time_value


def _looks_like_wechat_csv(raw_text: str) -> bool:
    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        header = [token.strip().lstrip("\ufeff")
                  for token in stripped.split(",")]
        required_fields = {"日期", "时间", "消息内容", "发送人"}
        return required_fields.issubset(set(header))
    return False


def _parse_wechat_csv(raw_text: str) -> ParseResult:
    parser_notes: list[str] = []
    normalized_messages: list[ParsedMessage] = []
    role_summary = {
        SpeakerRole.TEACHER: 0,
        SpeakerRole.STUDENT: 0,
        SpeakerRole.UNKNOWN: 0,
    }

    reader = csv.DictReader(StringIO(raw_text))
    for row_index, row in enumerate(reader, start=1):
        normalized_row = {
            (key or "").strip().lstrip("\ufeff"): (value or "")
            for key, value in row.items()
        }
        message_type = str(normalized_row.get("消息类型", "")).strip()
        if message_type != "文本":
            parser_notes.append(
                f"第 {row_index} 行消息类型为[{message_type or '空'}]，仅保留文本消息，已跳过。"
            )
            continue

        content = str(normalized_row.get("消息内容", "")).strip()
        if not content:
            parser_notes.append(f"第 {row_index} 行消息内容为空，已跳过。")
            continue

        sender = str(normalized_row.get("发送人", "")).strip() or None
        timestamp_text = _normalize_wechat_timestamp(
            str(normalized_row.get("日期", "")),
            str(normalized_row.get("时间", "")),
        )
        staff_flag = str(normalized_row.get("是否员工", "")).strip()
        if staff_flag == "是":
            speaker_role = SpeakerRole.TEACHER
        elif staff_flag == "否":
            speaker_role = SpeakerRole.STUDENT
        else:
            speaker_role = SpeakerRole.UNKNOWN

        role_summary[speaker_role] += 1
        normalized_messages.append(
            ParsedMessage(
                message_index=len(normalized_messages) + 1,
                speaker_role=speaker_role,
                speaker_name=sender,
                timestamp_text=timestamp_text,
                timestamp_at=_parse_timestamp(timestamp_text),
                content=content,
                raw_content=content,
                parse_note=None,
            )
        )

    if not normalized_messages:
        parser_notes.append("CSV 内容未识别到可用消息。")

    return ParseResult(
        messages=normalized_messages,
        parser_notes=parser_notes,
        role_summary=role_summary,
    )


def _score_speaker(content: str) -> tuple[int, int]:
    teacher_score = sum(1 for hint in TEACHER_HINTS if hint in content)
    student_score = sum(1 for hint in STUDENT_HINTS if hint in content)
    if content.endswith("？") and "老师" in content:
        student_score += 1
    return teacher_score, student_score


def _infer_roles(candidates: list[_MessageCandidate]) -> tuple[dict[str, SpeakerRole], SpeakerRole]:
    role_scores: dict[str, dict[str, int]] = {}
    named_candidates = [
        candidate for candidate in candidates if candidate.speaker_name]

    for candidate in named_candidates:
        assert candidate.speaker_name is not None
        scores = role_scores.setdefault(candidate.speaker_name, {
                                        "teacher": 0, "student": 0})
        teacher_score, student_score = _score_speaker(candidate.content)
        scores["teacher"] += teacher_score
        scores["student"] += student_score

    role_map: dict[str, SpeakerRole] = {}
    if len(role_scores) >= 2:
        teacher_name = max(role_scores.items(), key=lambda item: (
            item[1]["teacher"] - item[1]["student"], item[1]["teacher"]))[0]
        student_name = max(role_scores.items(), key=lambda item: (
            item[1]["student"] - item[1]["teacher"], item[1]["student"]))[0]
        if teacher_name != student_name:
            role_map[teacher_name] = SpeakerRole.TEACHER
            role_map[student_name] = SpeakerRole.STUDENT

    for speaker_name, scores in role_scores.items():
        if speaker_name in role_map:
            continue
        if scores["teacher"] > scores["student"]:
            role_map[speaker_name] = SpeakerRole.TEACHER
        elif scores["student"] > scores["teacher"]:
            role_map[speaker_name] = SpeakerRole.STUDENT
        else:
            role_map[speaker_name] = SpeakerRole.UNKNOWN

    preamble_role = SpeakerRole.TEACHER if SpeakerRole.TEACHER in role_map.values(
    ) else SpeakerRole.UNKNOWN
    return role_map, preamble_role


def parse_chat_text(raw_text: str) -> ParseResult:
    if _looks_like_wechat_csv(raw_text):
        return _parse_wechat_csv(raw_text)

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    parser_notes: list[str] = []
    candidates: list[_MessageCandidate] = []
    preamble_lines: list[str] = []
    index = 0

    while index < len(lines):
        is_speaker_line = index + \
            1 < len(lines) and _is_timestamp(lines[index + 1])
        if not is_speaker_line:
            preamble_lines.append(lines[index])
            index += 1
            continue

        speaker_name = lines[index]
        timestamp_text = lines[index + 1]
        content_lines: list[str] = []
        cursor = index + 2
        while cursor < len(lines):
            next_is_speaker = cursor + \
                1 < len(lines) and _is_timestamp(lines[cursor + 1])
            if next_is_speaker:
                break
            content_lines.append(lines[cursor])
            cursor += 1

        content = "\n".join(content_lines).strip()
        if content:
            candidates.append(
                _MessageCandidate(
                    speaker_name=speaker_name,
                    timestamp_text=timestamp_text,
                    content=content,
                    raw_content=content,
                )
            )
        else:
            parser_notes.append(
                f"检测到空消息或附件占位，已跳过：{speaker_name} {timestamp_text}")
        index = cursor

    if preamble_lines:
        preamble_content = "\n".join(preamble_lines).strip()
        candidates.insert(
            0,
            _MessageCandidate(
                speaker_name=None,
                timestamp_text=None,
                content=preamble_content,
                raw_content=preamble_content,
                parse_note="未检测到昵称与时间戳的前置文本已保留。",
            ),
        )
        parser_notes.append("存在未带昵称与时间戳的前置文本，已按单条消息保留。")

    role_map, preamble_role = _infer_roles(candidates)
    normalized_messages: list[ParsedMessage] = []
    role_summary = {
        SpeakerRole.TEACHER: 0,
        SpeakerRole.STUDENT: 0,
        SpeakerRole.UNKNOWN: 0,
    }

    for message_index, candidate in enumerate(candidates, start=1):
        if candidate.speaker_name is None:
            speaker_role = preamble_role
        else:
            speaker_role = role_map.get(
                candidate.speaker_name, SpeakerRole.UNKNOWN)
        role_summary[speaker_role] += 1
        normalized_messages.append(
            ParsedMessage(
                message_index=message_index,
                speaker_role=speaker_role,
                speaker_name=candidate.speaker_name,
                timestamp_text=candidate.timestamp_text,
                timestamp_at=_parse_timestamp(candidate.timestamp_text),
                content=candidate.content,
                raw_content=candidate.raw_content,
                parse_note=candidate.parse_note,
            )
        )

    return ParseResult(messages=normalized_messages, parser_notes=parser_notes, role_summary=role_summary)
