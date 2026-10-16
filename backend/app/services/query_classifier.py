import re
from typing import Optional, Tuple

# Keywords and phrases indicative of real-time or volatile information
VOLATILE_KEYWORDS = [
    r"\bweather\b",
    r"\btemperature\b",
    r"\bforecast\b",
    r"\bstock\s*price\b",
    r"\bcrypto\b",
    r"\bbitcoin\b",
    r"\bethereum\b",
    r"\bbtc\b",
    r"\bbreaking\s*news\b",
    r"\blatest\s*news\b",
    r"\bcurrency\s*rate\b",
    r"\bexchange\s*rate\b",
    r"\btoday\b",
    r"\btonight\b",
    r"\bright\s*now\b",
    r"\bcurrent\s*time\b",
    r"\blive\s*score\b",
    r"\bscore\s*update\b",
]

COMPILED_PATTERNS = [re.compile(pattern, re.IGNORECASE) for pattern in VOLATILE_KEYWORDS]


def is_volatile_query(prompt: str) -> tuple[bool, str | None]:
    """
    Analyzes whether a query requests live, real-time, or continuously mutating data.
    If so, returns True along with the matched keyword or pattern.
    """
    cleaned = prompt.strip()
    for pattern in COMPILED_PATTERNS:
        match = pattern.search(cleaned)
        if match:
            return True, f"Matched real-time pattern: '{match.group(0)}'"
    return False, None
