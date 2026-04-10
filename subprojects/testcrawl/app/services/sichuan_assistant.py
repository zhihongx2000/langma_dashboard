from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.content import Content
from app.models.section import Section

settings = get_settings()


SYSTEM_PROMPT = (
    "你是考试院信息助手，专注提供考试院与自考相关信息。"
    "你只能依据提供的爬取内容回答，不要编造。"
    "优先给出简洁总结；如果用户是查找类问题，给出最相关条目和结论。"
    "必要时在结尾使用 [ID] 标注依据来源。"
)


def answer_from_crawled_content(db: Session, question: str, province_id: int = 1) -> dict:
    query = (question or "").strip()
    if not query:
        return {
            "ok": False,
            "mode": "invalid_input",
            "answer": "请输入问题后再搜索。",
            "related_items": [],
        }

    rows = db.scalars(
        select(Content)
        .join(Section, Section.id == Content.section_id)
        .where(Section.province_id == province_id, Content.is_deleted.is_(False))
        .order_by(Content.crawled_at.desc())
        .limit(200)
    ).all()

    if not rows:
        return {
            "ok": False,
            "mode": "empty",
            "answer": "当前还没有可用的爬取内容，请先刷新抓取后再提问。",
            "related_items": [],
        }

    related = _pick_related(rows, query, limit=10)
    context_items = related if related else rows[:10]

    if not settings.deepseek_api_key:
        return {
            "ok": True,
            "mode": "rule_fallback",
            "answer": "已按关键词匹配到相关内容。你可以查看下方条目并点击标题链接查看原文。",
            "related_items": [_to_item(x) for x in context_items],
        }

    context_blocks = []
    for item in context_items:
        snippet = (item.content_text or "")[:300].replace("\n", " ").strip()
        context_blocks.append(
            f"[ID:{item.id}] 标题: {item.title}\n链接: {item.url}\n发布日期: {item.publish_date or '未知'}\n摘要: {snippet}"
        )

    try:
        client = OpenAI(
            api_key=settings.deepseek_api_key,
            base_url=(settings.deepseek_api_base_url or "https://api.deepseek.com/v1").rstrip("/"),
        )
        resp = client.chat.completions.create(
            model=settings.ai_search_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"用户问题：{query}\n\n"
                        "可用爬取内容：\n"
                        + "\n\n".join(context_blocks)
                        + "\n\n请先给结论，再给要点，最后列出引用ID。"
                    ),
                },
            ],
            temperature=0.2,
        )
        answer = ((resp.choices[0].message.content if resp.choices else "") or "").strip()
        if not answer:
            answer = "模型未返回有效回答，你可以换个问法再试一次。"
        return {
            "ok": True,
            "mode": "deepseek_answer",
            "answer": answer,
            "related_items": [_to_item(x) for x in context_items],
        }
    except Exception as exc:
        return {
            "ok": True,
            "mode": "rule_fallback",
            "answer": f"模型暂时不可用，已返回匹配内容列表（{type(exc).__name__}）。",
            "related_items": [_to_item(x) for x in context_items],
        }


def _pick_related(rows: list[Content], question: str, limit: int) -> list[Content]:
    keywords = [x.strip() for x in question.replace("，", " ").replace(",", " ").split(" ") if x.strip()]
    scored = []
    for row in rows:
        title = row.title or ""
        body = row.content_text or ""
        score = 0
        for kw in keywords:
            if kw in title:
                score += 5
            if kw in body:
                score += 1
        if question in title:
            score += 8
        if question in body:
            score += 2
        scored.append((score, row))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for s, r in scored if s > 0][:limit]


def _to_item(row: Content) -> dict:
    return {
        "id": row.id,
        "title": row.title,
        "url": row.url,
        "publish_date": row.publish_date.isoformat() if row.publish_date else None,
        "crawled_at": row.crawled_at.isoformat() if row.crawled_at else None,
    }
