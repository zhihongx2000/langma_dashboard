from app.services import section_discovery


def test_discover_sections_falls_back_to_browser_use_when_static_results_are_few(monkeypatch):
    monkeypatch.setattr(section_discovery.settings, "browser_use_min_results_trigger", 3)

    class FakeResult:
        url = "https://example.com"
        html = """
        <html>
          <body>
            <a href="/contact">联系我们</a>
          </body>
        </html>
        """

    monkeypatch.setattr(section_discovery, "fetch_html", lambda *args, **kwargs: FakeResult())
    monkeypatch.setattr(
        section_discovery,
        "discover_sections_with_browser_use",
        lambda url: [("通知公告", "https://example.com/news"), ("报名报考", "https://example.com/signup")],
    )

    results = section_discovery.discover_sections("https://example.com", timeout=5, limit=5)

    assert ("通知公告", "https://example.com/news") in results
    assert ("报名报考", "https://example.com/signup") in results


def test_discover_sections_prefers_static_results_when_enough(monkeypatch):
    monkeypatch.setattr(section_discovery.settings, "browser_use_min_results_trigger", 2)

    class FakeResult:
        url = "https://example.com"
        html = """
        <html>
          <body>
            <a href="/news">通知公告</a>
            <a href="/policy">政策规定</a>
          </body>
        </html>
        """

    monkeypatch.setattr(section_discovery, "fetch_html", lambda *args, **kwargs: FakeResult())
    monkeypatch.setattr(section_discovery, "discover_sections_with_browser_use", lambda url: [("AI", "https://example.com/ai")])

    results = section_discovery.discover_sections("https://example.com", timeout=5, limit=5)

    assert ("通知公告", "https://example.com/news") in results
    assert ("政策规定", "https://example.com/policy") in results
    assert ("AI", "https://example.com/ai") not in results


def test_discover_sections_uses_fixed_rule_for_chongqing():
    results = section_discovery.discover_sections(
        "https://www.cqksy.cn/web/column/col1846543.html",
        timeout=5,
        limit=5,
    )
    assert results == [("自学考试", "https://www.cqksy.cn/web/column/col1846543.html")]

