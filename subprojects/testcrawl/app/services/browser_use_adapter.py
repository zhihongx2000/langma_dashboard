import asyncio
import time

from pydantic import BaseModel, Field

from app.config import get_settings

settings = get_settings()


class SectionCandidate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    url: str = Field(min_length=1, max_length=1000)


class SectionDiscoveryOutput(BaseModel):
    sections: list[SectionCandidate] = Field(default_factory=list)


def browser_use_available() -> bool:
    return bool(settings.browser_use_enabled and settings.openai_api_key)


def discover_sections_with_browser_use(home_url: str) -> list[tuple[str, str]]:
    if not browser_use_available():
        return []

    try:
        return asyncio.run(_discover_sections_with_browser_use(home_url))
    except Exception:
        return []


def resolve_openai_base_url() -> str | None:
    if not settings.openai_base_url:
        return None
    base_url = settings.openai_base_url.rstrip("/")
    if not base_url.endswith("/v1"):
        base_url = f"{base_url}/v1"
    return base_url


def check_llm_connectivity(prompt: str = "Reply with OK only.") -> dict:
    if not settings.openai_api_key:
        return {
            "ok": False,
            "model": settings.browser_use_model,
            "base_url": resolve_openai_base_url(),
            "error": "OPENAI_API_KEY is empty",
        }
    try:
        return asyncio.run(_check_llm_connectivity(prompt))
    except Exception as exc:
        return {
            "ok": False,
            "model": settings.browser_use_model,
            "base_url": resolve_openai_base_url(),
            "error": f"{type(exc).__name__}: {str(exc)}",
        }


async def _check_llm_connectivity(prompt: str) -> dict:
    from browser_use import ChatOpenAI
    from browser_use.llm.messages import UserMessage

    start = time.perf_counter()
    llm = ChatOpenAI(
        model=settings.browser_use_model,
        api_key=settings.openai_api_key,
        base_url=resolve_openai_base_url(),
        temperature=0.0,
        reasoning_effort="minimal",
    )
    response = await llm.ainvoke([UserMessage(content=prompt)])
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    content = (getattr(response, "completion", None) or "").strip()
    return {
        "ok": bool(content),
        "model": settings.browser_use_model,
        "base_url": resolve_openai_base_url(),
        "latency_ms": elapsed_ms,
        "response_preview": content[:200],
    }


async def _discover_sections_with_browser_use(home_url: str) -> list[tuple[str, str]]:
    from browser_use import Agent, ChatOpenAI

    llm = ChatOpenAI(
        model=settings.browser_use_model,
        api_key=settings.openai_api_key,
        base_url=resolve_openai_base_url(),
        temperature=0.0,
        reasoning_effort="minimal",
    )
    task = (
        "Open the provided education exam website home page or list page, identify the most useful "
        "self-study exam related sections, and return only same-site section links. "
        "Prefer sections about notices, announcements, registration, exam schedule, score query, "
        "policy, self-study exam, and admissions. Ignore login pages, contact pages, privacy pages, "
        "home links, search links, and file downloads. "
        f"Return at most {settings.browser_use_result_limit} sections for this URL: {home_url}"
    )
    agent = Agent(
        task=task,
        llm=llm,
        output_model_schema=SectionDiscoveryOutput,
        use_vision=False,
        max_actions_per_step=3,
        directly_open_url=True,
        enable_planning=False,
    )
    history = await agent.run(max_steps=settings.browser_use_max_steps)
    output = history.structured_output or history.get_structured_output(SectionDiscoveryOutput)
    if output is None:
        return []

    dedup: dict[str, str] = {}
    for section in output.sections:
        if section.url.startswith("http") and section.url not in dedup:
            dedup[section.url] = section.name.strip() or "AI discovered section"
    return [(name, url) for url, name in dedup.items()]
