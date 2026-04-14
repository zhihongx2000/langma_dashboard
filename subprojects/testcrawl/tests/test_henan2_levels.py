from fastapi.testclient import TestClient

from app.main import app
from app.services.henan2_levels import LEVEL1_SECTIONS, _filter_rows_by_keywords


def test_henan2_section_names():
    assert LEVEL1_SECTIONS == ("鏃堕棿瀹夋帓", "鏀跨瓥路鍏憡")


def test_filter_rows_by_keywords():
    rows = [
        {"title": "2026骞翠笂鍗婂勾鑷鑰冭瘯鏃堕棿瀹夋帓", "url": "u1", "publish_date": ""},
        {"title": "鍏充簬鏌愰」宸ヤ綔鐨勫叕鍛?, "url": "u2", "publish_date": ""},
        {"title": "鏃犲叧鏍囬", "url": "u3", "publish_date": ""},
    ]
    time_rows = _filter_rows_by_keywords(rows, ("鏃堕棿瀹夋帓",))
    policy_rows = _filter_rows_by_keywords(rows, ("鍏憡", "鏀跨瓥"))
    assert len(time_rows) == 1
    assert len(policy_rows) == 1


def test_henan2_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "http://zkwb.haeea.cn/ZKService/default.aspx",
            "level1": [{"name": "鏃堕棿瀹夋帓", "items": []}, {"name": "鏀跨瓥路鍏憡", "items": []}],
        }

    monkeypatch.setattr("app.routers.crawler_ui.get_henan2_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/henan2/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 2


