from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.zhejiang_levels import LEVEL1_SECTIONS, _parse_zj_list, _safe_zj_url


def test_zhejiang_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["鏈€鏂版秷鎭?, "鏀跨瓥鏂囦欢", "涓撲笟璁″垝", "鑰冭瘯鎶ュ悕", "杞€冨厤鑰?, "姣曚笟鍔炵悊"]


def test_safe_zj_url():
    assert _safe_zj_url("https://www.zjzs.net/art/2025/6/20/art_43_11321.html")
    assert _safe_zj_url("https://www.zjzs.net/col/col41/index.html")
    assert _safe_zj_url("https://example.com/a") is None


def test_parse_zj_list():
    html = """<html><body><ul>
    <li>2025-06-20 <a href="/art/2025/6/20/art_43_11321.html">2025骞?0鏈堟禉姹熺渷楂樼瓑鏁欒偛鑷鑰冭瘯鎶ュ悕鍏憡</a></li>
    <li><a href="/col/col41/index.html">鏀跨瓥鏂囦欢</a></li>
    </ul></body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_zj_list(soup, base_url="https://www.zjzs.net/col/col43/index.html")
    assert len(rows) == 2
    assert rows[0]["publish_date"] == "2025-06-20"


def test_zhejiang_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.zjzs.net/col/col21/index.html",
            "level1": [{"name": x[0], "items": []} for x in LEVEL1_SECTIONS],
        }

    monkeypatch.setattr("app.routers.crawler_ui.get_zhejiang_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/zhejiang/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 6


