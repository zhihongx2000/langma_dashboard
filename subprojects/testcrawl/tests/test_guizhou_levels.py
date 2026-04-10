from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.guizhou_levels import LEVEL1_SECTIONS, _date_from_article_url, _parse_guizhou_list, _safe_guizhou_article_url


def test_guizhou_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["考试报名", "专业计划", "通知公告"]


def test_safe_guizhou_article_url():
    assert _safe_guizhou_article_url(
        "http://zsksy.guizhou.gov.cn/zxks/ksbm/202604/t20260407_89968270.html"
    )
    assert _safe_guizhou_article_url(
        "http://zsksy.guizhou.gov.cn/zxks/tzgg_5375724/202603/t20260309_89619111.html"
    )
    assert _safe_guizhou_article_url("http://zsksy.guizhou.gov.cn/zxks/ksbm/") is None
    assert _safe_guizhou_article_url("https://example.com/a") is None


def test_date_from_article_url():
    assert _date_from_article_url(
        "http://zsksy.guizhou.gov.cn/zxks/ksjh/202404/t20240410_84187881.html"
    ) == "2024-04-10"


def test_parse_guizhou_list():
    html = """<html><body><ul>
    <li><a href="/zxks/ksbm/202604/t20260407_89968270.html">贵州省2026年上半年高等教育自学考试考前提示</a></li>
    </ul></body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_guizhou_list(soup, base_url="http://zsksy.guizhou.gov.cn/zxks/ksbm/")
    assert len(rows) == 1
    assert rows[0]["publish_date"] == "2026-04-07"


def test_guizhou_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "http://zsksy.guizhou.gov.cn/zxks/ksjh/index.html",
            "level1": [{"name": n, "items": []} for n, _ in LEVEL1_SECTIONS],
        }

    monkeypatch.setattr("app.routers.test_local.get_guizhou_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/guizhou/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 3
