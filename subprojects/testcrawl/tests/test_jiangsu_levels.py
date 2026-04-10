from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.jiangsu_levels import LEVEL1_SECTIONS


def test_jiangsu_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == [
        "招考信息",
        "政策文件",
        "自考发展概况",
        "考试计划-专业建设",
        "考试计划-考试日程",
        "考试计划-考试大纲",
        "考试计划-计划简编",
        "考试信息-报名",
        "考试信息-考试",
        "考试信息-成绩",
        "考籍管理-实践论文",
        "考籍管理-本科资审",
        "考籍管理-毕业办理",
        "考籍管理-转考免考",
        "考籍管理-学士学位",
    ]
    assert len(names) == 15


def test_parse_jiangsu_news_list():
    from app.services.jiangsu_levels import _parse_news_list

    html = """<html><body><ul class="news-list">
      <li><a class="content-list-ul-a" href="//www.jseea.cn/content/redirect.do?id=1" target="_blank">测试标题 <span>2026-01-01</span></a></li>
    </ul></body></html>"""
    soup = BeautifulSoup(html, "lxml")
    items = _parse_news_list(soup, base_url="https://www.jseea.cn/webfile/selflearning/selflearning_infomation/")
    assert len(items) == 1
    assert items[0]["title"] == "测试标题"
    assert items[0]["publish_date"] == "2026-01-01"
    assert items[0]["url"].startswith("https://www.jseea.cn/content/")


def test_jiangsu_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.jseea.cn/webfile/examination/selflearning/",
            "level1": [{"name": "招考信息", "items": []}],
        }

    monkeypatch.setattr("app.routers.test_local.get_jiangsu_levels", fake)

    with TestClient(app) as client:
        r = client.get("/api/test/jiangsu/levels")

    assert r.status_code == 200
    assert r.json()["level1"][0]["name"] == "招考信息"
