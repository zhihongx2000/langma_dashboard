from pathlib import Path
import re

DECODE_CANDIDATES = ("utf-8", "utf-8-sig", "gb18030", "gbk", "utf-16")

NOISE_PATTERNS = (
    "==============================",
    "604课程",
)

KNOWN_NAME_FIXES = {
    "黑龙江?": "黑龙江",
    "内蒙?": "内蒙古",
}


def _decode_text(raw: bytes) -> str:
    for encoding in DECODE_CANDIDATES:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def _normalize_name(line: str) -> str:
    text = line.replace("：", ":").replace("（", "(").replace("）", ")")
    for noise in NOISE_PATTERNS:
        text = text.replace(noise, "")
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"[?？]+", "", text)
    text = re.sub(r"\s+", " ", text).strip(" -:")
    return KNOWN_NAME_FIXES.get(text, text)


def parse_seed_file(path: str) -> list[tuple[str, str]]:
    fp = Path(path)
    if not fp.exists():
        return []

    text = _decode_text(fp.read_bytes())
    items: list[tuple[str, str]] = []
    current_name = "unknown"
    seen: set[tuple[str, str]] = set()

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        if line.startswith("-"):
            url = line.lstrip("-").strip()
            if url.startswith("http"):
                pair = (current_name, url)
                if pair not in seen:
                    items.append(pair)
                    seen.add(pair)
            continue

        if "http" in line:
            match = re.search(r"https?://\S+", line)
            if match:
                url = match.group(0).rstrip(").,")
                pair = (current_name, url)
                if pair not in seen:
                    items.append(pair)
                    seen.add(pair)
            continue

        if not line.startswith("="):
            cleaned = _normalize_name(line)
            if cleaned:
                current_name = cleaned

    return items


def make_code(name: str, idx: int) -> str:
    safe = re.sub(r"[^a-zA-Z0-9]+", "-", name.lower()).strip("-")
    return safe or f"province-{idx}"
