from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.hubei_levels import LEVEL1_SECTIONS, _parse_hubei_list, _safe_hubei_content_url


def test_hubei_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["鑷鑰冭瘯", "绀句細鍔╁", "鑰冪睄绠＄悊", "鑷€冭€冨姟", "鑷€冭鍒?]


def test_safe_hubei_content_url():
    assert _safe_hubei_content_url("http://www.hbea.edu.cn/html/2026-04/15753.shtml")
    assert _safe_hubei_content_url("https://www.hbea.edu.cn/html/zxks/index.shtml") is None
    assert _safe_hubei_content_url("https://example.com/a") is None


def test_parse_hubei_list():
    html = """<html><body><ul>
    <li><a href="/html/2026-04/15753.shtml">婀栧寳鐪?026骞?鏈堥珮绛夋暀鑲茶嚜瀛﹁€冭瘯鑰冨墠娓╅Θ鎻愮ず 2026骞?鏈?鏃?/a></li>
    <li><a href="/html/zxks/index.shtml">鑷鑰冭瘯</a></li>
    </ul></body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_hubei_list(soup, base_url="https://www.hbea.edu.cn/html/zxks/index.shtml")
    assert len(rows) == 1
    assert rows[0]["publish_date"] == "2026-04-03"


def test_hubei_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.hbea.edu.cn/html/zxks/index.shtml",
            "level1": [
                {"name": "鑷鑰冭瘯", "items": []},
                {"name": "绀句細鍔╁", "items": []},
                {"name": "鑰冪睄绠＄悊", "items": []},
                {"name": "鑷€冭€冨姟", "items": []},
                {"name": "鑷€冭鍒?, "items": []},
            ],
        }

    monkeypatch.setattr("app.routers.crawler_ui.get_hubei_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/hubei/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 5


