from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.xinjiang_levels import XINJIANG_LEVEL1_PAGES


def test_xinjiang_level1_spec():
    names = [n for n, _ in XINJIANG_LEVEL1_PAGES]
    assert names == ["閫氱煡鍏憡", "鏀跨瓥璧勮"]


def test_xinjiang_parse_list_page():
    from app.services.xinjiang_levels import _parse_list_page

    html = """<div id="conts"><div class="tabPanel"><ul class="list">
      <li><a href="/c/2026-01-01/1.shtml"><span class="time">2026-01-01</span><span class="txt">娴嬭瘯鏍囬</span></a></li>
    </ul></div></div>"""
    soup = BeautifulSoup(html, "lxml")
    items = _parse_list_page(soup, base_url="https://www.xjzk.gov.cn/zxks/gdjyzxks/tzgg/")
    assert len(items) == 1
    assert items[0]["title"] == "娴嬭瘯鏍囬"
    assert items[0]["publish_date"] == "2026-01-01"
    assert items[0]["url"].startswith("https://www.xjzk.gov.cn/")


def test_xinjiang_policy_column_includes_neea_links():
    from app.services.xinjiang_levels import _parse_list_page

    html = """<div id="conts"><div class="tabPanel"><ul class="list">
      <li><a href="https://zikao.neea.edu.cn/html1/folder/1512/1101-1.htm"><span class="time">2023-02-07</span><span class="txt">楂樼瓑鏁欒偛鑷鑰冭瘯鍒跺害</span></a></li>
    </ul></div></div>"""
    soup = BeautifulSoup(html, "lxml")
    policy = _parse_list_page(
        soup, base_url="https://www.xjzk.gov.cn/zxks/gdjyzxks/zczx/", policy_column=True
    )
    assert len(policy) == 1
    assert "neea.edu.cn" in policy[0]["url"]

    notice = _parse_list_page(
        soup, base_url="https://www.xjzk.gov.cn/zxks/gdjyzxks/tzgg/", policy_column=False
    )
    assert len(notice) == 0


def test_xinjiang_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.xjzk.gov.cn/zxks/gdjyzxks/tzgg/",
            "level1": [
                {"name": "閫氱煡鍏憡", "items": [{"title": "a", "url": "https://www.xjzk.gov.cn/c/1.shtml", "publish_date": ""}]},
                {"name": "鏀跨瓥璧勮", "items": []},
            ],
        }

    monkeypatch.setattr("app.routers.crawler_ui.get_xinjiang_levels", fake)

    with TestClient(app) as client:
        r = client.get("/api/test/xinjiang/levels")

    assert r.status_code == 200
    payload = r.json()
    assert len(payload["level1"]) == 2
    assert payload["level1"][0]["name"] == "閫氱煡鍏憡"

