"""一次性探测 101.md 涉及站点的导航链接（仅开发用，可删）。"""
from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from app.services.fetcher import fetch_html

TARGETS = [
    ("gs2", "https://kw.ganseea.cn/public-info/"),
    ("hn", "http://ea.hainan.gov.cn/ywdt/zxks/"),
    ("qh", "https://www.qhjyks.com/zyym/ztzl/zxksz/index.htm"),
    ("hn1", "http://www.haeea.cn/zixuekaoshi/"),
    ("hn2", "http://zkwb.haeea.cn/ZKService/default.aspx"),
    ("jl", "https://www.jleea.com.cn/front/channel/9944"),
    ("nx", "https://www.nxjyks.cn/contents/ZXKS/"),
    ("yn", "https://www.ynzs.cn/html/web/zkdt-zxks/index.html"),
    ("bj", "https://www.bjeea.cn/html/selfstudy/index.html"),
    ("zj", "https://www.zjzs.net/col/col21/index.html"),
    ("tj", "http://www.zhaokao.net/zxks/zyts/index.shtml"),
    ("hb", "http://zk.hebeea.edu.cn/HebzkWeb/index"),
]


def main() -> None:
    for key, u in TARGETS:
        try:
            r = fetch_html(u, timeout_sec=35, prefer_browser=False)
            soup = BeautifulSoup(r.html, "lxml")
            title = (soup.title.get_text(strip=True) if soup.title else "")[:60]
            print(f"\n=== {key} -> {r.url} | {title}")
            # collect short link texts with href
            seen: set[tuple[str, str]] = set()
            for a in soup.find_all("a", href=True):
                t = re.sub(r"\s+", " ", a.get_text(strip=True))
                if not t or len(t) > 30:
                    continue
                href = a["href"].strip()
                if href.startswith("#") or "javascript" in href.lower():
                    continue
                full = urljoin(r.url, href)
                if len(full) > 120:
                    continue
                pair = (t, full[:110])
                if pair in seen:
                    continue
                seen.add(pair)
                # filter interesting
                if any(
                    k in t
                    for k in (
                        "首页",
                        "开考",
                        "报名",
                        "政策",
                        "通知",
                        "法规",
                        "考试",
                        "成绩",
                        "自学",
                        "时间",
                        "专业",
                        "大纲",
                        "顶替",
                        "专接本",
                        "二年级",
                        "查询",
                        "必修",
                        "必备",
                        "快速",
                        "指南",
                        "信息",
                        "咨询",
                        "毕业",
                        "转考",
                        "免考",
                        "常见",
                    )
                ):
                    print(f"  {t!r} -> {full[:100]}")
        except Exception as e:
            print(f"\n=== {key} FAIL {u} {e}")


if __name__ == "__main__":
    main()
