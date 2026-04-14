from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.jiangsu_levels import LEVEL1_SECTIONS


def test_jiangsu_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == [
        "鎷涜€冧俊鎭?,
        "鏀跨瓥鏂囦欢",
        "鑷€冨彂灞曟鍐?,
        "鑰冭瘯璁″垝-涓撲笟寤鸿",
        "鑰冭瘯璁″垝-鑰冭瘯鏃ョ▼",
        "鑰冭瘯璁″垝-鑰冭瘯澶х翰",
        "鑰冭瘯璁″垝-璁″垝绠€缂?,
        "鑰冭瘯淇℃伅-鎶ュ悕",
        "鑰冭瘯淇℃伅-鑰冭瘯",
        "鑰冭瘯淇℃伅-鎴愮哗",
        "鑰冪睄绠＄悊-瀹炶返璁烘枃",
        "鑰冪睄绠＄悊-鏈璧勫",
        "鑰冪睄绠＄悊-姣曚笟鍔炵悊",
        "鑰冪睄绠＄悊-杞€冨厤鑰?,
        "鑰冪睄绠＄悊-瀛﹀＋瀛︿綅",
    ]
    assert len(names) == 15


def test_parse_jiangsu_news_list():
    from app.services.jiangsu_levels import _parse_news_list

    html = """<html><body><ul class="news-list">
      <li><a class="content-list-ul-a" href="//www.jseea.cn/content/redirect.do?id=1" target="_blank">娴嬭瘯鏍囬 <span>2026-01-01</span></a></li>
    </ul></body></html>"""
    soup = BeautifulSoup(html, "lxml")
    items = _parse_news_list(soup, base_url="https://www.jseea.cn/webfile/selflearning/selflearning_infomation/")
    assert len(items) == 1
    assert items[0]["title"] == "娴嬭瘯鏍囬"
    assert items[0]["publish_date"] == "2026-01-01"
    assert items[0]["url"].startswith("https://www.jseea.cn/content/")


def test_jiangsu_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.jseea.cn/webfile/examination/selflearning/",
            "level1": [{"name": "鎷涜€冧俊鎭?, "items": []}],
        }

    monkeypatch.setattr("app.routers.crawler_ui.get_jiangsu_levels", fake)

    with TestClient(app) as client:
        r = client.get("/api/test/jiangsu/levels")

    assert r.status_code == 200
    assert r.json()["level1"][0]["name"] == "鎷涜€冧俊鎭?

