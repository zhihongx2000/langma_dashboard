from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.tianjin_levels import LEVEL1_SECTIONS, _parse_tj_list, _safe_tj_url


def test_tianjin_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["鑷鑰冭瘯", "鑷€冭€冪敓鏈嶅姟骞冲彴", "閲嶈鎻愮ず", "鑷€冩寚鍗?, "淇℃伅鏌ヨ", "鍜ㄨ娓犻亾"]


def test_safe_tj_url():
    assert _safe_tj_url("http://www.zhaokao.net/zxks/system/2026/04/02/030009549.shtml")
    assert _safe_tj_url("http://www.zhaokao.net/sygl/system/2024/02/06/030006994.shtml") is None
    assert _safe_tj_url("https://example.com/a") is None


def test_parse_tj_list():
    html = """<html><body>
    <a href="http://www.zhaokao.net/zxks/system/2026/04/02/030009549.shtml">鑷鑰冭瘯鑰冨墠蹇呰鈥斺€?026骞翠笂鍗婂勾澶╂触甯傞珮绛夋暀鑲茶嚜瀛﹁€冭瘯灏嗕簬4鏈?1鏃ヨ嚦12鏃?/a>
    <a href="javascript:void(0)">涓婁竴椤?/a>
    </body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_tj_list(soup, base_url="http://www.zhaokao.net/zxks/zyts/index.shtml")
    assert len(rows) == 1
    assert "鑷鑰冭瘯" in rows[0]["title"]


def test_tianjin_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "http://www.zhaokao.net/zxks/zyts/index.shtml",
            "level1": [{"name": x[0], "items": []} for x in LEVEL1_SECTIONS],
        }

    monkeypatch.setattr("app.routers.crawler_ui.get_tianjin_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/tianjin/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 6


