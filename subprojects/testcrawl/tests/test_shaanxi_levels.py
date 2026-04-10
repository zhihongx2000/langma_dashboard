from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.shaanxi_levels import LEVEL1_SECTIONS, _extract_date_like, _parse_shaanxi_list, _safe_shaanxi_article_url


def test_shaanxi_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["自学考试"]


def test_safe_shaanxi_article_url():
    assert _safe_shaanxi_article_url("https://www.sneea.cn/info/1032/17260.htm")
    assert _safe_shaanxi_article_url("http://www.sneea.cn/info/1032/17260.html")
    assert _safe_shaanxi_article_url("https://www.sneea.cn/zc/zxks.htm") is None
    assert _safe_shaanxi_article_url("https://example.com/info/1/2.htm") is None


def test_extract_date_like_shaanxi():
    assert _extract_date_like("公告 2026年4月1日") == "2026-04-01"


def test_parse_shaanxi_list():
    html = """<html><body><ul>
    <li><a href="../info/1032/17260.htm">陕西省自学考试通知</a></li>
    </ul></body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_shaanxi_list(soup, base_url="https://www.sneea.cn/zc/zxks.htm")
    assert len(rows) == 1
    assert rows[0]["url"] == "https://www.sneea.cn/info/1032/17260.htm"
    assert "17260" in rows[0]["url"]


def test_shaanxi_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.sneea.cn/zc/zxks.htm",
            "level1": [{"name": "自学考试", "items": []}],
        }

    monkeypatch.setattr("app.routers.test_local.get_shaanxi_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/shaanxi/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 1
