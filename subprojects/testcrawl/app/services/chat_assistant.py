"""普通 AI 对话（OpenAI 兼容接口），不依赖爬取内容。"""

from __future__ import annotations

from openai import OpenAI

from app.config import get_settings

settings = get_settings()

CHAT_SYSTEM_PROMPT = (
    "你是一个友好、简洁的中文助手，可以回答各类常识、学习、技术等问题。"
    "回答尽量条理清晰；若不确定请如实说明。"
)

POLICY_SUMMARY_SYSTEM_PROMPT = """你是成人自考专业政策整理助手，我会不定期发送考试院各类官方通知、公告、政策文件，内容不固定，可能涉及报考、考试、毕业、免考、停考、补报等任意信息。
请你：
自动识别内容核心，只提炼关键、有效、对学生有用的信息
语言简洁通俗，去掉官话套话，方便成人自考学生阅读
重要时间、截止日期、条件、入口、要求须醒目：用「」或【】括起关键短语，或单独成行写「注意：…」。禁止使用星号、双星号、井号、反引号等 Markdown/代码符号，不要用星号作列表符号或假装加粗；子项用（1）（2）或另起一行「· …」，便于复制到微信、备忘录阅读
分点清晰排版（优先 1. 2. 3. 或一、二、三、），手机阅读友好
不编造、不延伸、不误导，只基于原文总结
最后用一句话提醒学生注意事项
直接输出整理好的内容即可，无需多余说明。"""


def _build_client() -> OpenAI | None:
    # 优先 DeepSeek：本地常见同时存在失效的 OPENAI_* 与有效的 DEEPSEEK_*，避免误连官方 OpenAI 报 401。
    if settings.deepseek_api_key:
        base = (settings.deepseek_api_base_url or "https://api.deepseek.com/v1").rstrip("/")
        return OpenAI(api_key=settings.deepseek_api_key, base_url=base)
    if settings.openai_api_key:
        base = (settings.openai_base_url or "https://api.openai.com/v1").rstrip("/")
        return OpenAI(api_key=settings.openai_api_key, base_url=base)
    return None


def chat_completion(messages: list[dict[str, str]], *, max_rounds: int = 20) -> dict:
    """
    messages: OpenAI 格式 [{"role":"user"|"assistant","content":"..."}, ...]
    """
    if not messages:
        return {"ok": False, "error": "messages 不能为空", "reply": ""}

    client = _build_client()
    if client is None:
        return {
            "ok": False,
            "error": "未配置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY，无法调用模型。",
            "reply": "",
        }

    # 只保留最近若干轮，避免超长
    trimmed = messages[-max_rounds * 2 :] if len(messages) > max_rounds * 2 else messages
    api_messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}, *trimmed]

    try:
        resp = client.chat.completions.create(
            model=settings.ai_search_model,
            messages=api_messages,
            temperature=0.7,
        )
        reply = ((resp.choices[0].message.content if resp.choices else "") or "").strip()
        if not reply:
            return {"ok": False, "error": "模型返回为空", "reply": ""}
        return {"ok": True, "error": None, "reply": reply}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "reply": ""}


def summarize_policy_document(*, content: str, title: str | None = None, max_chars: int = 28000) -> dict:
    """根据第三板块正文做自考政策类整理摘要（专用系统提示词）。"""
    body = (content or "").strip()
    if len(body) < 30:
        return {"ok": False, "error": "正文过短或为空，请先在第三板块加载文章。", "reply": ""}

    if len(body) > max_chars:
        body = body[:max_chars] + "\n\n（正文过长已截断，仅基于以上部分整理。）"

    client = _build_client()
    if client is None:
        return {
            "ok": False,
            "error": "未配置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY，无法调用模型。",
            "reply": "",
        }

    title_line = f"文档标题（供参考）：{title.strip()}\n\n" if (title or "").strip() else ""
    user_block = f"{title_line}以下为需要整理的官方文本：\n\n{body}"

    try:
        resp = client.chat.completions.create(
            model=settings.ai_search_model,
            messages=[
                {"role": "system", "content": POLICY_SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": user_block},
            ],
            temperature=0.3,
        )
        reply = ((resp.choices[0].message.content if resp.choices else "") or "").strip()
        if not reply:
            return {"ok": False, "error": "模型返回为空", "reply": ""}
        return {"ok": True, "error": None, "reply": reply}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "reply": ""}
