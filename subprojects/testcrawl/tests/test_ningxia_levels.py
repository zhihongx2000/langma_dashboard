from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.ningxia_levels import LEVEL1_SECTIONS, _extract_date_from_url, _parse_ningxia_list


def test_ningxia_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["高等教育自学考试"]


def test_parse_ningxia_links():
    html = """<html><body>
    <a href="/contents/ZXKS/2026/04/20260401181545000.html">宁夏2026年上半年高等教育自学考试考前温馨提示</a>
    <a href="/contents/GKKS/2026/04/1.html">其它栏目</a>
    </body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_ningxia_list(soup, base_url="https://www.nxjyks.cn/contents/ZXKS/")
    assert len(rows) == 1
    assert "高等教育自学考试" in rows[0]["title"]
    assert rows[0]["url"].endswith("/contents/ZXKS/2026/04/20260401181545000.html")


def test_extract_ningxia_date_from_url():
    assert _extract_date_from_url("https://www.nxjyks.cn/contents/ZXKS/2026/04/20260401181545000.html") == "2026-04-01"
    assert _extract_date_from_url("https://www.nxjyks.cn/contents/ZXKS/index.html") == ""


def test_ningxia_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.nxjyks.cn/contents/ZXKS/",
            "level1": [{"name": "高等教育自学考试", "items": []}],
        }

    monkeypatch.setattr("app.routers.test_local.get_ningxia_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/ningxia/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 1

