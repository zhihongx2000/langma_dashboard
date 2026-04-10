from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.guangdong2_levels import (
    LEVEL1_SECTIONS,
    _parse_notice_list,
    _rows_from_notice_payload,
    _safe_gd2_detail_url,
    _type_from_url,
)


def test_guangdong2_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["专业计划", "助学管理", "考务管理", "考籍管理", "其他公告"]


def test_safe_gd2_detail_url():
    assert _safe_gd2_detail_url("https://www.eeagd.edu.cn/selfec/notice-detail.html?ggxh=231")
    assert _safe_gd2_detail_url("https://eea.gd.gov.cn/x") is None
    assert _safe_gd2_detail_url("https://www.eeagd.edu.cn/selfec/main.html") is None


def test_parse_notice_list():
    html = """<html><body>
    <ul class="news-list">
      <li class="news-item">
        <a href="notice-detail.html?ggxh=227">
          <span>2026年专业调整相关文件及资料</span>
          <span class="news-date">2025-11-25</span>
        </a>
      </li>
    </ul>
    </body></html>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_notice_list(soup, base_url="https://www.eeagd.edu.cn/selfec/notice-list.html?type=zyjh")
    assert len(rows) == 1
    assert rows[0]["publish_date"] == "2025-11-25"
    assert "ggxh=227" in rows[0]["url"]


def test_rows_from_notice_payload():
    payload = {
        "data": {
            "notices": [
                {"ggxh": 231, "bt": "关于公布2026年4、10月广东省高等教育自学考试开考课程考试时间安排和使用教材的通知", "gxsj": "2025-12-23"}
            ]
        },
        "success": True,
    }
    rows = _rows_from_notice_payload(payload)
    assert len(rows) == 1
    assert rows[0]["url"].endswith("ggxh=231")
    assert rows[0]["publish_date"] == "2025-12-23"


def test_type_from_url():
    assert _type_from_url("https://www.eeagd.edu.cn/selfec/notice-list.html?type=kwgl") == "kwgl"


def test_guangdong2_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.eeagd.edu.cn/selfec/",
            "level1": [{"name": n, "items": []} for n, _ in LEVEL1_SECTIONS],
        }

    monkeypatch.setattr("app.routers.test_local.get_guangdong2_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/guangdong2/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 5
