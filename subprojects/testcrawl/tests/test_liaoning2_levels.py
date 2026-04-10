from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.liaoning2_levels import LEVEL1_SECTIONS, _parse_liaoning2_list, _safe_liaoning2_url


def test_liaoning2_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["温馨提示", "政策规定", "考生须知"]


def test_safe_liaoning2_url():
    assert _safe_liaoning2_url("https://zk.lnzsks.com/lnzk.wb/content/345")
    assert _safe_liaoning2_url("https://zk.lnzsks.com/lnzk.wb/catalog/2") is None
    assert _safe_liaoning2_url("https://example.com/a") is None


def test_parse_liaoning2_list():
    html = """<html><body><ul>
    <li><a href="/lnzk.wb/content/345">辽宁省2026年上半年高等教育自学考试准考证打印温馨提示</a><span>2026-04-03</span></li>
    <li><a href="/lnzk.wb/catalog/2">更多</a></li>
    </ul></body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_liaoning2_list(soup, base_url="https://zk.lnzsks.com/lnzk.wb/catalog/2")
    assert len(rows) == 1
    assert rows[0]["publish_date"] == "2026-04-03"


def test_liaoning2_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://zk.lnzsks.com/lnzk.wb/",
            "level1": [
                {"name": "温馨提示", "items": []},
                {"name": "政策规定", "items": []},
                {"name": "考生须知", "items": []},
            ],
        }

    monkeypatch.setattr("app.routers.test_local.get_liaoning2_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/liaoning2/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 3

