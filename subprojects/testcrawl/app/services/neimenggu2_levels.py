"""
内蒙古（门户2）— zkxxggl 主考学校公告入口：固定一级「自考公告」「政策规定」「主考学校公告栏」。

列表解析规则与 neimenggu1 相同（nm.zsks.cn /kszs/zxks/ 下文稿链接）。
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from app.services.neimenggu1_levels import _fetch_nm_html, _parse_neimenggu1_list

NEIMENGGU2_ENTRY = "https://www.nm.zsks.cn/kszs/zxks/zkxxggl/"

LEVEL1_SECTIONS: tuple[tuple[str, str], ...] = (
    ("自考公告", "https://www.nm.zsks.cn/kszs/zxks/ggl/"),
    ("政策规定", "https://www.nm.zsks.cn/kszs/zxks/zcfg/"),
    ("主考学校公告栏", NEIMENGGU2_ENTRY),
)


def get_neimenggu2_levels() -> dict:
    level1: list[dict] = []
    for display_name, page_url in LEVEL1_SECTIONS:
        try:
            final_url, html = _fetch_nm_html(page_url, timeout_sec=25)
            soup = BeautifulSoup(html, "lxml")
            items = _parse_neimenggu1_list(soup, base_url=final_url)
        except Exception:
            items = _stub_items(
                f"「{display_name}」栏目当前访问失败（SSL/网络限制），请稍后重试或直接访问官网。"
            )
            level1.append({"name": display_name, "items": items})
            continue
        if not items:
            items = _stub_items(f"当前未解析到内蒙古自学考试「{display_name}」列表。")
        level1.append({"name": display_name, "items": items})
    return {"source_url": NEIMENGGU2_ENTRY, "level1": level1}


def _stub_items(message: str) -> list[dict]:
    return [{"title": message, "url": NEIMENGGU2_ENTRY, "publish_date": ""}]
