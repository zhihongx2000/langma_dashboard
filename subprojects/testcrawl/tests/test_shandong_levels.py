from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.shandong_levels import LEVEL1_SECTIONS, _parse_sd_list, _safe_sd_url


def test_shandong_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["鑷鑰冭瘯"]


def test_safe_sd_url():
    assert _safe_sd_url("https://www.sdzk.cn/NewsInfo.aspx?NewsID=7160")
    assert _safe_sd_url("https://www.sdzk.cn/NewsListM.aspx?BCID=5&CID=1163") is None
    assert _safe_sd_url("https://example.com/a") is None


def test_parse_sd_list():
    html = """<html><body>
    <a href="NewsInfo.aspx?NewsID=7160">鑷村北涓滅渷2026骞?鏈堥珮绛夋暀鑲茶嚜瀛﹁€冭瘯鑰冪敓鐨勪竴灏佷俊 2026-03-30</a>
    <a href="javascript:void(0)">涓婁竴椤?/a>
    </body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_sd_list(soup, base_url="https://www.sdzk.cn/NewsListM.aspx?BCID=5&CID=1163")
    assert len(rows) == 1
    assert "楂樼瓑鏁欒偛鑷鑰冭瘯" in rows[0]["title"]


def test_shandong_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.sdzk.cn/NewsListM.aspx?BCID=5&CID=1163",
            "level1": [{"name": "鑷鑰冭瘯", "items": []}],
        }

    monkeypatch.setattr("app.routers.crawler_ui.get_shandong_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/shandong/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 1


