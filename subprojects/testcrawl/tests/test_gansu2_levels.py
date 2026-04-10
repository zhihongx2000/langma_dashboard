from fastapi.testclient import TestClient

from app.main import app
from app.services.gansu2_levels import (
    GANSU2_ENTRY,
    GANSU2_SECTIONS,
    _is_table_header_row,
    _section_url,
)


def test_gansu2_section_names_order():
    names = [t[0] for t in GANSU2_SECTIONS]
    assert names[0] == "首页"
    assert "开考专业查询" in names
    assert "二年级开考课程" in names
    assert "新旧专业课程顶替关系表（社会型）" in names


def test_section_url_hash():
    assert _section_url("/kkzy") == f"{GANSU2_ENTRY}#/kkzy"


def test_is_table_header_row():
    assert _is_table_header_row("专业名称 2026-04-11 上午【09:00-11:30】 2026-04-11 下午")
    assert not _is_table_header_row("510201 计算机应用技术（专科）")


def test_gansu2_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": GANSU2_ENTRY,
            "level1": [{"name": n, "items": []} for n, _, _, _ in GANSU2_SECTIONS],
        }

    monkeypatch.setattr("app.routers.test_local.get_gansu2_levels", fake)

    with TestClient(app) as client:
        r = client.get("/api/test/gansu2/levels")

    assert r.status_code == 200
    assert len(r.json()["level1"]) == len(GANSU2_SECTIONS)
