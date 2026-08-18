"""
ai/blink_detector.py
---------------------
Implements blink detection using the Eye Aspect Ratio (EAR) method
(Soukupova & Cech, 2016). Tracks a running blink counter and also
reports how long the eyes have been continuously closed, so the
fraud engine can flag suspiciously long closures.
"""

import time

from config import EAR_BLINK_THRESHOLD, EAR_CONSEC_FRAMES
from utils.helper import euclidean_distance

# MediaPipe FaceMesh 6-point eye landmark sets (classic EAR formulation)
RIGHT_EYE_EAR_POINTS = [33, 160, 158, 133, 153, 144]
LEFT_EYE_EAR_POINTS = [362, 385, 387, 263, 373, 380]


class BlinkResult:
    """Per-frame blink detector output."""

    def __init__(self, ear: float, eyes_closed: bool, blink_count: int,
                 eyes_closed_duration: float):
        self.ear = ear
        self.eyes_closed = eyes_closed
        self.blink_count = blink_count
        self.eyes_closed_duration = eyes_closed_duration


class BlinkDetector:
    """Stateful blink counter based on consecutive low-EAR frames."""

    def __init__(self):
        self._consecutive_closed_frames = 0
        self._blink_count = 0
        self._eyes_closed_since = None

    def reset(self):
        self._consecutive_closed_frames = 0
        self._blink_count = 0
        self._eyes_closed_since = None

    def process(self, landmarks) -> BlinkResult:
        """
        Args:
            landmarks: list of (x_px, y_px, z) tuples for one face.

        Returns:
            BlinkResult with current EAR, closed-state and blink count.
        """
        right_ear = self._eye_aspect_ratio(landmarks, RIGHT_EYE_EAR_POINTS)
        left_ear = self._eye_aspect_ratio(landmarks, LEFT_EYE_EAR_POINTS)
        avg_ear = (right_ear + left_ear) / 2.0

        eyes_closed = avg_ear < EAR_BLINK_THRESHOLD

        if eyes_closed:
            self._consecutive_closed_frames += 1
            if self._eyes_closed_since is None:
                self._eyes_closed_since = time.time()
        else:
            if self._consecutive_closed_frames >= EAR_CONSEC_FRAMES:
                self._blink_count += 1
            self._consecutive_closed_frames = 0
            self._eyes_closed_since = None

        closed_duration = 0.0
        if self._eyes_closed_since is not None:
            closed_duration = time.time() - self._eyes_closed_since

        return BlinkResult(
            ear=avg_ear,
            eyes_closed=eyes_closed,
            blink_count=self._blink_count,
            eyes_closed_duration=closed_duration,
        )

    @staticmethod
    def _eye_aspect_ratio(landmarks, indices) -> float:
        p1, p2, p3, p4, p5, p6 = [landmarks[i] for i in indices]
        vertical_1 = euclidean_distance(p2, p6)
        vertical_2 = euclidean_distance(p3, p5)
        horizontal = euclidean_distance(p1, p4)
        if horizontal == 0:
            return 0.3  # neutral fallback, avoids division by zero
        return (vertical_1 + vertical_2) / (2.0 * horizontal)
