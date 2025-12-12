"""
ICT Killzones utilities (time windows) for market context.

Default profile uses classic ICT session windows referenced in New York time:
- Asia:   20:00–00:00 NY
- London: 02:00–05:00 NY
- New York: 08:00–11:00 NY

Crypto trades 24/7; killzones are used as a *liquidity/volatility timing lens*.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import List, Optional, Tuple

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore

from tools.utils.formatters import format_timestamp


@dataclass(frozen=True)
class Killzone:
    key: str
    name: str
    start_hhmm: str
    end_hhmm: str


KILLZONE_PROFILES = {
    # Classic ICT killzones referenced in New York time.
    "ict_classic": [
        Killzone(key="asia", name="Asia Kill Zone", start_hhmm="20:00", end_hhmm="00:00"),
        Killzone(key="london", name="London Kill Zone", start_hhmm="02:00", end_hhmm="05:00"),
        Killzone(key="newyork", name="New York Kill Zone", start_hhmm="08:00", end_hhmm="11:00"),
    ]
}


def _parse_hhmm(hhmm: str) -> time:
    parts = (hhmm or "").strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid HH:MM time: {hhmm!r}")
    h = int(parts[0])
    m = int(parts[1])
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError(f"Invalid HH:MM time: {hhmm!r}")
    return time(hour=h, minute=m)


def _parse_yyyy_mm_dd(d: Optional[str], tz: ZoneInfo) -> date:
    if d is None or not str(d).strip():
        return datetime.now(tz).date()
    return datetime.strptime(d.strip(), "%Y-%m-%d").date()


def _format_dt(dt: datetime, tz: ZoneInfo) -> str:
    # Example: 2025-12-12 08:00:00 America/New_York
    return dt.astimezone(tz).strftime(f"%Y-%m-%d %H:%M:%S {tz.key}")


def _window_for_day(
    day: date,
    start_hhmm: str,
    end_hhmm: str,
    tz: ZoneInfo,
) -> Tuple[datetime, datetime]:
    start_t = _parse_hhmm(start_hhmm)
    end_t = _parse_hhmm(end_hhmm)
    start_dt = datetime.combine(day, start_t, tzinfo=tz)
    end_dt = datetime.combine(day, end_t, tzinfo=tz)
    if end_dt <= start_dt:
        end_dt = end_dt + timedelta(days=1)
    return start_dt, end_dt


def _in_window(now: datetime, start: datetime, end: datetime) -> bool:
    return start <= now < end


def _next_window(now: datetime, windows: List[Tuple[str, str, datetime, datetime]]) -> Optional[Tuple[str, str, datetime, datetime]]:
    """
    windows: list of (key, name, start_dt, end_dt) in same tz as 'now'
    """
    future = [(k, n, s, e) for (k, n, s, e) in windows if s > now]
    if future:
        return sorted(future, key=lambda x: x[2])[0]
    return None


def get_ict_killzones(
    date_yyyy_mm_dd: Optional[str] = None,
    timezone: str = "UTC",
    reference_timezone: str = "America/New_York",
    profile: str = "ict_classic",
    include_tomorrow: bool = True,
    **kwargs,
) -> str:
    """
    Show ICT Killzones for a given date, converted to a display timezone.

    Args:
        date_yyyy_mm_dd: Optional date in YYYY-MM-DD (interpreted in reference_timezone).
        timezone: Display timezone (IANA name). Default: UTC.
        reference_timezone: Where killzones are defined. Default: America/New_York.
        profile: Killzone profile key. Default: ict_classic.
        include_tomorrow: Include next-day windows (useful for Asia 20:00–00:00).
    """
    if ZoneInfo is None:
        return (
            "❌ Error: zoneinfo is not available in this Python environment.\n\n"
            "Reasoning: ICT killzones require timezone conversion. Please use Python 3.9+ "
            "or install a zoneinfo-compatible environment."
        )

    try:
        ref_tz = ZoneInfo(reference_timezone)
    except Exception as e:
        return f"❌ Error: Invalid reference_timezone '{reference_timezone}'. Details: {e}"

    try:
        out_tz = ZoneInfo(timezone)
    except Exception as e:
        return f"❌ Error: Invalid timezone '{timezone}'. Details: {e}"

    zones = KILLZONE_PROFILES.get(profile)
    if not zones:
        available = ", ".join(sorted(KILLZONE_PROFILES.keys()))
        return f"❌ Error: Unknown profile '{profile}'. Available: {available}"

    try:
        day = _parse_yyyy_mm_dd(date_yyyy_mm_dd, ref_tz)
    except Exception as e:
        return f"❌ Error: Invalid date '{date_yyyy_mm_dd}'. Expected YYYY-MM-DD. Details: {e}"

    now_ref = datetime.now(ref_tz)
    today_ref = day

    # Build windows for day (+ optionally tomorrow) in reference tz.
    days = [today_ref]
    if include_tomorrow:
        days.append(today_ref + timedelta(days=1))

    windows: List[Tuple[str, str, datetime, datetime]] = []
    for d in days:
        for kz in zones:
            start_dt, end_dt = _window_for_day(d, kz.start_hhmm, kz.end_hhmm, ref_tz)
            # Deduplicate: if we included tomorrow, don't double-add overlapping windows
            windows.append((kz.key, kz.name, start_dt, end_dt))

    # De-dupe by exact start/end/name (just in case)
    uniq = {}
    for k, n, s, e in windows:
        uniq[(n, s, e)] = (k, n, s, e)
    windows = sorted(uniq.values(), key=lambda x: x[2])

    active = [(k, n, s, e) for (k, n, s, e) in windows if _in_window(now_ref, s, e)]
    active_str = "OUTSIDE"
    if active:
        # In case of overlaps (rare), list all.
        active_names = ", ".join(n for (_, n, _, _) in active)
        active_str = f"INSIDE: {active_names}"

    nxt = _next_window(now_ref, windows)
    next_str = "None"
    if nxt:
        delta = nxt[2] - now_ref
        mins = int(delta.total_seconds() // 60)
        if mins >= 60:
            next_str = f"{nxt[1]} in {mins//60}h {mins%60}m"
        else:
            next_str = f"{nxt[1]} in {mins}m"

    header_ts = format_timestamp()
    lines: List[str] = []
    lines.append(f"🕐 {header_ts} ICT Killzones")
    lines.append(f"Reference TZ: {ref_tz.key} | Display TZ: {out_tz.key} | Profile: {profile}")
    lines.append(f"Date (reference): {today_ref.isoformat()}")
    lines.append("")
    lines.append(f"Now (reference): {_format_dt(now_ref, ref_tz)}")
    lines.append(f"Status: {active_str} | Next: {next_str}")
    lines.append("")
    lines.append("Killzones:")

    for _, name, start_ref, end_ref in windows:
        start_out = start_ref.astimezone(out_tz)
        end_out = end_ref.astimezone(out_tz)
        # Compact formatting for readability
        ref_range = f"{start_ref.strftime('%Y-%m-%d %H:%M')}–{end_ref.strftime('%Y-%m-%d %H:%M')} {ref_tz.key}"
        out_range = f"{start_out.strftime('%Y-%m-%d %H:%M')}–{end_out.strftime('%Y-%m-%d %H:%M')} {out_tz.key}"
        marker = "✅" if _in_window(now_ref, start_ref, end_ref) else "•"
        lines.append(f"{marker} {name}")
        lines.append(f"   - Ref: {ref_range}")
        lines.append(f"   - Out: {out_range}")

    lines.append("")
    lines.append("💡 Notes:")
    lines.append("- Killzones are *time windows* where liquidity + volatility often increases.")
    lines.append("- Use as a timing filter for liquidity sweeps, breakouts, and OB/FVG reactions.")
    lines.append("- For crypto (24/7), treat killzones as a probabilistic lens, not a rule.")

    return "\n".join(lines)

