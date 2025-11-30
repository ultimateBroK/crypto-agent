"""Natural language helpers for parsing user intent."""
from __future__ import annotations

import re
from typing import Iterable, Optional, Tuple, Union

from tools.utils.constants import VALID_TIMEFRAMES

# Precompiled regex to capture tokens like "4h", "15 minute", "1-day", etc.
_TIMEFRAME_PATTERN = re.compile(
    r"(?P<num>\d{1,2})\s*(?:-|\s)?\s*(?P<unit>mins?|minutes?|m|hrs?|hours?|h|days?|d|weeks?|w|months?|mos?|mo)"
)

# Keyword aliases that do not necessarily include an explicit number.
_KEYWORD_TIMEFRAMES = {
    "intraday": "1h",
    "hourly": "1h",
    "daily": "1d",
    "weekly": "1w",
    "monthly": "1M",
}

# Preference order when scanning dictionaries for textual context.
_TEXT_KEYS_IN_PRIORITY = (
    "prompt",
    "query",
    "question",
    "request",
    "instruction",
    "user_input",
    "message",
    "text",
    "context",
)

# Map of unit variants to canonical CCXT suffixes.
_UNIT_TO_SUFFIX = {
    "m": "m",
    "min": "m",
    "mins": "m",
    "minute": "m",
    "minutes": "m",
    "h": "h",
    "hr": "h",
    "hrs": "h",
    "hour": "h",
    "hours": "h",
    "d": "d",
    "day": "d",
    "days": "d",
    "w": "w",
    "week": "w",
    "weeks": "w",
    "mo": "M",
    "mos": "M",
    "month": "M",
    "months": "M",
}


def _iter_text_fragments(value) -> Iterable[str]:
    """Yield all string fragments from arbitrarily nested structures."""
    if value is None:
        return
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _iter_text_fragments(item)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _iter_text_fragments(item)


def _extract_timeframe_from_text(text: Optional[str]) -> Optional[str]:
    """Return normalized timeframe if any known token exists within text."""
    if not text:
        return None
    lower_text = text.lower()

    # Direct match against valid timeframe tokens like "4h" or "1d".
    for tf in sorted(VALID_TIMEFRAMES, key=len, reverse=True):
        if tf in lower_text:
            return tf

    # Keyword-based matches (e.g., "daily", "weekly").
    for keyword, tf in _KEYWORD_TIMEFRAMES.items():
        if keyword in lower_text:
            return tf

    # Regex-based "<number><unit>" matches.
    match = _TIMEFRAME_PATTERN.search(lower_text)
    if match:
        unit = match.group("unit") or ""
        suffix = _UNIT_TO_SUFFIX.get(unit.lower())
        if suffix:
            number = int(match.group("num"))
            candidate = f"{number}{suffix}"
            if candidate in VALID_TIMEFRAMES:
                return candidate

    return None


def resolve_timeframe(
    explicit: Optional[str] = None,
    *,
    default: str = "1h",
    return_reason: bool = False,
    **kwargs,
) -> Union[str, Tuple[str, Optional[str]]]:
    """Resolve timeframe from explicit arg or natural-language context."""
    reason: Optional[str] = None
    fallback = default if default in VALID_TIMEFRAMES else "1h"

    # 1) Respect explicit argument if it maps to a valid timeframe token.
    explicit_tf = _extract_timeframe_from_text(explicit)
    if explicit_tf:
        return (explicit_tf, None) if return_reason else explicit_tf
    if explicit:
        reason = f"Timeframe '{explicit}' is not supported. Falling back to {fallback}."

    # 2) Look for timeframe hints in prioritized kwargs keys.
    for key in _TEXT_KEYS_IN_PRIORITY:
        value = kwargs.get(key)
        for fragment in _iter_text_fragments(value):
            tf = _extract_timeframe_from_text(fragment)
            if tf:
                note = f"Detected timeframe '{tf}' from {key}."
                return (tf, note) if return_reason else tf

    # 3) Scan any remaining textual kwargs for hints.
    for key, value in kwargs.items():
        if key in _TEXT_KEYS_IN_PRIORITY:
            continue
        for fragment in _iter_text_fragments(value):
            tf = _extract_timeframe_from_text(fragment)
            if tf:
                note = f"Detected timeframe '{tf}' from request context."
                return (tf, note) if return_reason else tf

    # 4) Fall back to default timeframe.
    return (fallback, reason) if return_reason else fallback