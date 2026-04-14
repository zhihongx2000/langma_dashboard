from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.hebei_levels import LEVEL1_SECTIONS, _parse_notice_block, _safe_hebei_url


def test_hebei_section_names():
    assert LEVEL1_SECTIONS == ("鏈€鏂伴€氱煡鍏憡", "鏌ヨ涓績", "鑰冪敓蹇呰")


def test_safe_hebei_url():
    assert _safe_hebei_url("https://zk.hebeea.edu.cn/HebzkWeb/content?id=abc")
    assert _safe_hebei_url("https://www.hebeea.edu.cn/c/2026-04-02/492219.html")
    assert _safe_hebei_url("https://example.com/a") is None


def test_parse_notice_block():
    html = """<div class="tongzhi_list_box">
      <div class="tongzhi_nr"><a href="/HebzkWeb/content?id=d29c8354-c485-4cab-a86a-157677340ac5" title="2026骞翠笂鍗婂勾娌冲寳鐪侀珮绛夋暀鑲茶嚜瀛﹁€冭瘯鑰冨墠鎻愮ず锛堜竴锛?>2026骞翠笂鍗婂勾娌冲寳鐪侀珮绛夋暀鑲茶嚜瀛﹁€冭瘯鑰冨墠鎻愮ず锛堜竴锛?/a></div>
      <div class="tongzhi_fabushijian">2026-04-07</div>
    </div>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_notice_block(soup)
    assert len(rows) == 1
    assert rows[0]["publish_date"] == "2026-04-07"


def test_hebei_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://zk.hebeea.edu.cn/HebzkWeb/index",
            "level1": [{"name": x, "items": []} for x in LEVEL1_SECTIONS],
        }

    monkeypatch.setattr("app.routers.crawler_ui.get_hebei_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/hebei/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 3


