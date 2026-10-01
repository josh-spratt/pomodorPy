import unittest

from pomodoro.core import Phase, Timer


class FakeClock:
    def __init__(self, t=0.0):
        self.t = t

    def __call__(self):
        return self.t

    def advance(self, s):
        self.t += s


def make_timer(clock=None):
    clock = clock or FakeClock()
    return Timer(focus_seconds=1500, break_seconds=300, clock=clock), clock


class TestInitial(unittest.TestCase):
    def test_starts_in_focus_with_full_duration(self):
        timer, _ = make_timer()
        self.assertEqual(timer.phase, Phase.FOCUS)
        self.assertFalse(timer.paused)
        self.assertEqual(timer.remaining(), 1500)


class TestCountdown(unittest.TestCase):
    def test_remaining_decreases_as_clock_advances(self):
        timer, clock = make_timer()
        clock.advance(10)
        self.assertEqual(timer.remaining(), 1490)

    def test_partial_second_is_not_counted(self):
        timer, clock = make_timer()
        clock.advance(29.5)
        self.assertEqual(timer.remaining(), 1471)


class TestPauseResume(unittest.TestCase):
    def test_paused_time_does_not_elapse(self):
        timer, clock = make_timer()
        clock.advance(100)
        timer.toggle_pause()
        clock.advance(500)
        self.assertTrue(timer.paused)
        self.assertEqual(timer.remaining(), 1400)

    def test_resume_restarts_elapsed_from_frozen_point(self):
        timer, clock = make_timer()
        clock.advance(100)
        timer.toggle_pause()
        clock.advance(500)
        timer.toggle_pause()
        self.assertFalse(timer.paused)
        clock.advance(200)
        self.assertEqual(timer.remaining(), 1200)


class TestPhaseTransition(unittest.TestCase):
    def test_tick_returns_false_before_phase_ends(self):
        timer, clock = make_timer()
        clock.advance(1499)
        self.assertFalse(timer.tick())

    def test_focus_completes_then_flips_to_break(self):
        timer, clock = make_timer()
        clock.advance(1500)
        self.assertTrue(timer.tick())
        self.assertEqual(timer.phase, Phase.BREAK)
        self.assertEqual(timer.remaining(), 300)

    def test_cycle_alternates_and_counts_completions(self):
        timer, clock = make_timer()
        for expected in [Phase.BREAK, Phase.FOCUS, Phase.BREAK]:
            clock.advance(timer.duration)
            timer.tick()
            self.assertEqual(timer.phase, expected)
        self.assertEqual(timer.completions, 3)

    def test_only_focus_completions_count_as_pomodoros(self):
        timer, clock = make_timer()
        clock.advance(1500)
        timer.tick()
        self.assertEqual(timer.focus_completions, 1)
        clock.advance(300)
        timer.tick()
        self.assertEqual(timer.focus_completions, 1)
        clock.advance(1500)
        timer.tick()
        self.assertEqual(timer.focus_completions, 2)


class TestValidation(unittest.TestCase):
    def test_zero_or_negative_durations_raise(self):
        with self.assertRaises(ValueError):
            Timer(focus_seconds=0, break_seconds=300, clock=lambda: 0)
        with self.assertRaises(ValueError):
            Timer(focus_seconds=-5, break_seconds=300, clock=lambda: 0)


if __name__ == "__main__":
    unittest.main()
