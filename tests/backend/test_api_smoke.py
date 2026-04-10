from fastapi.testclient import TestClient

from backend.config.settings import clear_settings_cache
from backend.db.session import clear_db_caches


def test_persona_analysis_api_smoke(tmp_path, monkeypatch) -> None:
    test_database_path = tmp_path / "persona-analysis-test.db"
    monkeypatch.setenv("LANG_MA_DATABASE_URL",
                       f"sqlite:///{test_database_path}")
    clear_settings_cache()
    clear_db_caches()

    from backend.main import create_app

    app = create_app()
    with TestClient(app) as client:
        model_response = client.get("/api/v1/persona-analysis/model-options")
        assert model_response.status_code == 200
        assert len(model_response.json()["data"]["items"]) >= 1

        prompt_response = client.get(
            "/api/v1/persona-analysis/prompt-versions")
        assert prompt_response.status_code == 200
        assert len(prompt_response.json()["data"]["items"]) >= 1

        session_response = client.post(
            "/api/v1/persona-analysis/sessions",
            json={"title": "测试会话"},
        )
        assert session_response.status_code == 200
        assert session_response.json()["data"]["item"]["title"] == "测试会话"

        folder_response = client.post(
            "/api/v1/persona-analysis/folders",
            json={"title": "测试文件夹"},
        )
        assert folder_response.status_code == 200
        folder_id = folder_response.json()["data"]["item"]["item_id"]

        nested_session_response = client.post(
            "/api/v1/persona-analysis/sessions",
            json={"title": "文件夹内会话", "folder_id": folder_id},
        )
        assert nested_session_response.status_code == 200
        nested_session_id = nested_session_response.json()["data"]["item"]["item_id"]

        delete_session_response = client.delete(
            f"/api/v1/persona-analysis/sessions/{nested_session_id}"
        )
        assert delete_session_response.status_code == 200
        assert delete_session_response.json()["data"]["item_id"] == nested_session_id

        nested_session_response = client.post(
            "/api/v1/persona-analysis/sessions",
            json={"title": "再次创建的会话", "folder_id": folder_id},
        )
        assert nested_session_response.status_code == 200

        delete_folder_response = client.delete(
            f"/api/v1/persona-analysis/folders/{folder_id}"
        )
        assert delete_folder_response.status_code == 200
        assert delete_folder_response.json()["data"]["item_id"] == folder_id

        sidebar_response = client.get("/api/v1/persona-analysis/sidebar")
        assert sidebar_response.status_code == 200
        sidebar_item_ids = {item["item_id"] for item in sidebar_response.json()["data"]["items"]}
        assert folder_id not in sidebar_item_ids

    clear_settings_cache()
    clear_db_caches()
