"""
ai/eye_tracker.py
------------------
Uses the 468 (+iris) MediaPipe FaceMesh landmarks to locate the left
and right eyes, compute their centers, and estimate gaze direction
(Center / Left / Right / Up / Down) using the iris position relative
to the eye corners.
"""

from utils.helper import clamp, safe_divide
from config import (
    GAZE_DOWN_THRESHOLD,
    GAZE_LEFT_THRESHOLD,
    GAZE_RIGHT_THRESHOLD,
    GAZE_UP_THRESHOLD,
)

# MediaPipe FaceMesh landmark indices -----------------------------------
# Right eye (subject's right eye, left side of a mirrored preview image)
RIGHT_EYE_OUTER = 33
RIGHT_EYE_INNER = 133
RIGHT_EYE_TOP = 159
RIGHT_EYE_BOTTOM = 145
RIGHT_IRIS_CENTER = 468     # only valid when refine_landmarks=True

# Left eye (subject's left eye)
LEFT_EYE_OUTER = 263
LEFT_EYE_INNER = 362
LEFT_EYE_TOP = 386
LEFT_EYE_BOTTOM = 374
LEFT_IRIS_CENTER = 473      # only valid when refine_landmarks=True


class GazeResult:
    """Describes the estimated gaze direction for one frame."""

    def __init__(self, direction: str, horizontal_ratio: float, vertical_ratio: float,
                 left_eye_center, right_eye_center):
        self.direction = direction              # "CENTER" | "LEFT" | "RIGHT" | "UP" | "DOWN"
        self.horizontal_ratio = horizontal_ratio
        self.vertical_ratio = vertical_ratio
        self.left_eye_center = left_eye_center
        self.right_eye_center = right_eye_center


class EyeTracker:
    """Computes eye centers and gaze direction from face landmarks."""

    def estimate_gaze(self, landmarks) -> GazeResult:
        """
        Args:
            landmarks: list of (x_px, y_px, z) tuples, one primary face
                       from FaceDetector.primary_landmarks.

        Returns:
            GazeResult describing direction and eye centers.
        """
        right_outer = landmarks[RIGHT_EYE_OUTER]
        right_inner = landmarks[RIGHT_EYE_INNER]
        right_top = landmarks[RIGHT_EYE_TOP]
        right_bottom = landmarks[RIGHT_EYE_BOTTOM]

        left_outer = landmarks[LEFT_EYE_OUTER]
        left_inner = landmarks[LEFT_EYE_INNER]
        left_top = landmarks[LEFT_EYE_TOP]
        left_bottom = landmarks[LEFT_EYE_BOTTOM]

        right_eye_center = self._midpoint(right_outer, right_inner)
        left_eye_center = self._midpoint(left_outer, left_inner)

        # Iris landmarks are available because refine_landmarks=True.
        if len(landmarks) > RIGHT_IRIS_CENTER and len(landmarks) > LEFT_IRIS_CENTER:
            right_iris = landmarks[RIGHT_IRIS_CENTER]
            left_iris = landmarks[LEFT_IRIS_CENTER]
        else:
            # Fallback: approximate iris as the eye center itself.
            right_iris = right_eye_center
            left_iris = left_eye_center

        h_ratio_right = self._horizontal_ratio(right_iris, right_outer, right_inner)
        h_ratio_left = self._horizontal_ratio(left_iris, left_inner, left_outer)
        horizontal_ratio = (h_ratio_right + h_ratio_left) / 2.0

        v_ratio_right = self._vertical_ratio(right_iris, right_top, right_bottom)
        v_ratio_left = self._vertical_ratio(left_iris, left_top, left_bottom)
        vertical_ratio = (v_ratio_right + v_ratio_left) / 2.0

        direction = self._classify_direction(horizontal_ratio, vertical_ratio)

        return GazeResult(
            direction=direction,
            horizontal_ratio=horizontal_ratio,
            vertical_ratio=vertical_ratio,
            left_eye_center=left_eye_center,
            right_eye_center=right_eye_center,
        )

    @staticmethod
    def _midpoint(point_a, point_b):
        return ((point_a[0] + point_b[0]) / 2.0, (point_a[1] + point_b[1]) / 2.0)

    @staticmethod
    def _horizontal_ratio(iris_point, left_corner, right_corner) -> float:
        """0.0 = fully left corner, 1.0 = fully right corner."""
        eye_width = right_corner[0] - left_corner[0]
        ratio = safe_divide(iris_point[0] - left_corner[0], eye_width, default=0.5)
        return clamp(ratio, 0.0, 1.0)

    @staticmethod
    def _vertical_ratio(iris_point, top_point, bottom_point) -> float:
        """0.0 = fully top lid, 1.0 = fully bottom lid."""
        eye_height = bottom_point[1] - top_point[1]
        ratio = safe_divide(iris_point[1] - top_point[1], eye_height, default=0.5)
        return clamp(ratio, 0.0, 1.0)

    @staticmethod
    def _classify_direction(horizontal_ratio: float, vertical_ratio: float) -> str:
        if horizontal_ratio <= GAZE_LEFT_THRESHOLD:
            return "LEFT"
        if horizontal_ratio >= GAZE_RIGHT_THRESHOLD:
            return "RIGHT"
        if vertical_ratio >= GAZE_DOWN_THRESHOLD:
            return "DOWN"
        if vertical_ratio <= GAZE_UP_THRESHOLD:
            return "UP"
        return "CENTER"
