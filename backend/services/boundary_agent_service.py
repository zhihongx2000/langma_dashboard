from __future__ import annotations

from typing import Any

from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

from backend.config.settings import ModelOptionConfig, Settings
from backend.services.reference_kb_service import format_reference_hits, search_reference_chunks


def maybe_run_boundary_agent(
    *,
    settings: Settings,
    model_config: ModelOptionConfig,
    module_key: str,
    user_query: str,
) -> str | None:
    """Use a lightweight agent to fetch boundary clauses for ambiguous decisions."""
    if not settings.openai_api_key:
        return None
    if model_config.provider_key != "openai_compatible":
        return None

    @tool
    def search_reference_docs(question: str) -> str:
        """Search internal reference docs and return top matched sections."""
        chunks = search_reference_chunks(question, top_k=3)
        if not chunks:
            return "未找到命中文段。"

        lines = []
        for chunk in chunks:
            lines.append(
                f"[{chunk.chunk_id}] {chunk.source_path} / {chunk.section_title}\n{chunk.content[:500]}"
            )
        return "\n\n".join(lines)

    try:
        chat_kwargs: dict[str, Any] = {
            "model_name": model_config.api_model_name or model_config.model_key,
            "openai_api_key": settings.openai_api_key,
            "openai_api_base": settings.openai_base_url,
            "temperature": 0,
            "max_tokens": 800,
            "request_timeout": 60,
            "max_retries": 0,
        }
        chat_model = ChatOpenAI(**chat_kwargs)
        agent = create_agent(
            model=chat_model,
            tools=[search_reference_docs],
            system_prompt=(
                "你是教育咨询分析边界裁决助手。"
                "当判定边界模糊时，必须先调用 search_reference_docs 获取依据，"
                "然后用两句话给出：1)边界说明 2)引用的文档片段ID。"
            ),
        )
        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            f"模块: {module_key}\n"
                            f"当前争议: {user_query}\n"
                            "请先检索 references，再给出边界说明和依据片段。"
                        ),
                    }
                ]
            }
        )
        messages = result.get("messages") if isinstance(result, dict) else None
        if not messages:
            return None
        final_message = messages[-1]
        content = getattr(final_message, "content", None)
        if isinstance(content, str) and content.strip():
            return content.strip()
    except Exception:
        return None

    fallback_hits = format_reference_hits(
        search_reference_chunks(user_query, top_k=2))
    if fallback_hits:
        return f"检索到参考依据：{'; '.join(fallback_hits)}"
    return None
