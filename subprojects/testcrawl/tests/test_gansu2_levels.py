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
    assert names[0] == "棣栭〉"
    assert "寮€鑰冧笓涓氭煡璇? in names
    assert "浜屽勾绾у紑鑰冭绋? in names
    assert "鏂版棫涓撲笟璇剧▼椤舵浛鍏崇郴琛紙绀句細鍨嬶級" in names


def test_section_url_hash():
    assert _section_url("/kkzy") == f"{GANSU2_ENTRY}#/kkzy"


def test_is_table_header_row():
    assert _is_table_header_row("涓撲笟鍚嶇О 2026-04-11 涓婂崍銆?9:00-11:30銆?2026-04-11 涓嬪崍")
    assert not _is_table_header_row("510201 璁＄畻鏈哄簲鐢ㄦ妧鏈紙涓撶锛?)


def test_gansu2_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": GANSU2_ENTRY,
            "level1": [{"name": n, "items": []} for n, _, _, _ in GANSU2_SECTIONS],
        }

    monkeypatch.setattr("app.routers.crawler_ui.get_gansu2_levels", fake)

    with TestClient(app) as client:
        r = client.get("/api/test/gansu2/levels")

    assert r.status_code == 200
    assert len(r.json()["level1"]) == len(GANSU2_SECTIONS)

