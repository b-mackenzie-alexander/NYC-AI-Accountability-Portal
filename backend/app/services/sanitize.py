import re


def sanitize_text(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value).strip()
