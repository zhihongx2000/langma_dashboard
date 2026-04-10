from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.shanxi_levels import LEVEL1_SECTIONS, _extract_date_like, _parse_shanxi_list, _safe_shanxi_article_url


def test_shanxi_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["自学考试"]


def test_safe_shanxi_article_url():
    assert _safe_shanxi_article_url("http://www.sxkszx.cn/news/202643/n0315127133.html")
    assert _safe_shanxi_article_url("http://www.sxkszx.cn/news/zxks/index.html") is None
    assert _safe_shanxi_article_url("https://example.com/a") is None


def test_extract_date_like():
    assert _extract_date_like("公告 2026年4月1日") == "2026-04-01"
    assert _extract_date_like("x 2025-12-30") == "2025-12-30"


def test_parse_shanxi_list():
    html = """<html><body><ul>
    <li><a href="/news/202643/n0315127133.html">山西省2026年考试说明</a></li>
    </ul></body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_shanxi_list(soup, base_url="http://www.sxkszx.cn/news/zxks/index.html")
    assert len(rows) == 1
    assert "n0315127133" in rows[0]["url"]


def test_shanxi_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "http://www.sxkszx.cn/news/zxks/index.html",
            "level1": [{"name": "自学考试", "items": []}],
        }

    monkeypatch.setattr("app.routers.test_local.get_shanxi_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/shanxi/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 1
