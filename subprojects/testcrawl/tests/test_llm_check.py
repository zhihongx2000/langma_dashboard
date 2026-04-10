from app.services import browser_use_adapter


def test_check_llm_connectivity_returns_error_when_key_missing(monkeypatch):
    monkeypatch.setattr(browser_use_adapter.settings, "openai_api_key", None)
    result = browser_use_adapter.check_llm_connectivity()
    assert result["ok"] is False
    assert "OPENAI_API_KEY is empty" in result["error"]


def test_check_llm_connectivity_success(monkeypatch):
    monkeypatch.setattr(browser_use_adapter.settings, "openai_api_key", "dummy-key")

    async def fake_check(prompt):
        return {
            "ok": True,
            "model": "gpt-5-mini",
            "base_url": "https://example.com/v1",
            "latency_ms": 123,
            "response_preview": "OK",
        }

    monkeypatch.setattr(
        browser_use_adapter,
        "_check_llm_connectivity",
        fake_check,
    )
    result = browser_use_adapter.check_llm_connectivity(prompt="test")
    assert result["ok"] is True
    assert result["response_preview"] == "OK"
