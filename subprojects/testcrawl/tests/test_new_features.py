from fastapi.testclient import TestClient

from app.main import app


def test_crawl_report_latest_endpoint():
    with TestClient(app) as client:
        response = client.get("/api/crawl/report-latest")
    assert response.status_code == 200
    payload = response.json()
    assert "summary" in payload
    assert "items" in payload


def test_ai_search_endpoint(monkeypatch):
    import app.routers.contents as contents_router_module

    monkeypatch.setattr(
        contents_router_module,
        "search_contents_ai",
        lambda db, query, province_id, limit: {
            "query": query,
            "mode": "ai_rerank",
            "reason": "ok",
            "items": [{"id": 1, "title": "test", "url": "https://example.com", "publish_date": None, "crawled_at": None}],
        },
    )

    with TestClient(app) as client:
        response = client.get("/api/search/ai", params={"query": "test"})
    assert response.status_code == 200
    assert response.json()["mode"] == "ai_rerank"

