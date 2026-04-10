from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from app.main import app
from app.services.xizang_levels import LEVEL1_SPEC


def test_xizang_level1_spec_order():
    names = [n for n, _ in LEVEL1_SPEC]
    assert names == ["通知公告", "政策法规", "招生简章"]


def test_xizang_parse_sample_html():
    sample = """<!DOCTYPE html><html><body>
    <div class="middle">
    <div class="title-tzgg"><a href="/92/138/index.html">a</a></div>
    <ul>
      <li><a href="/92/138/1.html">公告一</a><span class="date">2026-01-01</span></li>
    </ul>
    <div class="title-zcfg"></div>
    <ul>
      <li><a href="/92/139/2.html">政策一</a><span class="date">2026-02-01</span></li>
    </ul>
    <div class="title-zsjz"></div>
    <ul>
      <li><a href="/92/140/3.html">简章一</a><span class="date">2026-03-01</span></li>
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

    assert level1[0]["name"] == "通知公告"
    assert level1[0]["items"][0]["title"] == "公告一"
    assert level1[0]["items"][0]["url"].endswith("/92/138/1.html")
    assert level1[1]["items"][0]["title"] == "政策一"
    assert level1[2]["items"][0]["title"] == "简章一"


def test_xizang_levels_endpoint(monkeypatch):
    def fake_levels():
        return {
            "source_url": "http://zsks.edu.xizang.gov.cn/92/index.html",
            "level1": [
                {"name": "通知公告", "items": [{"title": "t", "url": "http://zsks.edu.xizang.gov.cn/x.html", "publish_date": ""}]},
                {"name": "政策法规", "items": []},
                {"name": "招生简章", "items": []},
            ],
        }

    monkeypatch.setattr("app.routers.test_local.get_xizang_levels", fake_levels)

    with TestClient(app) as client:
        r = client.get("/api/test/xizang/levels")

    assert r.status_code == 200
    payload = r.json()
    assert len(payload["level1"]) == 3
    assert payload["level1"][0]["name"] == "通知公告"


def test_get_level3_accepts_xizang_netloc(monkeypatch):
    """正文抓取校验应允许西藏等省域名（与四川列表内 sceea 限制分离）。"""
    from app.services.fetcher import FetchResult
    from app.services.sichuan_levels import get_level3_content

    monkeypatch.setattr(
        "app.services.sichuan_levels.fetch_html",
        lambda url, timeout_sec=25, prefer_browser=False: FetchResult(
            url=url,
            html="<html><head><title>测</title></head><body><p>正文</p></body></html>",
            source="mock",
        ),
    )
    monkeypatch.setattr("app.services.sichuan_levels.normalize_html", lambda h: h)
    monkeypatch.setattr("app.services.sichuan_levels.extract_main_text", lambda html, url=None: "正文")

    out = get_level3_content("http://zsks.edu.xizang.gov.cn/92/138/1.html")
    assert out["ok"] is True
    assert "zsks.edu.xizang.gov.cn" in out["url"]
