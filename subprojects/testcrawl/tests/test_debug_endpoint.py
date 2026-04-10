from fastapi.testclient import TestClient

from app.main import app


def test_debug_discover_sections_requires_api_key():
    with TestClient(app) as client:
        response = client.get("/api/debug/discover-sections", params={"url": "https://example.com"})

    assert response.status_code == 401


def test_debug_discover_sections_returns_report(monkeypatch):
    fake_report = {
        "home_url": "https://example.com",
        "fetch_source": "playwright",
        "used_ai": False,
        "static_results": [("通知公告", "https://example.com/news")],
        "ai_results": [],
        "merged_results": [("通知公告", "https://example.com/news")],
    }

    import app.routers.debug as debug_router_module

    monkeypatch.setattr(debug_router_module, "discover_sections_with_report", lambda **kwargs: fake_report)

    with TestClient(app) as client:
        response = client.get(
            "/api/debug/discover-sections",
            params={"url": "https://example.com"},
            headers={"X-API-Key": "change-this-api-key"},
        )

    assert response.status_code == 200
    assert response.json()["home_url"] == "https://example.com"


def test_debug_llm_check(monkeypatch):
    import app.routers.debug as debug_router_module

    monkeypatch.setattr(
        debug_router_module,
        "check_llm_connectivity",
        lambda prompt: {
            "ok": True,
            "model": "gpt-5-mini",
            "base_url": "https://example.com/v1",
            "latency_ms": 100,
            "response_preview": "OK",
        },
    )

    with TestClient(app) as client:
        response = client.get(
            "/api/debug/llm-check",
            params={"prompt": "Reply with OK"},
            headers={"X-API-Key": "change-this-api-key"},
        )

    assert response.status_code == 200
    assert response.json()["ok"] is True
