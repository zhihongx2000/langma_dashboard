from fastapi.testclient import TestClient

from app.main import app


def test_sichuan_levels_endpoint(monkeypatch):
    def fake_levels():
        return {
            "source_url": "https://www.sceea.cn/Html/ZXKS.html",
            "level1": [
                {
                    "name": "综合信息",
                    "items": [
                        {
                            "title": "示例标题",
                            "url": "https://www.sceea.cn/a.html",
                            "publish_date": "2026-04-01",
                        }
                    ],
                }
            ],
        }

    monkeypatch.setattr("app.routers.test_local.get_sichuan_levels", fake_levels)

    with TestClient(app) as client:
        response = client.get("/api/test/sichuan/levels")

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload.get("level1"), list)
    assert payload["level1"][0]["items"][0]["publish_date"] == "2026-04-01"


def test_sichuan_content_endpoint(monkeypatch):
    def fake_content(url: str):
        return {
            "ok": True,
            "url": url,
            "title": "文章标题",
            "content_text": "正文内容",
            "content_preview": "正文内容",
        }

    monkeypatch.setattr("app.routers.test_local.get_level3_content", fake_content)

    with TestClient(app) as client:
        response = client.get("/api/test/sichuan/content", params={"url": "https://www.sceea.cn/a.html"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["title"] == "文章标题"


def test_score_query_endpoint(monkeypatch):
    monkeypatch.setattr(
        "app.routers.test_local.get_score_query_url",
        lambda province_name, portal_url=None: "https://cx.sceea.cn/html/SZCJ.htm",
    )

    with TestClient(app) as client:
        response = client.get("/api/test/score-query", params={"province_id": 1})

    assert response.status_code == 200
    payload = response.json()
    assert payload["province_id"] == 1
    assert payload["province_name"] == "四川"
    assert payload["score_query_url"] == "https://cx.sceea.cn/html/SZCJ.htm"


def test_sichuan_assistant_endpoint(monkeypatch):
    def fake_answer(db, question: str, province_id: int = 1):
        assert province_id == 1
        return {
            "ok": True,
            "mode": "deepseek_answer",
            "answer": f"回答: {question}",
            "related_items": [
                {
                    "id": 1,
                    "title": "相关条目",
                    "url": "https://www.sceea.cn/b.html",
                    "publish_date": "2026-03-01",
                }
            ],
        }

    monkeypatch.setattr("app.routers.test_local.answer_from_crawled_content", fake_answer)

    with TestClient(app) as client:
        response = client.post("/api/test/sichuan/assistant", json={"question": "请总结自考政策"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["answer"].startswith("回答:")
    assert payload["related_items"][0]["url"] == "https://www.sceea.cn/b.html"
