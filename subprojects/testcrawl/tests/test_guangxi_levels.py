from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.guangxi_levels import LEVEL1_SECTIONS, _extract_date_like, _parse_guangxi_list, _safe_guangxi_article_url


def test_guangxi_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["通知公告", "招生问答", "招考日程"]


def test_safe_guangxi_article_url():
    assert _safe_guangxi_article_url("https://www.gxeea.cn/view/content_1148_32484.htm")
    assert _safe_guangxi_article_url("https://www.gxeea.cn/zxks/tzgg.htm") is None
    assert _safe_guangxi_article_url("https://example.com/view/content_1_2.htm") is None


def test_extract_date_like_guangxi():
    assert _extract_date_like("2026年3月1日发布公告") == "2026-03-01"


def test_parse_guangxi_list():
    html = """<html><body><ul>
    <li><a href="../view/content_1148_32484.htm">广西自学考试通知</a></li>
    </ul></body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_guangxi_list(soup, base_url="https://www.gxeea.cn/zxks/tzgg.htm")
    assert len(rows) == 1
    assert rows[0]["url"] == "https://www.gxeea.cn/view/content_1148_32484.htm"


def test_guangxi_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.gxeea.cn/zxks/tzgg.htm",
            "level1": [{"name": n, "items": []} for n, _ in LEVEL1_SECTIONS],
        }

    monkeypatch.setattr("app.routers.test_local.get_guangxi_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/guangxi/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 3
