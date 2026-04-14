from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.yunnan_levels import LEVEL1_SECTIONS, _extract_date_like, _parse_yunnan_list


def test_yunnan_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["鑷鑰冭瘯"]


def test_parse_yunnan_links():
    html = """<html><body>
    <a href="https://www.ynzs.cn/html/content/8407.html">2026骞翠笂鍗婂勾浜戝崡鐪佺95娆￠珮绛夋暀鑲茶嚜瀛﹁€冭瘯鍜岄珮鏍℃暀甯堣祫鏍艰瀹氳绋嬭€冭瘯娓╅Θ鎻愮ず</a>
    <a href="https://www.ynzs.cn/html/web/zkdt-zxks/index.html">鑷鑰冭瘯鏍忕洰</a>
    </body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_yunnan_list(soup, base_url="https://www.ynzs.cn/html/web/zkdt-zxks/index.html")
    assert len(rows) == 1
    assert "楂樼瓑鏁欒偛鑷鑰冭瘯" in rows[0]["title"]
    assert rows[0]["url"].endswith("/html/content/8407.html")


def test_extract_yunnan_date_like():
    assert _extract_date_like("2025/11/10 浜戝崡鐪侀珮绛夋暀鑲茶嚜瀛﹁€冭瘯姣曚笟鐢宠鍔炶瘉椤荤煡") == "2025-11-10"
    assert _extract_date_like("鏃犳棩鏈?) == ""


def test_yunnan_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.ynzs.cn/html/web/zkdt-zxks/index.html",
            "level1": [{"name": "鑷鑰冭瘯", "items": []}],
        }

    monkeypatch.setattr("app.routers.crawler_ui.get_yunnan_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/yunnan/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 1


