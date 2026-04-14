from fastapi.testclient import TestClient

from app.main import app
from app.services.hunan_levels import SECTION_NAMES, _extract_date_like, _url_from_onclick


def test_hunan_section_names():
    assert SECTION_NAMES == (
        "2026骞磋€冭瘯鏃ョ▼",
        "鏈€鏂版秷鎭?,
        "閫氱煡鍏憡",
        "鑷€冩斂绛?,
        "寮€鑰冭绋嬭鍒?,
        "鑰冭瘯澶х翰",
        "鑰冭瘯璁″垝",
    )


def test_hunan_onclick_url_parse():
    onclick = "window.location.href='/student_anon/noticeDetail?id=abc123'"
    url = _url_from_onclick(onclick, base_url="https://nzkks.hneao.cn/student_anon/home")
    assert url.endswith("/student_anon/noticeDetail?id=abc123")


def test_hunan_date_extract():
    assert _extract_date_like("2026骞?鏈?鏃?) == "2026-04-03"
    assert _extract_date_like("2026-01-23") == "2026-01-23"
    assert _extract_date_like("2026.01") == "2026-01-01"


def test_hunan_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://nzkks.hneao.cn/student_anon/home",
            "level1": [{"name": x, "items": []} for x in SECTION_NAMES],
        }

    monkeypatch.setattr("app.routers.crawler_ui.get_hunan_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/hunan/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 7


