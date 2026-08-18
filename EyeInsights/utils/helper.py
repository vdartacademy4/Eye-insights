"""
utils/helper.py
----------------
Small, reusable helper functions used across the AI pipeline and UI:
distance calculations, timestamp formatting, safe division, clamping, etc.
"""

import math
from datetime import datetime


def euclidean_distance(point_a, point_b) -> float:
    """Return the euclidean distance between two (x, y) points."""
    return math.sqrt((point_a[0] - point_b[0]) ** 2 + (point_a[1] - point_b[1]) ** 2)


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Divide two numbers, returning `default` instead of raising on zero division."""
    if denominator == 0:
        return default
    return numerator / denominator


def clamp(value: float, min_value: float, max_value: float) -> float:
    """Clamp `value` into the inclusive range [min_value, max_value]."""
    return max(min_value, min(value, max_value))


def now_timestamp() -> str:
    """Return current time formatted as 'YYYY-MM-DD HH:MM:SS'."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def now_filename_stamp() -> str:
    """Return current time formatted for safe use inside filenames."""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def format_seconds(total_seconds: float) -> str:
    """Format a duration given in seconds as HH:MM:SS."""
    total_seconds = int(max(0, total_seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def validate_non_empty(value: str) -> bool:
    """Return True if the given string is non-empty after stripping whitespace."""
    return isinstance(value, str) and len(value.strip()) > 0


def validate_register_number(value: str) -> bool:
    """Basic validation: register number must be alphanumeric, 4-20 characters."""
    value = value.strip()
    return value.isalnum() and 4 <= len(value) <= 20
