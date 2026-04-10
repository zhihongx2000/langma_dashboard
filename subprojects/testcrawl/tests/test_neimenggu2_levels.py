from fastapi.testclient import TestClient

from app.main import app
from app.services.neimenggu2_levels import LEVEL1_SECTIONS, NEIMENGGU2_ENTRY


def test_neimenggu2_entry_url():
    assert "zkxxggl" in NEIMENGGU2_ENTRY


def test_neimenggu2_section_names():
    names = [n for n, _ in LEVEL1_SECTIONS]
    assert names == ["自考公告", "政策规定", "主考学校公告栏"]


def test_neimenggu2_list_urls():
    urls = [u for _, u in LEVEL1_SECTIONS]
    assert "ggl/" in urls[0]
    assert "zcfg/" in urls[1]
    assert "zkxxggl" in urls[2]


def test_neimenggu2_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": NEIMENGGU2_ENTRY,
            "level1": [{"name": n, "items": []} for n, _ in LEVEL1_SECTIONS],
        }

    monkeypatch.setattr("app.routers.test_local.get_neimenggu2_levels", fake)
    with TestClient(app) as client:
        r = client.get("/api/test/neimenggu2/levels")
    assert r.status_code == 200
    assert len(r.json()["level1"]) == 3

