"""Persistent session stats: focus sessions and breaks completed per day.

Stored as JSON so it survives restarts and supports day/week/month rollups.
"""

import json
from datetime import date, timedelta
from pathlib import Path

DEFAULT_PATH = Path.home() / ".pomodoro_stats.json"

FOCUS = "focus"
BREAK = "break"


def _iso(day=None) -> str:
    if day is None:
        day = date.today()
    return day.isoformat() if isinstance(day, date) else str(day)


def _parse(day: str) -> date:
    return date.fromisoformat(day)


def _num(value) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def _read(path) -> dict:
    path = Path(path)
    try:
        with open(path) as fh:
            data = json.load(fh)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    if not isinstance(data, dict):
        return {}
    days = data.get("days")
    if isinstance(days, dict):
        return days
    # Migrate the legacy {"date": ..., "count": ...} shape written by v1.
    if "date" in data:
        return {str(data["date"]): {FOCUS: _num(data.get("count")), BREAK: 0}}
    return {}


def _write(path, days) -> None:
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as fh:
            json.dump({"days": days}, fh)
    except OSError:
        pass


def _entry(days: dict, key: str) -> dict:
    entry = days.get(key)
    return entry if isinstance(entry, dict) else {}


def record(path=DEFAULT_PATH, kind=FOCUS, day=None) -> int:
    """Increment and persist one `kind` for `day`; return the new total."""
    key = _iso(day)
    days = _read(path)
    entry = _entry(days, key)
    entry[kind] = _num(entry.get(kind)) + 1
    days[key] = entry
    _write(path, days)
    return entry[kind]


def count(path=DEFAULT_PATH, kind=FOCUS, day=None) -> int:
    """Total for a single `day` (default today) and `kind`."""
    return _num(_entry(_read(path), _iso(day)).get(kind))


def _aggregate(days: dict, start=None, end=None) -> dict:
    out = {FOCUS: 0, BREAK: 0}
    for key, entry in days.items():
        if not isinstance(entry, dict):
            continue
        try:
            d = _parse(key)
        except (ValueError, TypeError):
            continue
        if start is not None and d < start:
            continue
        if end is not None and d > end:
            continue
        out[FOCUS] += _num(entry.get(FOCUS))
        out[BREAK] += _num(entry.get(BREAK))
    return out


def totals(path=DEFAULT_PATH, start=None, end=None) -> dict:
    """Sum focus/break counts over an inclusive date range."""
    return _aggregate(_read(path), start, end)


def daily(path=DEFAULT_PATH, start=None, end=None) -> list[tuple[str, dict]]:
    """Per-day totals within the inclusive range, oldest first."""
    days = _read(path)
    rows = []
    for key in sorted(days):
        try:
            d = _parse(key)
        except (ValueError, TypeError):
            continue
        if start is not None and d < start:
            continue
        if end is not None and d > end:
            continue
        rows.append((key, _aggregate(days, start=d, end=d)))
    return rows


def summary(path=DEFAULT_PATH, today=None) -> dict:
    """Calendar day/week/month totals up to and including `today`."""
    if today is None:
        today = date.today()
    elif not isinstance(today, date):
        today = _parse(str(today))
    return {
        "day": totals(path, start=today, end=today),
        "week": totals(path, start=today - timedelta(days=today.weekday()), end=today),
        "month": totals(path, start=today.replace(day=1), end=today),
    }
