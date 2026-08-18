"""
database/models.py
-------------------
Lightweight dataclasses that mirror the SQLite table rows. These are
plain data containers -- all persistence logic lives in database.py.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Student:
    id: Optional[int]
    name: str
    register_number: str
    department: str
    subject: str
    created_at: str = ""


@dataclass
class ExamLog:
    id: Optional[int]
    student_id: int
    event_type: str        # e.g. "BLINK", "GAZE_LEFT", "HEAD_TURN", "FACE_MISSING"
    details: str
    timestamp: str = ""


@dataclass
class Warning:
    id: Optional[int]
    student_id: int
    warning_type: str
    message: str
    screenshot_path: str
    timestamp: str = ""


@dataclass
class Summary:
    id: Optional[int]
    student_id: int
    exam_duration_seconds: int
    total_blinks: int
    total_warnings: int
    fraud_score: int
    result: str             # "Pass" | "Fail" | "Fraud Suspected"
    pdf_path: str = ""
    timestamp: str = ""
    extra: dict = field(default_factory=dict)
