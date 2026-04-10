from app.services import fetcher


def test_fetch_html_falls_back_to_requests(monkeypatch):
    calls: list[str] = []

    monkeypatch.setattr(fetcher.settings, "crawl_use_browser", True)

    def fake_browser(url: str, timeout_sec: int):
        calls.append("browser")
        return None

    def fake_requests(url: str, timeout_sec: int):
        calls.append("requests")
        return fetcher.FetchResult(url=url, html="<html></html>", source="requests", status_code=200)

    monkeypatch.setattr(fetcher, "_fetch_with_playwright", fake_browser)
    monkeypatch.setattr(fetcher, "_fetch_with_requests", fake_requests)

    result = fetcher.fetch_html("https://example.com", timeout_sec=5, prefer_browser=True)

    assert result.source == "requests"
    assert calls == ["browser", "requests"]


def test_fetch_html_uses_browser_when_available(monkeypatch):
    monkeypatch.setattr(fetcher.settings, "crawl_use_browser", True)

    def fake_browser(url: str, timeout_sec: int):
        return fetcher.FetchResult(url=url, html="<html>ok</html>", source="playwright", status_code=200)

    monkeypatch.setattr(fetcher, "_fetch_with_playwright", fake_browser)

    result = fetcher.fetch_html("https://example.com", timeout_sec=5, prefer_browser=True)

    assert result.source == "playwright"

