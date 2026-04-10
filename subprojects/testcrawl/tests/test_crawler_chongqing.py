from app.services.crawler import _is_chongqing_zxks_section


def test_is_chongqing_zxks_section():
    assert _is_chongqing_zxks_section("https://www.cqksy.cn/web/column/col1846543.html")
    assert _is_chongqing_zxks_section("https://www.cqksy.cn/web/column/col1846543.html/")
    assert not _is_chongqing_zxks_section("https://www.cqksy.cn/web/column/colxxxx.html")
