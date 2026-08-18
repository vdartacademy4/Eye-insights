"""
ai/fraud_engine.py
-------------------
Combines the outputs of FaceDetector, EyeTracker, BlinkDetector and
HeadPoseEstimator into a single fraud score and a stream of discrete
"warning" events. Applies minimum-duration and cooldown logic so
that a single noisy frame does not spam warnings.
"""

import time
from dataclasses import dataclass, field
from typing import List, Optional

from config import (
    FRAUD_POINTS_EYES_CLOSED_LONG,
    FRAUD_POINTS_FACE_MISSING,
    FRAUD_POINTS_HEAD_TURNED,
    FRAUD_POINTS_LOOK_DOWN,
    FRAUD_POINTS_LOOK_LEFT,
    FRAUD_POINTS_LOOK_RIGHT,
    FRAUD_POINTS_MULTIPLE_FACES,
    FRAUD_SCORE_MAX,
    EYES_CLOSED_ALERT_SECONDS,
    VIOLATION_MIN_DURATION,
    WARNING_COOLDOWN_SECONDS,
)
from utils.logger import get_logger

logger = get_logger("FraudEngine")


@dataclass
class WarningEvent:
    """A discrete fraud warning raised by the engine."""
    warning_type: str
    message: str
    points: int
    timestamp: float = field(default_factory=time.time)


@dataclass
class FraudAnalysis:
    """Aggregated per-frame status returned to the monitoring layer."""
    face_count: int = 0
    gaze_direction: str = "CENTER"
    head_direction: str = "NORMAL"
    ear: float = 0.0
    eyes_closed: bool = False
    blink_count: int = 0
    fraud_score: int = 0
    new_warning: Optional[WarningEvent] = None
    status_text: str = "Monitoring Normal"
    status_level: str = "OK"          # "OK" | "CAUTION" | "DANGER"


class FraudEngine:
    """Stateful engine that turns per-frame AI signals into a fraud score."""

    def __init__(self):
        self.fraud_score: int = 0
        self.warnings: List[WarningEvent] = []

        # Track how long a given condition has been continuously true,
        # so a single flickering frame doesn't trigger a warning.
        self._condition_start_time = {}
        # Track the last time each warning type fired, for cooldown.
        self._last_warning_time = {}

    def reset(self):
        self.fraud_score = 0
        self.warnings = []
        self._condition_start_time = {}
        self._last_warning_time = {}

    def evaluate(self, face_count: int, gaze_direction: str, head_direction: str,
                 ear: float, eyes_closed: bool, eyes_closed_duration: float,
                 blink_count: int) -> FraudAnalysis:
        """
        Evaluate one frame's worth of AI signals and update the fraud score.
        Returns a FraudAnalysis describing the current state (and any new
        warning that should trigger a screenshot + DB log).
        """
        new_warning = None

        if face_count == 0:
            new_warning = self._maybe_raise(
                "FACE_MISSING", "No face detected in frame.", FRAUD_POINTS_FACE_MISSING
            )
        elif face_count > 1:
            new_warning = self._maybe_raise(
                "MULTIPLE_FACES", "Multiple faces detected in frame.", FRAUD_POINTS_MULTIPLE_FACES
            )
        else:
            # Only evaluate gaze/head/eye conditions when exactly one face is present.
            if gaze_direction == "LEFT":
                new_warning = self._maybe_raise(
                    "LOOK_LEFT", "Student looked to the left.", FRAUD_POINTS_LOOK_LEFT
                )
            elif gaze_direction == "RIGHT":
                new_warning = self._maybe_raise(
                    "LOOK_RIGHT", "Student looked to the right.", FRAUD_POINTS_LOOK_RIGHT
                )
            elif gaze_direction == "DOWN":
                new_warning = self._maybe_raise(
                    "LOOK_DOWN", "Student looked down repeatedly.", FRAUD_POINTS_LOOK_DOWN
                )

            if new_warning is None and head_direction in ("LEFT", "RIGHT", "UP", "DOWN"):
                new_warning = self._maybe_raise(
                    "HEAD_TURNED", f"Head turned {head_direction.lower()}.", FRAUD_POINTS_HEAD_TURNED
                )

            if new_warning is None and eyes_closed and eyes_closed_duration >= EYES_CLOSED_ALERT_SECONDS:
                new_warning = self._maybe_raise(
                    "EYES_CLOSED_LONG",
                    f"Eyes closed for {eyes_closed_duration:.1f} seconds.",
                    FRAUD_POINTS_EYES_CLOSED_LONG,
                )

        if new_warning:
            self.fraud_score = min(FRAUD_SCORE_MAX, self.fraud_score + new_warning.points)
            self.warnings.append(new_warning)
            logger.warning(f"Fraud warning raised: {new_warning.warning_type} "
                            f"(+{new_warning.points} -> score={self.fraud_score})")

        status_text, status_level = self._status_summary(
            face_count, gaze_direction, head_direction, eyes_closed
        )

        return FraudAnalysis(
            face_count=face_count,
            gaze_direction=gaze_direction,
            head_direction=head_direction,
            ear=ear,
            eyes_closed=eyes_closed,
            blink_count=blink_count,
            fraud_score=self.fraud_score,
            new_warning=new_warning,
            status_text=status_text,
            status_level=status_level,
        )

    def _maybe_raise(self, warning_type: str, message: str, points: int) -> Optional[WarningEvent]:
        """
        Apply "minimum sustained duration" + "cooldown" logic before
        actually raising a warning event.
        """
        now = time.time()

        start = self._condition_start_time.get(warning_type)
        if start is None:
            self._condition_start_time[warning_type] = now
            return None  # condition just started, not sustained yet

        sustained_for = now - start
        if sustained_for < VIOLATION_MIN_DURATION:
            return None  # not sustained long enough yet

        last_fired = self._last_warning_time.get(warning_type, 0)
        if now - last_fired < WARNING_COOLDOWN_SECONDS:
            return None  # still cooling down since the last identical warning

        self._last_warning_time[warning_type] = now
        self._condition_start_time[warning_type] = now  # restart sustain window
        return WarningEvent(warning_type=warning_type, message=message, points=points)

    def clear_condition(self, warning_type: str):
        """Call when a condition is no longer true, to reset its sustain timer."""
        self._condition_start_time.pop(warning_type, None)

    @staticmethod
    def _status_summary(face_count, gaze_direction, head_direction, eyes_closed):
        if face_count == 0:
            return "No Face Detected", "DANGER"
        if face_count > 1:
            return "Multiple Faces Detected", "DANGER"
        if gaze_direction != "CENTER":
            return f"Looking {gaze_direction.title()}", "CAUTION"
        if head_direction != "NORMAL":
            return f"Head Turned {head_direction.title()}", "CAUTION"
        if eyes_closed:
            return "Eyes Closed", "CAUTION"
        return "Monitoring Normal", "OK"
