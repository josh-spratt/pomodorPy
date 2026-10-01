"""Terminal UX: in-place countdown rendering, pause hint, beep on completion."""

import sys
from datetime import date

from .core import Phase, Timer
from . import settings, stats

_BAR_WIDTH = 30


def render(timer: Timer, today_count: int = 0) -> str:
    total = timer.duration
    remaining = timer.remaining()
    minutes, seconds = divmod(remaining, 60)
    filled = round(_BAR_WIDTH * (total - remaining) / total)
    bar = "█" * filled + "░" * (_BAR_WIDTH - filled)
    state = "⏸" if timer.paused else "▶"
    return (
        f"{state} {timer.phase.value:>5} {minutes:02d}:{seconds:02d} "
        f"|{bar}| 🍅 {today_count} today"
    )


def render_stats(stats_path=stats.DEFAULT_PATH) -> str:
    today = date.today()
    summary = stats.summary(stats_path, today)
    lines = [
        f"🍅 Pomodoro stats — {today.isoformat()}",
        "",
        f"{'':<12}{'Pomodoros':>10}{'Breaks':>8}",
    ]
    for label, key in [
        ("Today", "day"),
        ("This week", "week"),
        ("This month", "month"),
    ]:
        row = summary[key]
        lines.append(f"{label:<12}{row[stats.FOCUS]:>10}{row[stats.BREAK]:>8}")

    days = stats.daily(stats_path, start=today.replace(day=1), end=today)
    if days:
        lines += ["", "Daily breakdown (this month):"]
        for day, row in days:
            lines.append(
                f"  {day}  {row[stats.FOCUS]:>3} pomodoros  {row[stats.BREAK]:>3} breaks"
            )
    return "\n".join(lines)


def run(timer: Timer, stats_path=stats.DEFAULT_PATH) -> None:
    import time as _time

    today_count = stats.count(stats_path, stats.FOCUS)
    print("Pomodoro started — Ctrl+C to pause/resume, Ctrl+\\ to quit.")
    last_line_len = 0
    try:
        while True:
            line = render(timer, today_count)
            pad = " " * max(0, last_line_len - len(line))
            print(f"\r{line}{pad}", end="", flush=True)
            last_line_len = len(line)
            if timer.tick():
                sys.stdout.write("\a\n")
                if timer.phase is Phase.BREAK:
                    today_count = stats.record(stats_path, stats.FOCUS)
                    print(f"🍅 Focus complete — {today_count} pomodoro(s) today!")
                else:
                    stats.record(stats_path, stats.BREAK)
                emoji = "☕️" if timer.phase is Phase.BREAK else "🍅"
                print(f"{emoji} {timer.phase.value} started!")
                last_line_len = 0
            _time.sleep(1)
    except KeyboardInterrupt:
        timer.toggle_pause()
        print("\nPaused — press Ctrl+C again to resume.")
        try:
            input()
        except KeyboardInterrupt:
            pass
        timer.toggle_pause()
