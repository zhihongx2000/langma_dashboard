from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Exam Crawler API"
    app_env: str = "dev"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    database_url: str = "sqlite:///./testcrawl.db"
    admin_api_key: str = "change-this-api-key"

    crawl_timeout_sec: int = 20
    crawl_max_sections_per_province: int = 8
    crawl_max_articles_per_section: int = 20
    crawl_request_delay_sec: float = 1.0
    crawl_use_browser: bool = True
    playwright_headless: bool = True
    playwright_wait_until: str = "domcontentloaded"
    playwright_timeout_ms: int = 20000
    playwright_post_load_wait_ms: int = 1000
    browser_use_enabled: bool = False
    browser_use_model: str = "gpt-4.1-mini"
    browser_use_max_steps: int = 8
    browser_use_result_limit: int = 8
    browser_use_min_results_trigger: int = 3
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    ai_search_model: str = "deepseek-chat"
    ai_search_candidates: int = 120
    ai_search_limit: int = 20
    deepseek_api_key: str | None = None
    deepseek_api_base_url: str = "https://api.deepseek.com/v1"
    auto_refresh_enabled: bool = True
    auto_refresh_hour: int = 12
    auto_refresh_minute: int = 0
    auto_refresh_timezone: str = "Asia/Shanghai"


@lru_cache
def get_settings() -> Settings:
    return Settings()
