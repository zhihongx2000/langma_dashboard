from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.jiangxi_levels import LEVEL1_SECTIONS, _parse_jiangxi_list, _safe_jiangxi_content_url


def test_jiangxi_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["考试动态", "通知公告", "常见问答"]


def test_safe_jiangxi_content_url():
    assert _safe_jiangxi_content_url("http://www.jxeea.cn/jxsjyksy/ksdt73/content/content_123.html")
    assert _safe_jiangxi_content_url("http://www.jxeea.cn/jxsjyksy/tzgg11/content/content_456.html")
    assert _safe_jiangxi_content_url("http://www.jxeea.cn/jxsjyksy/cjwd10/content/content_789.html")
    assert _safe_jiangxi_content_url("http://www.jxeea.cn/jxsjyksy/ksdt73/list.html") is None


def test_parse_jiangxi_list():
    html = """<html><body><ul>
    <li><a href="/jxsjyksy/ksdt73/content/content_2016434039371599872.html">江西省2025年下半年自学考试毕业审核工作顺利结束</a><span>2026-01-28</span></li>
    <li><a href="/jxsjyksy/ksdt73/list.html">考试动态</a></li>
    </ul></body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_jiangxi_list(soup, base_url="http://www.jxeea.cn/jxsjyksy/ksdt73/list.html")
    assert len(rows) == 1
    assert rows[0]["publish_date"] == "2026-01-28"


def test_parse_jiangxi_list_from_script_data():
    html = """<html><body>
    <script>
    var listData = {
      articleList: [{"title":"江西省2025年下半年自学考试毕业审核工作顺利结束","pubDate":"2026-01-28 16:50","urls":"{\\"pc\\":\\"/jxsjyksy/ksdt73/content/content_2016434039371599872.html\\"}"}],
      columnPageData: []
    }
    </script>
    </body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_jiangxi_list(soup, base_url="http://www.jxeea.cn/jxsjyksy/ksdt73/list.html")
    assert len(rows) == 1
    assert rows[0]["url"].endswith("/jxsjyksy/ksdt73/content/content_2016434039371599872.html")
    assert rows[0]["publish_date"] == "2026-01-28"


def test_jiangxi_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "http://www.jxeea.cn/jxsjyksy/zxks55/list.html",
            "level1": [
                {"name": "考试动态", "items": []},
                {"name": "通知公告", "items": []},
                {"name": "常见问答", "items": []},
            ],
        }

    monkeypatch.setattr("app.routers.test_local.get_jiangxi_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/jiangxi/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 3

