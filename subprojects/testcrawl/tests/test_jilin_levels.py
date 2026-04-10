from fastapi.testclient import TestClient

from app.main import app
from app.services.jilin_levels import CHANNEL_PATHS, LEVEL1_SECTIONS, _extract_date_like_text, _safe_jilin_content_url


def test_jilin_section_names():
    assert LEVEL1_SECTIONS == ("通知公告", "政策法规", "常见问答")


def test_safe_jilin_content_url():
    ok = _safe_jilin_content_url("https://www.jleea.com.cn/front/content/202620")
    bad = _safe_jilin_content_url("https://www.jleea.com.cn/front/channel/9944")
    assert ok is not None
    assert bad is None


def test_channel_paths_mapping():
    assert CHANNEL_PATHS == (
        ("通知公告", "gdjyzxks_tzgg"),
        ("政策法规", "gdjyzxks_ksdt"),
        ("常见问答", "gdjyzxks_cjwd"),
    )


def test_extract_date_like_text():
    assert _extract_date_like_text("2026-04-03 09:19:46") == "2026-04-03"
    assert _extract_date_like_text("无日期") == ""


def test_jilin_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.jleea.com.cn/front/channel/9944",
            "level1": [{"name": "通知公告", "items": []}, {"name": "政策法规", "items": []}, {"name": "常见问答", "items": []}],
        }

    monkeypatch.setattr("app.routers.test_local.get_jilin_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/jilin/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 3

