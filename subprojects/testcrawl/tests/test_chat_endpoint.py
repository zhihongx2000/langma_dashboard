from fastapi.testclient import TestClient

from app.main import app


def test_chat_endpoint_ok(monkeypatch):
    def fake_chat(messages, *, max_rounds=20):
        assert messages[-1]["role"] == "user"
        return {"ok": True, "error": None, "reply": "你好"}

    monkeypatch.setattr("app.routers.test_local.chat_completion", fake_chat)
    with TestClient(app) as client:
        r = client.post(
            "/api/test/chat",
            json={"messages": [{"role": "user", "content": "hi"}]},
        )
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert r.json()["reply"] == "你好"


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

    monkeypatch.setattr("app.routers.test_local.chat_completion", fake_chat)
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
        assert "官方" in content or "通知" in content
        return {"ok": True, "error": None, "reply": "- **截止**：示例\n- 注意：以官网为准"}

    monkeypatch.setattr("app.routers.test_local.summarize_policy_document", fake_summarize)
    with TestClient(app) as client:
        r = client.post(
            "/api/test/summarize-policy",
            json={"content": "某省考试院通知：自学考试报名时间延长至月底。", "title": "测试标题"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "截止" in body["reply"]
