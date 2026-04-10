from fastapi.testclient import TestClient

from app.main import app
from app.services.hunan_levels import SECTION_NAMES, _extract_date_like, _url_from_onclick


def test_hunan_section_names():
    assert SECTION_NAMES == (
        "2026年考试日程",
        "最新消息",
        "通知公告",
        "自考政策",
        "开考课程计划",
        "考试大纲",
        "考试计划",
    )


def test_hunan_onclick_url_parse():
    onclick = "window.location.href='/student_anon/noticeDetail?id=abc123'"
    url = _url_from_onclick(onclick, base_url="https://nzkks.hneao.cn/student_anon/home")
    assert url.endswith("/student_anon/noticeDetail?id=abc123")


def test_hunan_date_extract():
    assert _extract_date_like("2026年4月3日") == "2026-04-03"
    assert _extract_date_like("2026-01-23") == "2026-01-23"
    assert _extract_date_like("2026.01") == "2026-01-01"


def test_hunan_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://nzkks.hneao.cn/student_anon/home",
            "level1": [{"name": x, "items": []} for x in SECTION_NAMES],
        }

    monkeypatch.setattr("app.routers.test_local.get_hunan_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/hunan/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 7

