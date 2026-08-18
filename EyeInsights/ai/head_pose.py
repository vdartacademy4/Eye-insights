"""
ai/head_pose.py
----------------
Estimates head rotation (yaw / pitch) from 2D facial landmarks using
OpenCV's solvePnP against a generic 3D face model. Classifies the
head as Normal / Looking Left / Looking Right / Looking Up / Looking Down.
"""

import cv2
import numpy as np

from config import (
    HEAD_PITCH_DOWN_THRESHOLD,
    HEAD_PITCH_UP_THRESHOLD,
    HEAD_YAW_LEFT_THRESHOLD,
    HEAD_YAW_RIGHT_THRESHOLD,
)

# Landmark indices used for the PnP solve (correspond to the 3D model below)
NOSE_TIP = 1
CHIN = 152
LEFT_EYE_CORNER = 33
RIGHT_EYE_CORNER = 263
LEFT_MOUTH_CORNER = 61
RIGHT_MOUTH_CORNER = 291

# Generic 3D face model points (arbitrary units, approximate human geometry)
_MODEL_POINTS_3D = np.array([
    (0.0, 0.0, 0.0),          # Nose tip
    (0.0, -330.0, -65.0),     # Chin
    (-225.0, 170.0, -135.0),  # Left eye corner
    (225.0, 170.0, -135.0),   # Right eye corner
    (-150.0, -150.0, -125.0), # Left mouth corner
    (150.0, -150.0, -125.0),  # Right mouth corner
], dtype=np.float64)


class HeadPoseResult:
    """Describes head orientation for a single frame."""

    def __init__(self, yaw: float, pitch: float, roll: float, direction: str):
        self.yaw = yaw
        self.pitch = pitch
        self.roll = roll
        self.direction = direction   # "NORMAL" | "LEFT" | "RIGHT" | "UP" | "DOWN"


class HeadPoseEstimator:
    """Solves head pose (yaw/pitch/roll) using solvePnP."""

    def estimate(self, landmarks, image_width: int, image_height: int) -> HeadPoseResult:
        image_points = np.array([
            landmarks[NOSE_TIP][:2],
            landmarks[CHIN][:2],
            landmarks[LEFT_EYE_CORNER][:2],
            landmarks[RIGHT_EYE_CORNER][:2],
            landmarks[LEFT_MOUTH_CORNER][:2],
            landmarks[RIGHT_MOUTH_CORNER][:2],
        ], dtype=np.float64)

        focal_length = image_width
        center = (image_width / 2.0, image_height / 2.0)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1],
        ], dtype=np.float64)

        dist_coeffs = np.zeros((4, 1))  # assume no lens distortion

        success, rotation_vector, _ = cv2.solvePnP(
            _MODEL_POINTS_3D, image_points, camera_matrix, dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE,
        )

        if not success:
            return HeadPoseResult(yaw=0.0, pitch=0.0, roll=0.0, direction="NORMAL")

        rotation_matrix, _ = cv2.Rodrigues(rotation_vector)

        pitch, yaw, roll = self._rotation_matrix_to_euler(rotation_matrix)

        direction = self._classify_direction(yaw, pitch)

        return HeadPoseResult(yaw=yaw, pitch=pitch, roll=roll, direction=direction)

    @staticmethod
    def _rotation_matrix_to_euler(rotation_matrix):
        """Convert a rotation matrix to Euler angles (degrees): pitch, yaw, roll."""
        sy = np.sqrt(rotation_matrix[0, 0] ** 2 + rotation_matrix[1, 0] ** 2)
        singular = sy < 1e-6

        if not singular:
            x = np.arctan2(rotation_matrix[2, 1], rotation_matrix[2, 2])
            y = np.arctan2(-rotation_matrix[2, 0], sy)
            z = np.arctan2(rotation_matrix[1, 0], rotation_matrix[0, 0])
        else:
            x = np.arctan2(-rotation_matrix[1, 2], rotation_matrix[1, 1])
            y = np.arctan2(-rotation_matrix[2, 0], sy)
            z = 0

        pitch = np.degrees(x)
        yaw = np.degrees(y)
        roll = np.degrees(z)

        # Normalise pitch into a human-readable "looking down positive" range
        if pitch > 90:
            pitch = pitch - 180
        elif pitch < -90:
            pitch = pitch + 180

        return pitch, yaw, roll

    @staticmethod
    def _classify_direction(yaw: float, pitch: float) -> str:
        if yaw < HEAD_YAW_LEFT_THRESHOLD:
            return "LEFT"
        if yaw > HEAD_YAW_RIGHT_THRESHOLD:
            return "RIGHT"
        if pitch > HEAD_PITCH_DOWN_THRESHOLD:
            return "DOWN"
        if pitch < HEAD_PITCH_UP_THRESHOLD:
            return "UP"
        return "NORMAL"
