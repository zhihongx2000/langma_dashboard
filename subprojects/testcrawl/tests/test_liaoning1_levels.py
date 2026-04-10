from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.liaoning1_levels import LEVEL1_SECTIONS, _parse_liaoning1_list, _safe_liaoning1_url


def test_liaoning1_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["自学考试"]


def test_safe_liaoning1_url():
    assert _safe_liaoning1_url("https://www.lnzsks.com/newsinfo/IMS_20260408_45803_1VQRiYoMGJ.htm")
    assert _safe_liaoning1_url("https://www.lnzsks.com/listinfo/zxks_1.html") is None
    assert _safe_liaoning1_url("https://example.com/a") is None


def test_parse_liaoning1_list():
    html = """<html><body><ul>
    <li><a href="/newsinfo/IMS_20260408_45803_1VQRiYoMGJ.htm">辽宁省2026年上半年高等教育自学考试考前提示</a><span>2026-04-08</span></li>
    <li><a href="javascript:void(0)">下一页</a></li>
    </ul></body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_liaoning1_list(soup, base_url="https://www.lnzsks.com/listinfo/zxks_1.html")
    assert len(rows) == 1
    assert rows[0]["publish_date"] == "2026-04-08"


def test_liaoning1_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.lnzsks.com/listinfo/zxks_1.html",
            "level1": [{"name": "自学考试", "items": []}],
        }

    monkeypatch.setattr("app.routers.test_local.get_liaoning1_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/liaoning1/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 1

