from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.gansu_levels import LEVEL1_SECTIONS


def test_gansu_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["閫氱煡鍏憡", "鏀跨瓥瑙勫畾"]


def test_parse_gansu_newslist():
    from app.services.gansu_levels import _parse_newslist

    html = """<html><body><ul class="newslist ny">
      <li><a href="/zixuekaoshi/1.html" title="鏌愬叕鍛?>[閫氱煡鍏憡]鏌愬叕鍛?/a><span>2026-01-01</span></li>
    </ul></body></html>"""
    soup = BeautifulSoup(html, "lxml")
    items = _parse_newslist(soup, base_url="https://www.ganseea.cn/tongzhigonggao631/")
    assert len(items) == 1
    assert items[0]["title"] == "鏌愬叕鍛?
    assert items[0]["publish_date"] == "2026-01-01"
    assert items[0]["url"].startswith("https://www.ganseea.cn/")


def test_gansu_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.ganseea.cn/zixuekaoshi/",
            "level1": [{"name": "閫氱煡鍏憡", "items": []}, {"name": "鏀跨瓥瑙勫畾", "items": []}],
        }

    monkeypatch.setattr("app.routers.crawler_ui.get_gansu_levels", fake)

    with TestClient(app) as client:
        r = client.get("/api/test/gansu/levels")

    assert r.status_code == 200
    assert len(r.json()["level1"]) == 2

