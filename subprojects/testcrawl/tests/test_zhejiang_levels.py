from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.zhejiang_levels import LEVEL1_SECTIONS, _parse_zj_list, _safe_zj_url


def test_zhejiang_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["最新消息", "政策文件", "专业计划", "考试报名", "转考免考", "毕业办理"]


def test_safe_zj_url():
    assert _safe_zj_url("https://www.zjzs.net/art/2025/6/20/art_43_11321.html")
    assert _safe_zj_url("https://www.zjzs.net/col/col41/index.html")
    assert _safe_zj_url("https://example.com/a") is None


def test_parse_zj_list():
    html = """<html><body><ul>
    <li>2025-06-20 <a href="/art/2025/6/20/art_43_11321.html">2025年10月浙江省高等教育自学考试报名公告</a></li>
    <li><a href="/col/col41/index.html">政策文件</a></li>
    </ul></body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_zj_list(soup, base_url="https://www.zjzs.net/col/col43/index.html")
    assert len(rows) == 2
    assert rows[0]["publish_date"] == "2025-06-20"


def test_zhejiang_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.zjzs.net/col/col21/index.html",
            "level1": [{"name": x[0], "items": []} for x in LEVEL1_SECTIONS],
        }

    monkeypatch.setattr("app.routers.test_local.get_zhejiang_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/zhejiang/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 6

