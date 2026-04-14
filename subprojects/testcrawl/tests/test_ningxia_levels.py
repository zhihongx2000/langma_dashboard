from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.ningxia_levels import LEVEL1_SECTIONS, _extract_date_from_url, _parse_ningxia_list


def test_ningxia_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["楂樼瓑鏁欒偛鑷鑰冭瘯"]


def test_parse_ningxia_links():
    html = """<html><body>
    <a href="/contents/ZXKS/2026/04/20260401181545000.html">瀹佸2026骞翠笂鍗婂勾楂樼瓑鏁欒偛鑷鑰冭瘯鑰冨墠娓╅Θ鎻愮ず</a>
    <a href="/contents/GKKS/2026/04/1.html">鍏跺畠鏍忕洰</a>
    </body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_ningxia_list(soup, base_url="https://www.nxjyks.cn/contents/ZXKS/")
    assert len(rows) == 1
    assert "楂樼瓑鏁欒偛鑷鑰冭瘯" in rows[0]["title"]
    assert rows[0]["url"].endswith("/contents/ZXKS/2026/04/20260401181545000.html")


def test_extract_ningxia_date_from_url():
    assert _extract_date_from_url("https://www.nxjyks.cn/contents/ZXKS/2026/04/20260401181545000.html") == "2026-04-01"
    assert _extract_date_from_url("https://www.nxjyks.cn/contents/ZXKS/index.html") == ""


def test_ningxia_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.nxjyks.cn/contents/ZXKS/",
            "level1": [{"name": "楂樼瓑鏁欒偛鑷鑰冭瘯", "items": []}],
        }

    monkeypatch.setattr("app.routers.crawler_ui.get_ningxia_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/ningxia/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 1


