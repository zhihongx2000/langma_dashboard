from fastapi.testclient import TestClient

from app.main import app
from app.services.henan2_levels import LEVEL1_SECTIONS, _filter_rows_by_keywords


def test_henan2_section_names():
    assert LEVEL1_SECTIONS == ("时间安排", "政策·公告")


def test_filter_rows_by_keywords():
    rows = [
        {"title": "2026年上半年自学考试时间安排", "url": "u1", "publish_date": ""},
        {"title": "关于某项工作的公告", "url": "u2", "publish_date": ""},
        {"title": "无关标题", "url": "u3", "publish_date": ""},
    ]
    time_rows = _filter_rows_by_keywords(rows, ("时间安排",))
    policy_rows = _filter_rows_by_keywords(rows, ("公告", "政策"))
    assert len(time_rows) == 1
    assert len(policy_rows) == 1


def test_henan2_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "http://zkwb.haeea.cn/ZKService/default.aspx",
            "level1": [{"name": "时间安排", "items": []}, {"name": "政策·公告", "items": []}],
        }

    monkeypatch.setattr("app.routers.test_local.get_henan2_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/henan2/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 2

