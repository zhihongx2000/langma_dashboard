from fastapi.testclient import TestClient

from app.main import app


def test_formal_ui_page():
    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in (response.headers.get("content-type") or "")
    assert "level1SourceLink" in response.text
    assert "正式版" in response.text
    assert "智能问答助手" in response.text
    assert "资讯列表" in response.text


def test_legacy_test_ui_alias_redirects_to_formal_page():
    with TestClient(app) as client:
        response = client.get("/test-ui", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/"
