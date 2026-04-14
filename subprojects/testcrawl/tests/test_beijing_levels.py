from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.beijing_levels import LEVEL1_NAMES, _collect_rows_from_ul, _safe_beijing_url


def test_beijing_level_names():
    assert LEVEL1_NAMES == ("淇℃伅鍙戝竷鍙?, "鑷€冩斂绛?, "杩戞湡涓氬姟", "蹇€熼€氶亾", "蹇呭鐭ヨ瘑")


def test_safe_beijing_url():
    assert _safe_beijing_url("https://www.bjeea.cn/html/selfstudy/xxfbt/index.html")
    assert _safe_beijing_url("https://zikao.bjeea.cn/portal")
    assert _safe_beijing_url("https://example.com/a") is None


def test_collect_rows_from_ul():
    html = """<ul class="com-list">
      <li><span class="li-time">2026-03-11</span><a href="/html/selfstudy/xxfbt/2026/0311/87965.html">鍖椾含甯?026骞翠笂鍗婂勾鑷鑰冭瘯瀛﹀＋瀛︿綅鐢虫姤閫氱煡</a></li>
      <li><a href="https://zikao.bjeea.cn/">鑷€冧釜浜轰腑蹇?/a></li>
    </ul>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _collect_rows_from_ul(soup.select_one("ul"), seen=set(), max_items=20)
    assert len(rows) == 2
    assert rows[0]["publish_date"] == "2026-03-11"


def test_beijing_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.bjeea.cn/html/selfstudy/index.html",
            "level1": [{"name": x, "items": []} for x in LEVEL1_NAMES],
        }

    monkeypatch.setattr("app.routers.crawler_ui.get_beijing_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/beijing/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 5


