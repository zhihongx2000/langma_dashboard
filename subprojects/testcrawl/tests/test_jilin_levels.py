from fastapi.testclient import TestClient

from app.main import app
from app.services.jilin_levels import CHANNEL_PATHS, LEVEL1_SECTIONS, _extract_date_like_text, _safe_jilin_content_url


def test_jilin_section_names():
    assert LEVEL1_SECTIONS == ("閫氱煡鍏憡", "鏀跨瓥娉曡", "甯歌闂瓟")


def test_safe_jilin_content_url():
    ok = _safe_jilin_content_url("https://www.jleea.com.cn/front/content/202620")
    bad = _safe_jilin_content_url("https://www.jleea.com.cn/front/channel/9944")
    assert ok is not None
    assert bad is None


def test_channel_paths_mapping():
    assert CHANNEL_PATHS == (
        ("閫氱煡鍏憡", "gdjyzxks_tzgg"),
        ("鏀跨瓥娉曡", "gdjyzxks_ksdt"),
        ("甯歌闂瓟", "gdjyzxks_cjwd"),
    )


def test_extract_date_like_text():
    assert _extract_date_like_text("2026-04-03 09:19:46") == "2026-04-03"
    assert _extract_date_like_text("鏃犳棩鏈?) == ""


def test_jilin_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.jleea.com.cn/front/channel/9944",
            "level1": [{"name": "閫氱煡鍏憡", "items": []}, {"name": "鏀跨瓥娉曡", "items": []}, {"name": "甯歌闂瓟", "items": []}],
        }

    monkeypatch.setattr("app.routers.crawler_ui.get_jilin_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/jilin/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 3


