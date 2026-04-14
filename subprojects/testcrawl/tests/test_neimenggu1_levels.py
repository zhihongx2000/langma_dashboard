from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.neimenggu1_levels import (
    LEVEL1_SECTIONS,
    _date_from_article_url,
    _parse_neimenggu1_list,
    _safe_neimenggu1_article_url,
)


def test_neimenggu1_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["鍏憡鏍?, "鏀跨瓥瑙勫畾"]


def test_safe_neimenggu1_article_url():
    assert _safe_neimenggu1_article_url(
        "https://www.nm.zsks.cn/kszs/zxks/ggl/202601/t20260123_46212.html"
    )
    assert _safe_neimenggu1_article_url("https://www.nm.zsks.cn/kszs/zxks/ggl/") is None
    assert (
        _safe_neimenggu1_article_url(
            "https://www.nm.zsks.cn/kszs/zxks/wsbmbkxt_zx/202601/t20260123_1.html"
        )
        is None
    )


def test_date_from_article_url_neimenggu():
    assert (
        _date_from_article_url("https://www.nm.zsks.cn/kszs/zxks/zcfg/202508/t20250813_46011.html")
        == "2025-08-13"
    )


def test_parse_neimenggu1_list():
    html = """<html><body><ul>
    <li><a href="../ggl/202601/t20260123_46212.html">鍏充簬鑰冭瘯鐨勯€氱煡</a></li>
    </ul></body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_neimenggu1_list(soup, base_url="https://www.nm.zsks.cn/kszs/zxks/zcfg/index.html")
    assert len(rows) == 1
    assert "46212" in rows[0]["url"]
    assert rows[0]["publish_date"] == "2026-01-23"


def test_neimenggu1_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.nm.zsks.cn/kszs/zxks/",
            "level1": [{"name": n, "items": []} for n, _ in LEVEL1_SECTIONS],
        }

    monkeypatch.setattr("app.routers.crawler_ui.get_neimenggu1_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/neimenggu1/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 2

