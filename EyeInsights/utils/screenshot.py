"""
utils/screenshot.py
--------------------
Handles saving webcam frames to disk whenever the fraud engine raises
a warning, so the report can later reference visual evidence.
"""

import os

import cv2

from config import SCREENSHOTS_DIR, SCREENSHOT_JPEG_QUALITY
from utils.helper import now_filename_stamp
from utils.logger import get_logger

logger = get_logger("Screenshot")


def save_screenshot(frame_bgr, register_number: str, reason: str) -> str:
    """
    Save a BGR OpenCV frame to disk as a JPEG.

    Args:
        frame_bgr: The OpenCV frame (numpy array, BGR order).
        register_number: Student register number, used to namespace files.
        reason: Short reason string (e.g. "look_left") embedded in filename.

    Returns:
        The absolute path of the saved screenshot, or "" on failure.
    """
    if frame_bgr is None:
        logger.warning("Attempted to save a screenshot but frame was None.")
        return ""

    student_folder = os.path.join(SCREENSHOTS_DIR, _sanitize(register_number))
    os.makedirs(student_folder, exist_ok=True)

    safe_reason = _sanitize(reason)
    filename = f"{safe_reason}_{now_filename_stamp()}.jpg"
    filepath = os.path.join(student_folder, filename)

    try:
        cv2.imwrite(
            filepath,
            frame_bgr,
            [cv2.IMWRITE_JPEG_QUALITY, SCREENSHOT_JPEG_QUALITY],
        )
        logger.info(f"Screenshot saved: {filepath}")
        return filepath
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Failed to save screenshot: {exc}")
        return ""


def _sanitize(value: str) -> str:
    """Strip characters that are unsafe for filenames/folders."""
    keep = "-_"
    return "".join(c for c in str(value) if c.isalnum() or c in keep) or "unknown"
