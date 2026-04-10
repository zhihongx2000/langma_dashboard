from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.hubei_levels import LEVEL1_SECTIONS, _parse_hubei_list, _safe_hubei_content_url


def test_hubei_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["自学考试", "社会助学", "考籍管理", "自考考务", "自考计划"]


def test_safe_hubei_content_url():
    assert _safe_hubei_content_url("http://www.hbea.edu.cn/html/2026-04/15753.shtml")
    assert _safe_hubei_content_url("https://www.hbea.edu.cn/html/zxks/index.shtml") is None
    assert _safe_hubei_content_url("https://example.com/a") is None


def test_parse_hubei_list():
    html = """<html><body><ul>
    <li><a href="/html/2026-04/15753.shtml">湖北省2026年4月高等教育自学考试考前温馨提示 2026年4月3日</a></li>
    <li><a href="/html/zxks/index.shtml">自学考试</a></li>
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
                {"name": "自学考试", "items": []},
                {"name": "社会助学", "items": []},
                {"name": "考籍管理", "items": []},
                {"name": "自考考务", "items": []},
                {"name": "自考计划", "items": []},
            ],
        }

    monkeypatch.setattr("app.routers.test_local.get_hubei_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/hubei/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 5

