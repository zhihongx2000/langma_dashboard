from backend.config.settings import clear_settings_cache, get_settings
from backend.db.models import PromptVersion
from backend.db.session import clear_db_caches, get_session_factory
from backend.services.bootstrap_service import initialize_database
from backend.services.prompt_service import ensure_default_prompt_versions


def test_default_prompt_is_synced_from_file_for_untouched_v1(tmp_path, monkeypatch) -> None:
    test_database_path = tmp_path / "prompt-sync.db"
    monkeypatch.setenv("LANG_MA_DATABASE_URL", f"sqlite:///{test_database_path}")
    clear_settings_cache()
    clear_db_caches()
    initialize_database()

    session_factory = get_session_factory()
    settings = get_settings()
    expected_content = settings.resolve_path(
        "prompts/user_profiling_analysis/user_profile_and_reply/v1.md"
    ).read_text(encoding="utf-8")

    with session_factory() as db:
        prompt_version = PromptVersion(
            tool_key="user_profiling_analysis",
            task_key="user_profile_and_reply",
            version_label="v1",
            version_note="初始结构化 Prompt",
            content="# 旧的默认 Prompt\n\n这是一份应该被同步替换的内容。",
            is_active=True,
        )
        db.add(prompt_version)
        db.commit()
        db.refresh(prompt_version)

        ensure_default_prompt_versions(db)

        refreshed = db.get(PromptVersion, prompt_version.id)
        assert refreshed is not None
        assert refreshed.content == expected_content

    clear_settings_cache()
    clear_db_caches()


def test_default_prompt_sync_does_not_overwrite_user_managed_version(tmp_path, monkeypatch) -> None:
    test_database_path = tmp_path / "prompt-sync-protected.db"
    monkeypatch.setenv("LANG_MA_DATABASE_URL", f"sqlite:///{test_database_path}")
    clear_settings_cache()
    clear_db_caches()
    initialize_database()

    session_factory = get_session_factory()

    with session_factory() as db:
        custom_content = "# 老师自定义 Prompt\n\n请沿用老师已经手工调整过的版本。"
        prompt_version = PromptVersion(
            tool_key="user_profiling_analysis",
            task_key="user_profile_and_reply",
            version_label="v1",
            version_note="老师已手工调整",
            content=custom_content,
            is_active=True,
        )
        db.add(prompt_version)
        db.commit()
        db.refresh(prompt_version)

        ensure_default_prompt_versions(db)

        refreshed = db.get(PromptVersion, prompt_version.id)
        assert refreshed is not None
        assert refreshed.content == custom_content

    clear_settings_cache()
    clear_db_caches()