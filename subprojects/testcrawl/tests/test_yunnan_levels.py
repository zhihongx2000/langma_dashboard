from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.yunnan_levels import LEVEL1_SECTIONS, _extract_date_like, _parse_yunnan_list


def test_yunnan_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["自学考试"]


def test_parse_yunnan_links():
    html = """<html><body>
    <a href="https://www.ynzs.cn/html/content/8407.html">2026年上半年云南省第95次高等教育自学考试和高校教师资格认定课程考试温馨提示</a>
    <a href="https://www.ynzs.cn/html/web/zkdt-zxks/index.html">自学考试栏目</a>
    </body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_yunnan_list(soup, base_url="https://www.ynzs.cn/html/web/zkdt-zxks/index.html")
    assert len(rows) == 1
    assert "高等教育自学考试" in rows[0]["title"]
    assert rows[0]["url"].endswith("/html/content/8407.html")


def test_extract_yunnan_date_like():
    assert _extract_date_like("2025/11/10 云南省高等教育自学考试毕业申请办证须知") == "2025-11-10"
    assert _extract_date_like("无日期") == ""


def test_yunnan_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.ynzs.cn/html/web/zkdt-zxks/index.html",
            "level1": [{"name": "自学考试", "items": []}],
        }

    monkeypatch.setattr("app.routers.test_local.get_yunnan_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/yunnan/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 1

