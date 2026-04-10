import asyncio
import sys
from dataclasses import dataclass

from app.config import get_settings
from app.services.http_client import build_session, decode_response_text

settings = get_settings()


@dataclass
class FetchResult:
    url: str
    html: str
    source: str
    status_code: int | None = None


def fetch_html(url: str, timeout_sec: int | None = None, prefer_browser: bool = True) -> FetchResult:
    timeout = timeout_sec or settings.crawl_timeout_sec

    if prefer_browser and settings.crawl_use_browser:
        browser_result = _fetch_with_playwright(url, timeout)
        if browser_result is not None:
            return browser_result

    return _fetch_with_requests(url, timeout)


def _fetch_with_requests(url: str, timeout_sec: int) -> FetchResult:
    session = build_session()
    response = session.get(url, timeout=timeout_sec)
    response.raise_for_status()
    return FetchResult(
        url=response.url,
        html=decode_response_text(response),
        source="requests",
        status_code=response.status_code,
    )


def _fetch_with_playwright(url: str, timeout_sec: int) -> FetchResult | None:
    try:
        from playwright.sync_api import Error, TimeoutError as PlaywrightTimeoutError, sync_playwright
    except Exception:
        return None

    timeout_ms = min(int(timeout_sec * 1000), settings.playwright_timeout_ms)
    try:
        if sys.platform.startswith("win") and hasattr(asyncio, "WindowsProactorEventLoopPolicy"):
            # On Windows, selector loop cannot spawn Playwright subprocesses.
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=settings.playwright_headless)
            page = browser.new_page()
            page.set_extra_http_headers(
                {
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Cache-Control": "no-cache",
                }
            )
            page.goto(url, wait_until=settings.playwright_wait_until, timeout=timeout_ms)
            page.wait_for_timeout(settings.playwright_post_load_wait_ms)
            html = page.content()
            final_url = page.url
            browser.close()
            return FetchResult(url=final_url, html=html, source="playwright", status_code=200)
    except (PlaywrightTimeoutError, Error):
        return None
    except Exception:
        return None
