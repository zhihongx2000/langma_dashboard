from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.hainan_levels import LEVEL1_SECTIONS, _extract_date_from_url, _parse_zxks_links


def test_hainan_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["自学考试"]


def test_parse_hainan_links():
    html = """<html><body>
    <a href="/ywdt/zxks/202604/t20260401_4052762.html">【图文】 海南省2026年上半年高等教育自学考试考前温馨提示</a>
    <a href="/ywdt/mtpj/202604/t20260402_4053536.html">其它考试</a>
    </body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_zxks_links(soup, base_url="http://ea.hainan.gov.cn/ywdt/zxks/")
    assert len(rows) == 1
    assert "高等教育自学考试" in rows[0]["title"]
    assert rows[0]["publish_date"] == "2026-04-01"


def test_extract_date_from_url():
    assert _extract_date_from_url("http://ea.hainan.gov.cn/ywdt/zxks/202604/t20260401_4052762.html") == "2026-04-01"
    assert _extract_date_from_url("http://ea.hainan.gov.cn/ywdt/zxks/index.html") == ""


def test_hainan_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "http://ea.hainan.gov.cn/ywdt/zxks/",
            "level1": [{"name": "自学考试", "items": []}],
        }

    monkeypatch.setattr("app.routers.test_local.get_hainan_levels", fake)

    with TestClient(app) as client:
        r = client.get("/api/test/hainan/levels")

    assert r.status_code == 200
    assert len(r.json()["level1"]) == 1

