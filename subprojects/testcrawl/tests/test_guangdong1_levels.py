from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.guangdong1_levels import LEVEL1_SECTIONS, _parse_guangdong1_list, _safe_guangdong1_url


def test_guangdong1_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["鑷鑰冭瘯"]


def test_safe_guangdong1_url():
    assert _safe_guangdong1_url("https://eea.gd.gov.cn/zxks/content/post_4876655.html")
    assert _safe_guangdong1_url("https://eea.gd.gov.cn/zxks/index.html") is None
    assert _safe_guangdong1_url("https://example.com/a") is None


def test_parse_guangdong1_list():
    html = """<html><body><ul>
    <li><a href="/zxks/content/post_4876655.html">骞夸笢鐪?026骞?鏈堣嚜瀛﹁€冭瘯鑰冨墠娓╅Θ鎻愮ず</a><span>2026-04-03</span></li>
    <li><a href="/zxks/index_2.html">2</a></li>
    </ul></body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_guangdong1_list(soup, base_url="https://eea.gd.gov.cn/zxks/index.html")
    assert len(rows) == 1
    assert rows[0]["publish_date"] == "2026-04-03"


def test_guangdong1_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://eea.gd.gov.cn/zxks/index.html",
            "level1": [{"name": "鑷鑰冭瘯", "items": []}],
        }

    monkeypatch.setattr("app.routers.crawler_ui.get_guangdong1_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/guangdong1/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 1


