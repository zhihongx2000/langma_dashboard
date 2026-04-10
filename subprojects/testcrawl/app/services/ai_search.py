import json
import re

from openai import OpenAI
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.content import Content
from app.models.section import Section

settings = get_settings()


def search_contents_ai(db: Session, query: str, province_id: int | None = None, limit: int | None = None) -> dict:
    max_limit = limit or settings.ai_search_limit
    base_rows = _candidate_rows(db, query=query, province_id=province_id, limit=settings.ai_search_candidates)
    keyword_items = [_to_item(row) for row in base_rows[:max_limit]]

    if not settings.deepseek_api_key:
        return {
            "query": query,
            "mode": "keyword_only",
            "reason": "DEEPSEEK_API_KEY is empty",
            "items": keyword_items,
        }

    try:
        ai_ids = _ask_llm_for_ids(query=query, candidates=base_rows, limit=max_limit)
        if not ai_ids:
            return {"query": query, "mode": "keyword_only", "reason": "llm returned empty", "items": keyword_items}
        by_id = {content.id: _to_item(content) for content in base_rows}
        ai_items = [by_id[cid] for cid in ai_ids if cid in by_id][:max_limit]
        if not ai_items:
            return {"query": query, "mode": "keyword_only", "reason": "llm ids not in candidates", "items": keyword_items}
        return {"query": query, "mode": "ai_rerank", "reason": "ok", "items": ai_items}
    except Exception as exc:
        return {"query": query, "mode": "keyword_only", "reason": f"llm_error: {type(exc).__name__}", "items": keyword_items}


def _candidate_rows(db: Session, query: str, province_id: int | None, limit: int) -> list[Content]:
    stmt = (
        select(Content)
        .where(
            Content.is_deleted.is_(False),
            or_(Content.title.contains(query), Content.content_text.contains(query)),
        )
        .order_by(Content.crawled_at.desc())
        .limit(limit)
    )
    if province_id is not None:
        stmt = (
            select(Content)
            .join(Section, Section.id == Content.section_id)
            .where(
                Section.province_id == province_id,
                Content.is_deleted.is_(False),
                or_(Content.title.contains(query), Content.content_text.contains(query)),
            )
            .order_by(Content.crawled_at.desc())
            .limit(limit)
        )
    return db.scalars(stmt).all()


def _ask_llm_for_ids(query: str, candidates: list[Content], limit: int) -> list[int]:
    if not candidates:
        return []
    base_url = settings.deepseek_api_base_url.rstrip("/")
    client = OpenAI(api_key=settings.deepseek_api_key, base_url=base_url)
    lines = []
    for row in candidates:
        snippet = (row.content_text or "")[:180].replace("\n", " ").strip()
        lines.append(f'id={row.id} | title={row.title} | snippet={snippet}')
    prompt = (
        "你是考试院信息助手，专注提供各省考试院自考信息检索。\n"
        "任务：根据用户查询词，从候选内容中选出最相关的内容ID。\n"
        "要求：\n"
        "1. 优先返回与自学考试、报名报考、考试安排、成绩查询、政策通知、毕业申请相关的信息。\n"
        "2. 如果候选中有明显无关内容，不要选。\n"
        f"3. 最多返回 {limit} 个ID。\n"
        "4. 仅返回JSON：{\"selected_ids\": [数字ID,...]}，不要解释。\n"
        f"\n用户查询：{query}\n\n候选列表：\n" + "\n".join(lines)
    )
    resp = client.chat.completions.create(
        model=settings.ai_search_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    text = ((resp.choices[0].message.content if resp.choices else "") or "").strip()
    if not text:
        return []
    parsed = _safe_json_parse(text)
    if not parsed:
        return []
    ids = parsed.get("selected_ids", [])
    return [int(i) for i in ids if isinstance(i, int) or (isinstance(i, str) and i.isdigit())]


def _to_item(content: Content) -> dict:
    return {
        "id": content.id,
        "title": content.title,
        "url": content.url,
        "publish_date": content.publish_date,
        "crawled_at": content.crawled_at,
    }


def _safe_json_parse(text: str) -> dict | None:
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except Exception:
        pass
    # tolerate fenced markdown or extra leading text
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else None
    except Exception:
        return None
