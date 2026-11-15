import re

# Normalize to uppercase alphanumeric (Kenya-style plates often like KAA 123A)
_PLATE_CLEAN = re.compile(r"[^A-Z0-9]")


def normalize_plate(raw: str) -> str:
    cleaned = _PLATE_CLEAN.sub("", raw.upper().strip())
    return cleaned


def format_plate_display(normalized: str) -> str:
    """Best-effort display formatting for common Kenyan patterns."""
    if len(normalized) >= 7 and normalized[0] == "K" and normalized[1].isalpha():
        # e.g. KAA123A -> KAA 123A
        letters = ""
        i = 1
        while i < len(normalized) and normalized[i].isalpha() and len(letters) < 3:
            letters += normalized[i]
            i += 1
        rest = normalized[i:]
        if letters and rest:
            return f"K{letters} {rest}"
    return normalized
