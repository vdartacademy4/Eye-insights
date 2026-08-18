"""
ai/camera.py
------------
Wraps OpenCV VideoCapture to provide a simple, safe interface for
opening the webcam, reading frames (converted to RGB for Tkinter) and
releasing the device correctly.
"""

import cv2

from config import CAMERA_FPS_TARGET, CAMERA_HEIGHT, CAMERA_INDEX, CAMERA_WIDTH
from utils.logger import get_logger

logger = get_logger("Camera")


class Camera:
    """Manages the lifecycle of a webcam capture device."""

    def __init__(self, index: int = CAMERA_INDEX):
        self.index = index
        self._cap = None
        self.is_open = False

    def open(self) -> bool:
        """Open the webcam. Returns True on success."""
        self._cap = cv2.VideoCapture(self.index, cv2.CAP_DSHOW) if _is_windows() else cv2.VideoCapture(self.index)

        if not self._cap or not self._cap.isOpened():
            # Fallback: try opening without backend hint
            self._cap = cv2.VideoCapture(self.index)

        if not self._cap.isOpened():
            logger.error(f"Failed to open camera at index {self.index}")
            self.is_open = False
            return False

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        self._cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS_TARGET)

        self.is_open = True
        logger.info(f"Camera opened at index {self.index}")
        return True

    def read_frame_bgr(self):
        """Return the raw BGR frame from the camera, or None on failure."""
        if not self.is_open or self._cap is None:
            return None

        success, frame = self._cap.read()
        if not success:
            return None

        # Mirror the frame horizontally so it behaves like a webcam preview.
        frame = cv2.flip(frame, 1)
        return frame

    def read_frame_rgb(self):
        """Return the current frame converted to RGB (for PIL / CTk display)."""
        frame_bgr = self.read_frame_bgr()
        if frame_bgr is None:
            return None
        return cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

    def release(self):
        """Release the camera device."""
        if self._cap is not None:
            self._cap.release()
            self.is_open = False
            logger.info("Camera released.")


def _is_windows() -> bool:
    import platform
    return platform.system().lower() == "windows"
