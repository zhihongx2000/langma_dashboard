from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.anhui_levels import LEVEL1_SECTIONS, _parse_anhui_list, _safe_anhui_content_url


def test_anhui_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["鑷€冨姩鎬?, "鑰冭瘯瀹夋帓", "鏁欐潗鐗堟湰", "涓昏€冮櫌鏍?, "鏀跨瓥鏂囦欢", "鍔╁绠＄悊", "涓氬姟鍔炵悊", "鏈", "涓撶"]


def test_safe_anhui_content_url():
    assert _safe_anhui_content_url("https://www.ahzsks.cn/gdjyzxks/8609.htm")
    assert _safe_anhui_content_url("https://www.ahzsks.cn/gdjyzxks/search2.jsp?c=77") is None
    assert _safe_anhui_content_url("https://example.com/a") is None


def test_parse_anhui_list():
    html = """<html><body><ul>
    <li><a href="/gdjyzxks/8609.htm">瀹夊窘鐪侀珮绛夋暀鑲茶嚜瀛﹁€冭瘯2026骞?鏈堣€冭瘯鏁欐潗鐗堟湰鐩綍</a><span>2025-12-25</span></li>
    <li><a href="/gdjyzxks/675.htm">鑷€冩寚鍗?/a></li>
    </ul></body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_anhui_list(soup, base_url="https://www.ahzsks.cn/gdjyzxks/search2.jsp?c=81")
    assert len(rows) == 1
    assert rows[0]["publish_date"] == "2025-12-25"


def test_anhui_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.ahzsks.cn/gdjyzxks/",
            "level1": [{"name": "鑷€冨姩鎬?, "items": []}],
        }

    monkeypatch.setattr("app.routers.crawler_ui.get_anhui_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/anhui/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 1


