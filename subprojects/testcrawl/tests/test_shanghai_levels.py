from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.shanghai_levels import LEVEL1_SECTIONS, _extract_date_like, _parse_shanghai_list, _safe_shanghai_article_url


def test_shanghai_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["自考新闻", "考试日程", "政策法规", "大纲教材"]


def test_safe_shanghai_article_url():
    assert _safe_shanghai_article_url("https://www.shmeea.edu.cn/page/04100/20260403/20158.html")
    assert _safe_shanghai_article_url("https://www.shmeea.edu.cn/page/04100/") is None
    assert _safe_shanghai_article_url("https://example.com/page/04100/20260403/20158.html") is None


def test_extract_date_like_shanghai():
    assert _extract_date_like("发布时间 2026-04-03") == "2026-04-03"


def test_parse_shanghai_list():
    html = """<html><body><ul>
    <li><a href="/page/04100/20260403/20158.html">上海市2026年上半年高等教育自学考试考前提醒</a><span class="listTime">2026-04-03</span></li>
    </ul></body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_shanghai_list(soup, base_url="https://www.shmeea.edu.cn/page/04100/")
    assert len(rows) == 1
    assert rows[0]["url"] == "https://www.shmeea.edu.cn/page/04100/20260403/20158.html"
    assert rows[0]["publish_date"] == "2026-04-03"


def test_shanghai_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.shmeea.edu.cn/page/04000/",
            "level1": [{"name": n, "items": []} for n, _ in LEVEL1_SECTIONS],
        }

    monkeypatch.setattr("app.routers.test_local.get_shanghai_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/shmeea/levels")
        r2 = client.get("/api/test/shanghai/levels")
    assert r.status_code == 200
    assert r2.status_code == 200
    assert len(r.json()["level1"]) == 4
