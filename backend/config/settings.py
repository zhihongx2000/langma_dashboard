from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import AliasChoices, BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from backend.domain.enums import AnalysisModuleKey


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_SETTINGS_PATH = ROOT_DIR / "settings.yaml"


class AppConfig(BaseModel):
    name: str = "Lang Ma Dashboard API"
    api_prefix: str = "/api/v1"


class DatabaseConfig(BaseModel):
    sqlite_path: str = "data/lang_ma_dashboard.db"


class ModelOptionConfig(BaseModel):
    provider_key: str
    provider_label: str
    model_key: str
    api_model_name: str | None = None
    model_label: str
    is_default: bool = False
    is_enabled: bool = True
    temperature: float | None = None
    max_tokens: int | None = None


class PromptConfig(BaseModel):
    tool_key: str = "user_profiling_analysis"
    task_key: str = "user_profile_and_reply"
    default_version_label: str = "v1"
    default_prompt_path: str = "prompts/user_profiling_analysis/user_profile_and_reply/v1.md"


class ModulePromptConfig(PromptConfig):
    module_key: AnalysisModuleKey = AnalysisModuleKey.USER_PROFILE_AND_REPLY


class PersonaAnalysisConfig(BaseModel):
    model_options: list[ModelOptionConfig] = Field(default_factory=list)
    prompts: list[ModulePromptConfig] = Field(default_factory=list)

    def get_prompt_config(self, module_key: AnalysisModuleKey) -> PromptConfig:
        for item in self.prompts:
            if item.module_key == module_key:
                return item
        # Fallback to first module if available, else default config
        if self.prompts:
            return self.prompts[0]
        return PromptConfig()

    def get_prompt_configs(self) -> list[PromptConfig]:
        if not self.prompts:
            return [PromptConfig()]
        seen: set[tuple[str, str]] = set()
        unique_configs: list[PromptConfig] = []
        for item in self.prompts:
            key = (item.tool_key, item.task_key)
            if key in seen:
                continue
            seen.add(key)
            unique_configs.append(item)
        return unique_configs

    def get_system_template_path(self, module_key: AnalysisModuleKey) -> str:
        return f"prompts/user_profiling_analysis/system_templates/{module_key.value}.md"


class YamlSettings(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    persona_analysis: PersonaAnalysisConfig = Field(
        default_factory=PersonaAnalysisConfig)


class EnvironmentSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT_DIR / ".env"), extra="ignore")

    database_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LANG_MA_DATABASE_URL", "DATABASE_URL"),
    )
    openai_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "LANG_MA_OPENAI_API_KEY", "OPENAI_API_KEY", "DEEPSEEK_API_KEY"),
    )
    openai_base_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "LANG_MA_OPENAI_BASE_URL", "OPENAI_BASE_URL", "DEEPSEEK_API_BASE_URL"),
    )


class Settings(BaseModel):
    root_dir: Path
    app_name: str
    api_prefix: str
    database_url: str
    persona_analysis: PersonaAnalysisConfig
    openai_api_key: str | None = None
    openai_base_url: str | None = None

    def resolve_path(self, relative_path: str) -> Path:
        path = Path(relative_path)
        if path.is_absolute():
            return path
        return self.root_dir / path


def _load_yaml_settings(path: Path) -> YamlSettings:
    if not path.exists():
        return YamlSettings()

    raw_data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return YamlSettings.model_validate(raw_data)


def _resolve_database_url(root_dir: Path, database_url: str | None, sqlite_path: str) -> str:
    if database_url:
        if database_url.startswith("sqlite:///"):
            raw_path = Path(database_url.removeprefix("sqlite:///"))
            if not raw_path.is_absolute():
                return f"sqlite:///{(root_dir / raw_path).resolve()}"
        return database_url

    sqlite_file = Path(sqlite_path)
    if not sqlite_file.is_absolute():
        sqlite_file = root_dir / sqlite_file
    return f"sqlite:///{sqlite_file.resolve()}"


@lru_cache
def get_settings() -> Settings:
    yaml_settings = _load_yaml_settings(DEFAULT_SETTINGS_PATH)
    env_settings = EnvironmentSettings()
    database_url = _resolve_database_url(
        ROOT_DIR,
        env_settings.database_url,
        yaml_settings.database.sqlite_path,
    )

    return Settings(
        root_dir=ROOT_DIR,
        app_name=yaml_settings.app.name,
        api_prefix=yaml_settings.app.api_prefix,
        database_url=database_url,
        persona_analysis=yaml_settings.persona_analysis,
        openai_api_key=env_settings.openai_api_key,
        openai_base_url=env_settings.openai_base_url,
    )


def clear_settings_cache() -> None:
    get_settings.cache_clear()
