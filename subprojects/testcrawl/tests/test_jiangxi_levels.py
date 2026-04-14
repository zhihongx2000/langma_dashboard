from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.jiangxi_levels import LEVEL1_SECTIONS, _parse_jiangxi_list, _safe_jiangxi_content_url


def test_jiangxi_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["鑰冭瘯鍔ㄦ€?, "閫氱煡鍏憡", "甯歌闂瓟"]


def test_safe_jiangxi_content_url():
    assert _safe_jiangxi_content_url("http://www.jxeea.cn/jxsjyksy/ksdt73/content/content_123.html")
    assert _safe_jiangxi_content_url("http://www.jxeea.cn/jxsjyksy/tzgg11/content/content_456.html")
    assert _safe_jiangxi_content_url("http://www.jxeea.cn/jxsjyksy/cjwd10/content/content_789.html")
    assert _safe_jiangxi_content_url("http://www.jxeea.cn/jxsjyksy/ksdt73/list.html") is None


def test_parse_jiangxi_list():
    html = """<html><body><ul>
    <li><a href="/jxsjyksy/ksdt73/content/content_2016434039371599872.html">姹熻タ鐪?025骞翠笅鍗婂勾鑷鑰冭瘯姣曚笟瀹℃牳宸ヤ綔椤哄埄缁撴潫</a><span>2026-01-28</span></li>
    <li><a href="/jxsjyksy/ksdt73/list.html">鑰冭瘯鍔ㄦ€?/a></li>
    </ul></body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_jiangxi_list(soup, base_url="http://www.jxeea.cn/jxsjyksy/ksdt73/list.html")
    assert len(rows) == 1
    assert rows[0]["publish_date"] == "2026-01-28"


def test_parse_jiangxi_list_from_script_data():
    html = """<html><body>
    <script>
    var listData = {
      articleList: [{"title":"姹熻タ鐪?025骞翠笅鍗婂勾鑷鑰冭瘯姣曚笟瀹℃牳宸ヤ綔椤哄埄缁撴潫","pubDate":"2026-01-28 16:50","urls":"{\\"pc\\":\\"/jxsjyksy/ksdt73/content/content_2016434039371599872.html\\"}"}],
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
                {"name": "鑰冭瘯鍔ㄦ€?, "items": []},
                {"name": "閫氱煡鍏憡", "items": []},
                {"name": "甯歌闂瓟", "items": []},
            ],
        }

    monkeypatch.setattr("app.routers.crawler_ui.get_jiangxi_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/jiangxi/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 3


