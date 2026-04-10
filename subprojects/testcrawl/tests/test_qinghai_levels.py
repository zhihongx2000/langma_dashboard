from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.qinghai_levels import LEVEL1_SECTIONS, _parse_qinghai_list


def test_qinghai_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["自学考试"]


def test_parse_qinghai_links():
    html = """<html><body>
    <ul class="Culr-list01 gp-f16">
    <li><span class="date gp-f14">2026-04-02</span>
    <a href="5667.htm" target="_blank">青海省2026年上半年自学考试温馨提示</a></li>
    </ul>
    <a href="/zyym/ztzl/zxksz/index1.htm">2</a>
    <a href="/zyym/ztzl/zcfgz/100.htm">其它栏目</a>
    </body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_qinghai_list(soup, base_url="https://www.qhjyks.com/zyym/ztzl/zxksz/index.htm")
    assert len(rows) == 1
    assert "自学考试" in rows[0]["title"]
    assert rows[0]["url"].endswith("/zyym/ztzl/zxksz/5667.htm")
    assert rows[0]["publish_date"] == "2026-04-02"


def test_parse_qinghai_links_fallback_without_culr():
    html = """<html><body>
    <a href="/zyym/ztzl/zxksz/5667.htm">青海省2026年上半年自学考试温馨提示</a>
    <a href="/zyym/ztzl/zxksz/index1.htm">2</a>
    <a href="/zyym/ztzl/zcfgz/100.htm">其它栏目</a>
    </body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_qinghai_list(soup, base_url="https://www.qhjyks.com/zyym/ztzl/zxksz/index.htm")
    assert len(rows) == 1
    assert rows[0]["publish_date"] == ""


def test_qinghai_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.qhjyks.com/zyym/ztzl/zxksz/index.htm",
            "level1": [{"name": "自学考试", "items": []}],
        }

    monkeypatch.setattr("app.routers.test_local.get_qinghai_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/qinghai/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 1

