from fastapi.testclient import TestClient

from backend.config.settings import clear_settings_cache
from backend.db.session import clear_db_caches


def test_launch_education_exam_crawler_redirects(tmp_path, monkeypatch) -> None:
    test_database_path = tmp_path / "tools-launch-test.db"
    monkeypatch.setenv("LANG_MA_DATABASE_URL", f"sqlite:///{test_database_path}")
    monkeypatch.setenv("EDUCATION_EXAM_CRAWLER_BASE_URL", "http://127.0.0.1:8001")
    clear_settings_cache()
    clear_db_caches()

    from backend.main import create_app

    app = create_app()
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/tools/education-exam-crawler/launch",
            follow_redirects=False,
        )

    assert response.status_code == 307
    assert response.headers["location"] == "http://127.0.0.1:8001/"

    clear_settings_cache()
    clear_db_caches()


def test_launch_education_exam_crawler_requires_config(tmp_path, monkeypatch) -> None:
    test_database_path = tmp_path / "tools-launch-missing-config.db"
    monkeypatch.setenv("LANG_MA_DATABASE_URL", f"sqlite:///{test_database_path}")
    monkeypatch.delenv("LANG_MA_EDUCATION_EXAM_CRAWLER_BASE_URL", raising=False)
    monkeypatch.delenv("EDUCATION_EXAM_CRAWLER_BASE_URL", raising=False)
    monkeypatch.setenv("LANG_MA_EDUCATION_EXAM_CRAWLER_BASE_URL", "")
    clear_settings_cache()
    clear_db_caches()

    from backend.main import create_app

    app = create_app()
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/tools/education-exam-crawler/launch",
            follow_redirects=False,
        )

    assert response.status_code == 503
    payload = response.json()["detail"]
    assert payload["code"] == "TOOL_NOT_CONFIGURED"
    assert "未配置" in payload["detail"]
    assert "EDUCATION_EXAM_CRAWLER_BASE_URL" in payload["action"]

    clear_settings_cache()
    clear_db_caches()


def test_education_exam_crawler_status_without_config(tmp_path, monkeypatch) -> None:
    test_database_path = tmp_path / "tools-status-missing-config.db"
    monkeypatch.setenv("LANG_MA_DATABASE_URL", f"sqlite:///{test_database_path}")
    monkeypatch.delenv("LANG_MA_EDUCATION_EXAM_CRAWLER_BASE_URL", raising=False)
    monkeypatch.delenv("EDUCATION_EXAM_CRAWLER_BASE_URL", raising=False)
    monkeypatch.setenv("LANG_MA_EDUCATION_EXAM_CRAWLER_BASE_URL", "")
    clear_settings_cache()
    clear_db_caches()

    from backend.main import create_app

    app = create_app()
    with TestClient(app) as client:
        response = client.get("/api/v1/tools/education-exam-crawler/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["configured"] is False
    assert payload["reachable"] is False
    assert payload["launch_url"] == ""
    assert "未配置" in payload["message"]

    clear_settings_cache()
    clear_db_caches()


def test_education_exam_crawler_status_configured_but_unreachable(tmp_path, monkeypatch) -> None:
    test_database_path = tmp_path / "tools-status-unreachable.db"
    monkeypatch.setenv("LANG_MA_DATABASE_URL", f"sqlite:///{test_database_path}")
    monkeypatch.setenv("EDUCATION_EXAM_CRAWLER_BASE_URL", "http://127.0.0.1:8001")
    clear_settings_cache()
    clear_db_caches()

    from backend.main import create_app
    from backend.api.routes import tools

    monkeypatch.setattr(tools, "_is_crawler_reachable", lambda _: False)
    app = create_app()
    with TestClient(app) as client:
        response = client.get("/api/v1/tools/education-exam-crawler/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["configured"] is True
    assert payload["reachable"] is False
    assert payload["launch_url"] == "http://127.0.0.1:8001/"
    assert "未启动" in payload["message"]

    clear_settings_cache()
    clear_db_caches()
