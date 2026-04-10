from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.hebei_levels import LEVEL1_SECTIONS, _parse_notice_block, _safe_hebei_url


def test_hebei_section_names():
    assert LEVEL1_SECTIONS == ("最新通知公告", "查询中心", "考生必读")


def test_safe_hebei_url():
    assert _safe_hebei_url("https://zk.hebeea.edu.cn/HebzkWeb/content?id=abc")
    assert _safe_hebei_url("https://www.hebeea.edu.cn/c/2026-04-02/492219.html")
    assert _safe_hebei_url("https://example.com/a") is None


def test_parse_notice_block():
    html = """<div class="tongzhi_list_box">
      <div class="tongzhi_nr"><a href="/HebzkWeb/content?id=d29c8354-c485-4cab-a86a-157677340ac5" title="2026年上半年河北省高等教育自学考试考前提示（一）">2026年上半年河北省高等教育自学考试考前提示（一）</a></div>
      <div class="tongzhi_fabushijian">2026-04-07</div>
    </div>"""
    soup = BeautifulSoup(html, "lxml")
    rows = _parse_notice_block(soup)
    assert len(rows) == 1
    assert rows[0]["publish_date"] == "2026-04-07"


def test_hebei_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://zk.hebeea.edu.cn/HebzkWeb/index",
            "level1": [{"name": x, "items": []} for x in LEVEL1_SECTIONS],
        }

    monkeypatch.setattr("app.routers.test_local.get_hebei_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/hebei/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 3

