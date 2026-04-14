from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.xizang_levels import LEVEL1_SPEC


def test_xizang_level1_spec_order():
    names = [n for n, _ in LEVEL1_SPEC]
    assert names == ["閫氱煡鍏憡", "鏀跨瓥娉曡", "鎷涚敓绠€绔?]


def test_xizang_parse_sample_html():
    sample = """<!DOCTYPE html><html><body>
    <div class="middle">
    <div class="title-tzgg"><a href="/92/138/index.html">a</a></div>
    <ul>
      <li><a href="/92/138/1.html">鍏憡涓€</a><span class="date">2026-01-01</span></li>
    </ul>
    <div class="title-zcfg"></div>
    <ul>
      <li><a href="/92/139/2.html">鏀跨瓥涓€</a><span class="date">2026-02-01</span></li>
    </ul>
    <div class="title-zsjz"></div>
    <ul>
      <li><a href="/92/140/3.html">绠€绔犱竴</a><span class="date">2026-03-01</span></li>
    </ul>
    </div>
    </body></html>"""
    soup = BeautifulSoup(sample, "lxml")
    level1 = []
    base = "http://zsks.edu.xizang.gov.cn/92/index.html"
    for display_name, selector in LEVEL1_SPEC:
        marker = soup.select_one(selector)
        ul = marker.find_next_sibling("ul") if marker else None
        if not ul:
            level1.append({"name": display_name, "items": []})
            continue
        from app.services.xizang_levels import _collect_list_links

        items = _collect_list_links(ul, base_url=base)
        level1.append({"name": display_name, "items": items})

    assert level1[0]["name"] == "閫氱煡鍏憡"
    assert level1[0]["items"][0]["title"] == "鍏憡涓€"
    assert level1[0]["items"][0]["url"].endswith("/92/138/1.html")
    assert level1[1]["items"][0]["title"] == "鏀跨瓥涓€"
    assert level1[2]["items"][0]["title"] == "绠€绔犱竴"


def test_xizang_levels_endpoint(monkeypatch):
    def fake_levels():
        return {
            "source_url": "http://zsks.edu.xizang.gov.cn/92/index.html",
            "level1": [
                {"name": "閫氱煡鍏憡", "items": [{"title": "t", "url": "http://zsks.edu.xizang.gov.cn/x.html", "publish_date": ""}]},
                {"name": "鏀跨瓥娉曡", "items": []},
                {"name": "鎷涚敓绠€绔?, "items": []},
            ],
        }

    monkeypatch.setattr("app.routers.crawler_ui.get_xizang_levels", fake_levels)

    with TestClient(app) as client:
        r = client.get("/api/test/xizang/levels")

    assert r.status_code == 200
    payload = r.json()
    assert len(payload["level1"]) == 3
    assert payload["level1"][0]["name"] == "閫氱煡鍏憡"


def test_get_level3_accepts_xizang_netloc(monkeypatch):
    """姝ｆ枃鎶撳彇鏍￠獙搴斿厑璁歌タ钘忕瓑鐪佸煙鍚嶏紙涓庡洓宸濆垪琛ㄥ唴 sceea 闄愬埗鍒嗙锛夈€?""
    from app.services.fetcher import FetchResult
    from app.services.sichuan_levels import get_level3_content

    monkeypatch.setattr(
        "app.services.sichuan_levels.fetch_html",
        lambda url, timeout_sec=25, prefer_browser=False: FetchResult(
            url=url,
            html="<html><head><title>娴?/title></head><body><p>姝ｆ枃</p></body></html>",
            source="mock",
        ),
    )
    monkeypatch.setattr("app.services.sichuan_levels.normalize_html", lambda h: h)
    monkeypatch.setattr("app.services.sichuan_levels.extract_main_text", lambda html, url=None: "姝ｆ枃")

    out = get_level3_content("http://zsks.edu.xizang.gov.cn/92/138/1.html")
    assert out["ok"] is True
    assert "zsks.edu.xizang.gov.cn" in out["url"]

