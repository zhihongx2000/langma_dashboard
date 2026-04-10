from pathlib import Path

from app.services.seed_loader import parse_seed_file


def test_parse_seed_file_supports_gb18030(tmp_path: Path):
    content = """
2026年上半年各省份查询网站汇总
==============================

四川
- https://www.sceea.cn/List/NewsList_62_1.html

安徽（604课程）
- https://www.ahzsks.cn/gdjyzxks/search2.jsp?c=77
""".strip()
    seed_file = tmp_path / "seed.txt"
    seed_file.write_bytes(content.encode("gb18030"))

    items = parse_seed_file(str(seed_file))

    assert ("四川", "https://www.sceea.cn/List/NewsList_62_1.html") in items
    assert ("安徽", "https://www.ahzsks.cn/gdjyzxks/search2.jsp?c=77") in items


def test_parse_seed_file_deduplicates_urls(tmp_path: Path):
    content = """
四川
- https://example.com/a
- https://example.com/a
""".strip()
    seed_file = tmp_path / "seed.txt"
    seed_file.write_text(content, encoding="utf-8")

    items = parse_seed_file(str(seed_file))

    assert items == [("四川", "https://example.com/a")]


def test_get_score_query_url_keyword_match(monkeypatch):
    monkeypatch.setattr(
        "app.services.score_query.parse_seed_file",
        lambda _path: [
            ("新疆", "https://cx.example.com/w"),
            ("江苏", "https://js.example.com/w"),
        ],
    )
    from app.services.score_query import get_score_query_url

    assert get_score_query_url("新疆") == "https://cx.example.com/w"
    assert get_score_query_url("新疆1") == "https://cx.example.com/w"
    assert get_score_query_url("新疆2") == "https://cx.example.com/w"
    assert get_score_query_url("新疆２") == "https://cx.example.com/w"
    assert get_score_query_url("江苏") == "https://js.example.com/w"


def test_getcj_inner_mongolia_uses_last_listed_url():
    from app.services.score_query import get_score_query_url

    u = get_score_query_url("内蒙古")
    assert u is not None
    assert "wsbmbkxt" in u


def test_get_score_query_portal_fallback_when_name_unknown():
    from app.services.score_query import get_score_query_url

    u = get_score_query_url("__not_a_province__", portal_url="https://www.nxjyks.cn/contents/ZXKS/")
    assert u == "https://baoming.nxjyks.cn:20062/login"
