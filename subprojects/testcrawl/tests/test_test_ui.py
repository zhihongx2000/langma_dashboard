from fastapi.testclient import TestClient

from app.main import app


def test_test_ui_page():
    with TestClient(app) as client:
        response = client.get("/test-ui")
    assert response.status_code == 200
    assert "text/html" in (response.headers.get("content-type") or "")
    assert "成绩查询" in response.text
    assert "刷新当前省份" in response.text
    assert "查看原网址" in response.text
    assert "level1SourceLink" in response.text
