from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import re

from backend.config.settings import get_settings


@dataclass(frozen=True, slots=True)
class ReferenceChunk:
    source_path: str
    section_title: str
    chunk_id: str
    content: str


HEADER_PATTERN = re.compile(r"^#{1,6}\s+", re.MULTILINE)
TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fffA-Za-z0-9]+")


@lru_cache(maxsize=1)
def load_reference_chunks() -> tuple[ReferenceChunk, ...]:
    settings = get_settings()
    reference_dir = settings.resolve_path("prompts/references")
    if not reference_dir.exists():
        return tuple()

    chunks: list[ReferenceChunk] = []
    for path in sorted(reference_dir.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        chunks.extend(_split_markdown(path.name, content))
    return tuple(chunks)


def search_reference_chunks(query: str, top_k: int = 3) -> list[ReferenceChunk]:
    if not query.strip():
        return []

    chunks = load_reference_chunks()
    if not chunks:
        return []

    query_tokens = set(_tokenize(query))
    scored: list[tuple[int, ReferenceChunk]] = []
    for chunk in chunks:
        chunk_tokens = set(_tokenize(chunk.content))
        if not chunk_tokens:
            continue
        overlap = len(query_tokens & chunk_tokens)
        if overlap <= 0:
            continue
        scored.append((overlap, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [item[1] for item in scored[:top_k]]


def format_reference_hits(chunks: list[ReferenceChunk]) -> list[str]:
    return [
        f"{chunk.chunk_id}|{chunk.source_path}|{chunk.section_title}"
        for chunk in chunks
    ]


def _split_markdown(file_name: str, content: str) -> list[ReferenceChunk]:
    sections = HEADER_PATTERN.split(content)
    headers = HEADER_PATTERN.findall(content)

    if not sections:
        return []

    chunks: list[ReferenceChunk] = []
    if sections[0].strip():
        chunks.append(
            ReferenceChunk(
                source_path=f"prompts/references/{file_name}",
                section_title="intro",
                chunk_id=f"{file_name}#intro",
                content=sections[0].strip(),
            )
        )

    for index, body in enumerate(sections[1:], start=1):
        if not body.strip():
            continue
        header = headers[index - 1].strip().replace("#",
                                                    "").strip() if index - 1 < len(headers) else "section"
        chunks.append(
            ReferenceChunk(
                source_path=f"prompts/references/{file_name}",
                section_title=header or "section",
                chunk_id=f"{file_name}#sec-{index}",
                content=body.strip(),
            )
        )
    return chunks


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_PATTERN.findall(text)]
