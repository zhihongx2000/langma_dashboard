from fastapi.testclient import TestClient

from app.main import app


def test_chat_endpoint_ok(monkeypatch):
    def fake_chat(messages, *, max_rounds=20):
        assert messages[-1]["role"] == "user"
        return {"ok": True, "error": None, "reply": "浣犲ソ"}

    monkeypatch.setattr("app.routers.crawler_ui.chat_completion", fake_chat)
    with TestClient(app) as client:
        r = client.post(
            "/api/test/chat",
            json={"messages": [{"role": "user", "content": "hi"}]},
        )
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert r.json()["reply"] == "浣犲ソ"


def test_chat_rejects_bad_role():
    with TestClient(app) as client:
        r = client.post(
            "/api/test/chat",
            json={"messages": [{"role": "system", "content": "x"}]},
        )
    assert r.status_code == 400


def test_chat_alias_path_ok(monkeypatch):
    def fake_chat(messages, *, max_rounds=20):
        return {"ok": True, "error": None, "reply": "pong"}

    monkeypatch.setattr("app.routers.crawler_ui.chat_completion", fake_chat)
    with TestClient(app) as client:
        r = client.post(
            "/api/test/ai/chat",
            json={"messages": [{"role": "user", "content": "ping"}]},
        )
    assert r.status_code == 200
    assert r.json()["reply"] == "pong"


def test_summarize_policy_endpoint_ok(monkeypatch):
    def fake_summarize(*, content, title=None, max_chars=28000):
        assert len(content) >= 10
        assert "notice" in content or "official" in content
        return {"ok": True, "error": None, "reply": "- deadline: example\n- note: use official source"}

    monkeypatch.setattr("app.routers.crawler_ui.summarize_policy_document", fake_summarize)
    with TestClient(app) as client:
        r = client.post(
            "/api/test/summarize-policy",
            json={"content": "official notice: registration deadline has been extended to month end.", "title": "test title"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "deadline" in body["reply"]

