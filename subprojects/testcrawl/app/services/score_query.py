import re
import unicodedata
from pathlib import Path
from urllib.parse import unquote, urlparse

from app.services.seed_loader import parse_seed_file


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _normalize_label(s: str) -> str:
    """等价折叠空白/全角数字等，避免库里的名称与 getcj 肉眼一致但匹配失败。"""
    t = unicodedata.normalize("NFKC", (s or "").strip())
    return " ".join(t.split())


def _province_name_variants(province_name: str) -> list[str]:
    n = _normalize_label(province_name)
    out: list[str] = []
    for cand in (n, re.sub(r"\d+$", "", n).strip()):
        if cand and cand not in out:
            out.append(cand)
    return out or [n]


def _cj_name_to_score() -> dict[str, str]:
    """getcj.txt 中同一省名出现多行时取末行（如内蒙古网报系统在后）。"""
    items = parse_seed_file(str(_project_root() / "getcj.txt"))
    out: dict[str, str] = {}
    for n, u in items:
        out[n] = u
    return out


def _norm_portal(url: str) -> tuple[str, str]:
    p = urlparse((url or "").strip())
    host = (p.netloc or "").lower()
    path = unquote((p.path or "").rstrip("/")).lower()
    return (host, path)


def _portal_score_entries(cj_map: dict[str, str]) -> list[tuple[tuple[str, str], str]]:
    """get.txt 门户 URL → getcj 成绩 URL（按省名对齐）。"""
    items = parse_seed_file(str(_project_root() / "get.txt"))
    entries: list[tuple[tuple[str, str], str]] = []
    for name, purl in items:
        su = cj_map.get(name)
        if not su:
            continue
        t = _norm_portal(purl)
        if t[0]:
            entries.append((t, su))
    return entries


def _score_by_portal(portal_url: str, cj_map: dict[str, str]) -> str | None:
    entries = _portal_score_entries(cj_map)
    key = _norm_portal(portal_url)
    h, pa = key
    if not h:
        return None
    for e, su in entries:
        if e == key:
            return su
    best: str | None = None
    best_l = -1
    for (kh, kp), su in entries:
        if kh != h or not kp or not pa:
            continue
        if pa.startswith(kp) or kp.startswith(pa):
            l = min(len(pa), len(kp))
            if l > best_l:
                best_l = l
                best = su
    return best


def get_score_query_url(province_name: str, portal_url: str | None = None) -> str | None:
    cj_map = _cj_name_to_score()
    cj_pairs = list(cj_map.items())
    variants = _province_name_variants(province_name) if province_name else []

    for vn in variants:
        for name, url in cj_map.items():
            if _normalize_label(name) == vn:
                return url

    # 关键词匹配：getcj 中的省名出现在当前省名中即可（如 新疆1、新疆2 → 新疆）
    by_len = sorted(
        (pair for pair in cj_pairs if pair[0]),
        key=lambda p: len(_normalize_label(p[0])),
        reverse=True,
    )
    for vn in variants:
        for name, url in by_len:
            cn = _normalize_label(name)
            if not cn:
                continue
            if cn in vn or vn in cn:
                return url

    if portal_url:
        hit = _score_by_portal(portal_url, cj_map)
        if hit:
            return hit
    return None
