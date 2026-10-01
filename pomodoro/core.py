"""Pure timer engine for the Pomodoro cycle.

Time is injected so tests can advance the clock without sleeping.
"""

import enum
import time


class Phase(enum.Enum):
    FOCUS = "Focus"
    BREAK = "Break"


class Timer:
    def __init__(self, focus_seconds: int, break_seconds: int, clock=time.monotonic):
        if focus_seconds <= 0 or break_seconds <= 0:
            raise ValueError("durations must be positive")
        self._focus_seconds = focus_seconds
        self._break_seconds = break_seconds
        self._clock = clock
        self.phase = Phase.FOCUS
        self._start = clock()
        self._paused_at: float | None = None
        self.completions = 0
        self.focus_completions = 0

    @property
    def duration(self) -> int:
        return (
            self._focus_seconds if self.phase is Phase.FOCUS else self._break_seconds
        )

    @property
    def paused(self) -> bool:
        return self._paused_at is not None

    def remaining(self) -> int:
        """Seconds left in the current phase, clamped at zero."""
        if self.paused:
            elapsed = self._paused_at - self._start
        else:
            elapsed = self._clock() - self._start
        return max(0, self.duration - int(elapsed))

    def toggle_pause(self) -> None:
        if self._paused_at is None:
            self._paused_at = self._clock()
        else:
            # Freeze the elapsed time by re-anchoring the start point.
            self._start += self._clock() - self._paused_at
            self._paused_at = None

    def tick(self) -> bool:
        """Advance the cycle. Returns True when the phase just completed."""
        if self.remaining() > 0:
            return False
        if self.phase is Phase.FOCUS:
            self.focus_completions += 1
        self.completions += 1
        self.phase = Phase.BREAK if self.phase is Phase.FOCUS else Phase.FOCUS
        self._start = self._clock()
        return True
