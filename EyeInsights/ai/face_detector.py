"""
ai/face_detector.py
--------------------
Wraps MediaPipe FaceMesh to detect facial landmarks, and to flag the
"no face" and "multiple faces" conditions that feed the fraud engine.
"""

import mediapipe as mp

from config import (
    FACEMESH_REFINE_LANDMARKS,
    MAX_NUM_FACES,
    MIN_DETECTION_CONFIDENCE,
    MIN_TRACKING_CONFIDENCE,
)
from utils.logger import get_logger

logger = get_logger("FaceDetector")


class FaceDetectionResult:
    """Container describing what FaceDetector found in a single frame."""

    def __init__(self, face_count: int, landmarks_list, image_width: int, image_height: int):
        self.face_count = face_count
        self.landmarks_list = landmarks_list      # list of landmark lists (one per detected face)
        self.image_width = image_width
        self.image_height = image_height

    @property
    def no_face(self) -> bool:
        return self.face_count == 0

    @property
    def multiple_faces(self) -> bool:
        return self.face_count > 1

    @property
    def primary_landmarks(self):
        """Landmarks of the first detected face, or None if no face found."""
        if not self.landmarks_list:
            return None
        return self.landmarks_list[0]


class FaceDetector:
    """Detects facial landmarks (468 points) using MediaPipe FaceMesh."""

    def __init__(self):
        self._mp_face_mesh = mp.solutions.face_mesh
        self._face_mesh = self._mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=MAX_NUM_FACES,
            refine_landmarks=FACEMESH_REFINE_LANDMARKS,
            min_detection_confidence=MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=MIN_TRACKING_CONFIDENCE,
        )
        logger.info("MediaPipe FaceMesh initialised.")

    def process(self, frame_rgb) -> FaceDetectionResult:
        """
        Run FaceMesh on an RGB frame.

        Returns:
            FaceDetectionResult with landmark points converted to pixel
            coordinates [(x_px, y_px, z), ...] for each detected face.
        """
        height, width = frame_rgb.shape[:2]
        results = self._face_mesh.process(frame_rgb)

        landmarks_list = []
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                points = [
                    (lm.x * width, lm.y * height, lm.z)
                    for lm in face_landmarks.landmark
                ]
                landmarks_list.append(points)

        return FaceDetectionResult(
            face_count=len(landmarks_list),
            landmarks_list=landmarks_list,
            image_width=width,
            image_height=height,
        )

    def close(self):
        self._face_mesh.close()
        logger.info("MediaPipe FaceMesh closed.")
