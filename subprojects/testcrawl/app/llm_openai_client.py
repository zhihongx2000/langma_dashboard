"""OpenAI 兼容客户端（优先 DeepSeek，与 chat_assistant 逻辑一致）。"""

from __future__ import annotations

from openai import OpenAI

from app.config import get_settings

HARDCODED_DEEPSEEK_API_KEY = "sk-4125d7e673a144fe89f053b5117636e8"
HARDCODED_DEEPSEEK_API_BASE_URL = "https://api.deepseek.com/v1"


def get_openai_compatible_client() -> OpenAI | None:
    s = get_settings()
    if HARDCODED_DEEPSEEK_API_KEY.strip():
        return OpenAI(
            api_key=HARDCODED_DEEPSEEK_API_KEY.strip(),
            base_url=HARDCODED_DEEPSEEK_API_BASE_URL.rstrip("/"),
        )
    ds = (s.deepseek_api_key or "").strip()
    if ds:
        base = (s.deepseek_api_base_url or "https://api.deepseek.com/v1").rstrip("/")
        return OpenAI(api_key=ds, base_url=base)
    oa = (s.openai_api_key or "").strip()
    if oa:
        base = (s.openai_base_url or "https://api.openai.com/v1").rstrip("/")
        return OpenAI(api_key=oa, base_url=base)
    return None
