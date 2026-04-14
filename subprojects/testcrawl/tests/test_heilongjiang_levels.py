from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.heilongjiang_levels import CHANNEL_NAME, LEVEL2_SECTIONS


def test_heilongjiang_section_names():
    names = [n for n, _ in LEVEL2_SECTIONS]
    assert names[0] == "鏈€鏂颁俊鎭?
    assert names[-1] == "璁″垝鏁欐潗"
    assert len(names) == 10


def test_parse_hlj_list_table():
    from app.services.heilongjiang_levels import _parse_list_table

    html = """<html><body><table><tbody>
      <tr>
        <td><img src="/x.gif"/><a href="./202601/t1.htm" target="_blank">娴嬭瘯閫氱煡</a></td>
        <td>2026-01-01</td>
      </tr>
    </tbody></table></body></html>"""
    soup = BeautifulSoup(html, "lxml")
    items = _parse_list_table(soup, base_url="https://www.lzk.hl.cn/zk/zkxx/")
    assert len(items) == 1
    assert items[0]["title"] == "娴嬭瘯閫氱煡"
    assert items[0]["publish_date"] == "2026-01-01"
    assert items[0]["url"].endswith("/zk/zkxx/202601/t1.htm")


def test_heilongjiang_levels_endpoint(monkeypatch):
    def fake():
        return {
            "source_url": "https://www.lzk.hl.cn/zk/zxxx_149/",
            "channel_name": CHANNEL_NAME,
            "level1": [{"name": "鏈€鏂颁俊鎭?, "items": []}],
        }

    monkeypatch.setattr("app.routers.crawler_ui.get_heilongjiang_levels", fake)

    with TestClient(app) as client:
        r = client.get("/api/test/heilongjiang/levels")

    assert r.status_code == 200
    assert r.json().get("channel_name") == CHANNEL_NAME

