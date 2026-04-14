from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.fujian_levels import LEVEL1_SECTIONS, _date_from_article_url, _parse_fujian_list, _safe_fujian_article_url


def test_fujian_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["鍏ず鍏憡", "鑷€冨姩鎬?, "鏀跨瓥鏂囦欢"]


def test_safe_fujian_article_url():
    assert _safe_fujian_article_url("http://www.eeafj.cn/zkgsgg/20260401/14450.html")
    assert _safe_fujian_article_url("http://www.eeafj.cn/zkzkzc/20250718/14135.html")
    assert _safe_fujian_article_url("http://www.eeafj.cn/sygggs/20260101/1.html") is None
    assert _safe_fujian_article_url("http://www.eeafj.cn/zkgsgg/") is None


def test_date_from_article_url():
    assert _date_from_article_url("http://www.eeafj.cn/zkzkdt/20221026/12409.html") == "2022-10-26"


def test_parse_fujian_list():
    html = """<html><body><ul>
    <li><a href="/zkgsgg/20260401/14450.html">[04-01] 绂忓缓鐪?026骞翠笂鍗婂勾鑷鑰冭瘯娓╅Θ鎻愰啋</a></li>
    </ul></body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_fujian_list(soup, base_url="https://www.eeafj.cn/zkgsgg/")
    assert len(rows) == 1
    assert rows[0]["publish_date"] == "2026-04-01"
    assert "娓╅Θ鎻愰啋" in rows[0]["title"]


def test_fujian_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.eeafj.cn/zxks/",
            "level1": [{"name": n, "items": []} for n, _ in LEVEL1_SECTIONS],
        }

    monkeypatch.setattr("app.routers.crawler_ui.get_fujian_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/fujian/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 3

