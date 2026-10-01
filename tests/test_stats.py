import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from pomodoro import stats


class TestStats(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "stats.json"

    def tearDown(self):
        self._tmp.cleanup()

    def test_no_file_means_zero(self):
        self.assertEqual(stats.count(self.path, day="2026-01-01"), 0)
        self.assertEqual(stats.totals(self.path), {stats.FOCUS: 0, stats.BREAK: 0})

    def test_record_increments_focus_and_breaks(self):
        self.assertEqual(stats.record(self.path, stats.FOCUS, day="2026-01-01"), 1)
        self.assertEqual(stats.record(self.path, stats.FOCUS, day="2026-01-01"), 2)
        self.assertEqual(stats.record(self.path, stats.BREAK, day="2026-01-01"), 1)
        self.assertEqual(stats.count(self.path, stats.FOCUS, day="2026-01-01"), 2)
        self.assertEqual(stats.count(self.path, stats.BREAK, day="2026-01-01"), 1)

    def test_new_day_does_not_affect_other_days(self):
        stats.record(self.path, stats.FOCUS, day="2026-01-01")
        stats.record(self.path, stats.FOCUS, day="2026-01-01")
        stats.record(self.path, stats.FOCUS, day="2026-01-02")
        self.assertEqual(stats.count(self.path, stats.FOCUS, day="2026-01-01"), 2)
        self.assertEqual(stats.count(self.path, stats.FOCUS, day="2026-01-02"), 1)

    def test_totals_over_range(self):
        stats.record(self.path, stats.FOCUS, day="2026-01-04")
        stats.record(self.path, stats.FOCUS, day="2026-01-05")
        stats.record(self.path, stats.FOCUS, day="2026-01-05")
        stats.record(self.path, stats.BREAK, day="2026-01-05")
        totals = stats.totals(
            self.path, start=date(2026, 1, 5), end=date(2026, 1, 5)
        )
        self.assertEqual(totals, {stats.FOCUS: 2, stats.BREAK: 1})

    def test_summary_day_week_month(self):
        # 2026-01-01 is a Thursday, so the week containing 2026-01-07 starts Mon 01-05.
        stats.record(self.path, stats.FOCUS, day="2026-01-04")  # prior week
        for _ in range(3):
            stats.record(self.path, stats.FOCUS, day="2026-01-07")  # today
        stats.record(self.path, stats.BREAK, day="2026-01-06")  # this week
        summary = stats.summary(self.path, today=date(2026, 1, 7))
        self.assertEqual(summary["day"], {stats.FOCUS: 3, stats.BREAK: 0})
        self.assertEqual(summary["week"], {stats.FOCUS: 3, stats.BREAK: 1})
        self.assertEqual(summary["month"], {stats.FOCUS: 4, stats.BREAK: 1})

    def test_daily_breakdown_is_sorted_and_filtered(self):
        stats.record(self.path, stats.FOCUS, day="2026-01-03")
        stats.record(self.path, stats.FOCUS, day="2026-01-01")
        stats.record(self.path, stats.BREAK, day="2026-01-01")
        rows = stats.daily(
            self.path, start=date(2026, 1, 1), end=date(2026, 1, 4)
        )
        self.assertEqual(
            rows,
            [
                ("2026-01-01", {stats.FOCUS: 1, stats.BREAK: 1}),
                ("2026-01-03", {stats.FOCUS: 1, stats.BREAK: 0}),
            ],
        )

    def test_legacy_file_is_migrated(self):
        self.path.write_text(json.dumps({"date": "2026-01-01", "count": 4}))
        self.assertEqual(stats.count(self.path, stats.FOCUS, day="2026-01-01"), 4)
        self.assertEqual(stats.count(self.path, stats.BREAK, day="2026-01-01"), 0)

    def test_corrupt_file_is_tolerated(self):
        self.path.write_text("not json")
        self.assertEqual(stats.count(self.path, day="2026-01-01"), 0)
        self.assertEqual(stats.record(self.path, stats.FOCUS, day="2026-01-01"), 1)


if __name__ == "__main__":
    unittest.main()
