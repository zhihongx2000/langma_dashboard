from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.henan1_levels import LEVEL1_SECTIONS, _parse_henan_links


def test_henan1_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["自学考试"]


def test_parse_henan_links():
    html = """<html><body>
    <a href="/zixuekaoshi/2026/0101/1.html">河南省高等教育自学考试公告</a>
    <a href="/other/1.html">其它栏目</a>
    </body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_henan_links(soup, base_url="https://www.haeea.cn/zixuekaoshi/")
    assert len(rows) == 1
    assert "自学考试" in rows[0]["title"]
    assert "/zixuekaoshi/" in rows[0]["url"]


def test_henan1_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "http://www.haeea.cn/zixuekaoshi/",
            "level1": [{"name": "自学考试", "items": []}],
        }

    monkeypatch.setattr("app.routers.test_local.get_henan1_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/henan1/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 1

