"""
utils/timer.py
---------------
A simple stopwatch/countdown timer used to track exam duration.
Thread-safe enough for the single Tkinter `after()` polling loop used
by the dashboard (no background threads touch it concurrently).
"""

import time

from utils.helper import format_seconds


class ExamTimer:
    """Tracks elapsed and remaining time for an exam session."""

    def __init__(self, duration_minutes: int = 60):
        self.duration_seconds = duration_minutes * 60
        self._start_time = None
        self._elapsed_at_pause = 0.0
        self._running = False

    def start(self):
        """Start (or resume) the timer."""
        if not self._running:
            self._start_time = time.time()
            self._running = True

    def pause(self):
        """Pause the timer, preserving elapsed time."""
        if self._running:
            self._elapsed_at_pause += time.time() - self._start_time
            self._running = False

    def stop(self):
        """Stop the timer completely."""
        if self._running:
            self._elapsed_at_pause += time.time() - self._start_time
        self._running = False

    def reset(self, duration_minutes: int = None):
        """Reset the timer, optionally with a new duration."""
        if duration_minutes is not None:
            self.duration_seconds = duration_minutes * 60
        self._start_time = None
        self._elapsed_at_pause = 0.0
        self._running = False

    def elapsed(self) -> float:
        """Return total elapsed seconds so far."""
        if self._running and self._start_time is not None:
            return self._elapsed_at_pause + (time.time() - self._start_time)
        return self._elapsed_at_pause

    def remaining(self) -> float:
        """Return remaining seconds until duration expires (never negative)."""
        return max(0.0, self.duration_seconds - self.elapsed())

    def is_time_up(self) -> bool:
        """True once the configured duration has fully elapsed."""
        return self.elapsed() >= self.duration_seconds

    def elapsed_formatted(self) -> str:
        return format_seconds(self.elapsed())

    def remaining_formatted(self) -> str:
        return format_seconds(self.remaining())
