"""Entry point: python -m pomodoro"""

import argparse

from . import settings, stats
from .cli import render_stats, run
from .core import Timer


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        prog="pomodoro", description="A terminal Pomodoro timer."
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="print pomodoro/break totals for today, this week and this month, then exit",
    )
    parser.add_argument(
        "--stats-file",
        default=stats.DEFAULT_PATH,
        help=f"stats file location (default: {stats.DEFAULT_PATH})",
    )
    args = parser.parse_args(argv)

    if args.stats:
        print(render_stats(args.stats_file))
        return

    timer = Timer(
        focus_seconds=settings.FOCUS_MINUTES * 60,
        break_seconds=settings.BREAK_MINUTES * 60,
    )
    run(timer, args.stats_file)


if __name__ == "__main__":
    main()
