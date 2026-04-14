from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.chongqing_levels import LEVEL1_SECTIONS, _parse_chongqing_list, _safe_chongqing_article_url


def test_chongqing_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["鑷鑰冭瘯"]


def test_safe_chongqing_article_url():
    assert _safe_chongqing_article_url("https://www.cqksy.cn/web/article/1/202603/1234567890.html")
    assert _safe_chongqing_article_url("https://www.cqksy.cn/web/column/col1846543.html") is None
    assert _safe_chongqing_article_url("https://example.com/web/article/1/202603/123.html") is None


def test_parse_chongqing_list():
    html = """<html><body><ul>
    <li><a href="/web/article/1/202603/1234567890.html">閲嶅簡甯傞珮绛夋暀鑲茶嚜瀛﹁€冭瘯宸ヤ綔瀹夋帓</a><span>2026-03-20</span></li>
    <li><a href="/web/column/col1846543.html">鑷鑰冭瘯</a></li>
    </ul></body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_chongqing_list(soup, base_url="https://www.cqksy.cn/web/column/col1846543.html")
    assert len(rows) == 1
    assert rows[0]["publish_date"] == "2026-03-20"


def test_chongqing_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.cqksy.cn/web/column/col1846543.html",
            "level1": [
                {"name": "鑷鑰冭瘯", "items": []},
            ],
        }

    monkeypatch.setattr("app.routers.crawler_ui.get_chongqing_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/chongqing/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 1


