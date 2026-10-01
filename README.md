# 🍅 Pomodoro Timer

A simple, terminal-based Pomodoro timer written in pure Python — **no external dependencies**, standard library only.

Cycles between ☕️ **Focus** (25 min) and Break (5 min) with an in-place countdown, progress bar, pause/resume, a terminal beep at each transition, and persistent daily stats.

## Requirements

- Python 3.10+ (uses `float | None` union syntax in `core.py`)

## Usage

```bash
python -m pomodoro
```

That's it. The timer runs until you quit.

| Key | Action |
|---|---|
| `Ctrl+C` (first press) | Pause the timer |
| `Ctrl+C` (second press, after pausing) | Resume |
| `Ctrl+\` | Quit |

At each phase transition you'll get a terminal beep (`\a`) and a message like:

```
🍅 Focus started!
☕️ Break started!
```

Completed focus sessions and breaks are tracked per day and shown in the timer's
footer (`🍅 N today`). The history is stored in `~/.pomodoro_stats.json`.

### Command-line options

| Flag | Description |
|---|---|
| `--stats` | Print pomodoro/break totals for today, this week and this month, then exit |
| `--stats-file PATH` | Read/write a different stats file (default: `~/.pomodoro_stats.json`) |
| `-h`, `--help` | Show help and exit |

## Stats

List how many pomodoros and breaks you've completed per day, week, and month:

```bash
python -m pomodoro --stats
```

```
🍅 Pomodoro stats — 2026-09-30

             Pomodoros  Breaks
Today                2       1
This week           12       9
This month          43      30

Daily breakdown (this month):
  2026-09-27    1 pomodoros    0 breaks
  2026-09-30    2 pomodoros    1 breaks
```

**What is counted.** A pomodoro is recorded when a **Focus** phase completes; a
break is recorded when a **Break** phase completes. Paused time and a quit
mid-phase are not counted.

**Rollup windows.** All ranges are inclusive and anchored to today:

- **Today** — today only.
- **This week** — Monday through today (weeks start on Monday).
- **This month** — the 1st of the current month through today.

**Storage.** History is a single JSON file, one entry per day:

```json
{
  "days": {
    "2026-09-27": { "focus": 1, "break": 0 },
    "2026-09-30": { "focus": 2, "break": 1 }
  }
}
```

The file is created on the first completed phase. Counts are never reset by the
clock changing — new days are simply added as new keys. Files written by the
earlier single-day format (`{"date": ..., "count": ...}`) are read transparently
and upgraded on the next write. Missing, unreadable, or corrupt files are
treated as empty.

### Stats API

`pomodoro/stats.py` is a small, IO-isolated module you can use directly:

```python
from pomodoro import stats

stats.record(stats.DEFAULT_PATH, stats.FOCUS)   # +1 focus for today, returns new total
stats.record(stats.DEFAULT_PATH, stats.BREAK)   # +1 break for today

stats.count(stats.DEFAULT_PATH, stats.FOCUS)                         # today's focus count
stats.count(stats.DEFAULT_PATH, stats.FOCUS, day="2026-09-30")       # a specific day

stats.totals(stats.DEFAULT_PATH, start=..., end=...)   # {"focus": N, "break": N}
stats.daily(stats.DEFAULT_PATH, start=..., end=...)    # [("2026-09-30", {...}), ...]
stats.summary(stats.DEFAULT_PATH)                      # {"day": {...}, "week": {...}, "month": {...}}
```

`day` accepts a `datetime.date` or an ISO `"YYYY-MM-DD"` string; `start`/`end`
accept `date` objects.

## Configuration

Edit `pomodoro/settings.py`:

```python
FOCUS_MINUTES = 25
BREAK_MINUTES = 5
```

## Project Layout

```
pomodoro/
├── __init__.py      # package marker
├── __main__.py      # entry point & --stats/--stats-file argument parsing
├── cli.py           # terminal rendering, stats report, pause/resume handling
├── core.py          # pure Timer engine (injected clock, no IO)
├── settings.py      # duration defaults
└── stats.py         # persistent per-day focus/break counts & rollups
tests/
├── test_core.py     # unit tests with a fake clock (no real waiting)
└── test_stats.py    # stats persistence & rollup tests (temp files)
```

### Design notes

`core.Timer` never sleeps or prints — you inject a clock callable so tests can advance time instantly:

```python
from pomodoro.core import Timer

clock = FakeClock()
timer = Timer(focus_seconds=1500, break_seconds=300, clock=clock)
clock.advance(1500)
assert timer.tick()  # phase just completed
```

This keeps business logic fully unit-testable without waiting on real wall-clock time. `timer.focus_completions` counts only focus phases (pomodoros), while `timer.completions` counts every phase.

`stats` keeps all file IO in one module and degrades gracefully: any missing,
corrupt, or foreign-shaped file is treated as empty rather than raising. Tests
pass a temporary path and fixed dates, so nothing touches your real
`~/.pomodoro_stats.json` or depends on the current date.

## Running Tests

```bash
python -m unittest discover -s tests -v
```

All tests should pass instantly (they use a fake clock, so nothing actually sleeps).

## Roadmap ideas

- CLI flags (`--focus`, `--break`) instead of editing `settings.py`
- Long break every N pomodoros
- Desktop notifications / sound file instead of terminal beep
