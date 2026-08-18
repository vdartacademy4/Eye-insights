"""
ui/exam.py
----------
ExamController glues together the AI monitoring pipeline, the SQLite
database, the exam timer and the fraud engine's warning stream into a
single object the Dashboard screen can drive with simple method calls
(start_exam / poll / stop_exam), keeping ui/dashboard.py focused on
widgets and layout instead of business logic.
"""

from config import (
    DEFAULT_EXAM_DURATION_MINUTES,
    FRAUD_SCORE_FAIL_THRESHOLD,
    MAX_WARNINGS_ALLOWED,
    SCREENSHOT_ON_WARNING,
)
from ai.monitoring import MonitoringSession
from database.database import Database
from database.models import ExamLog, Summary, Warning
from utils.logger import get_logger
from utils.pdf_generator import generate_report
from utils.screenshot import save_screenshot
from utils.timer import ExamTimer

logger = get_logger("ExamController")


class ExamController:
    """Coordinates a full exam session for one student."""

    def __init__(self, database: Database, student):
        self.db = database
        self.student = student

        self.monitoring = MonitoringSession()
        self.timer = ExamTimer(DEFAULT_EXAM_DURATION_MINUTES)

        self._warnings_this_session = []
        self._exam_active = False
        self._max_warnings_hit_callback = None

    def set_max_warnings_callback(self, callback):
        """Register a callback fired exactly once when MAX_WARNINGS_ALLOWED is hit."""
        self._max_warnings_hit_callback = callback

    def start_exam(self) -> bool:
        """Start monitoring + timer. Returns False if the camera failed to open."""
        if not self.monitoring.start():
            return False
        self.timer.reset(DEFAULT_EXAM_DURATION_MINUTES)
        self.timer.start()
        self._warnings_this_session = []
        self._exam_active = True
        logger.info(f"Exam started for student_id={self.student.id}")
        return True

    def poll(self):
        """
        Process the next camera frame. Should be called repeatedly from a
        Tkinter `after()` loop. Returns a MonitoringResult, or None if the
        exam isn't active / no frame was available.
        """
        if not self._exam_active:
            return None

        result = self.monitoring.process_next_frame()
        if result is None:
            return None

        analysis = result.analysis

        if analysis.new_warning is not None:
            self._handle_new_warning(analysis.new_warning)

        return result

    def _handle_new_warning(self, warning_event):
        screenshot_path = ""
        if SCREENSHOT_ON_WARNING:
            frame_bgr = self.monitoring.get_raw_frame_bgr()
            screenshot_path = save_screenshot(
                frame_bgr, self.student.register_number, warning_event.warning_type
            )

        db_warning = Warning(
            id=None, student_id=self.student.id,
            warning_type=warning_event.warning_type, message=warning_event.message,
            screenshot_path=screenshot_path,
        )
        self.db.add_warning(db_warning)
        self.db.add_log(ExamLog(
            id=None, student_id=self.student.id,
            event_type=warning_event.warning_type, details=warning_event.message,
        ))

        db_warning.screenshot_path = screenshot_path
        self._warnings_this_session.append(db_warning)

        total_warnings = self.db.count_warnings(self.student.id)
        if total_warnings >= MAX_WARNINGS_ALLOWED and self._max_warnings_hit_callback:
            self._max_warnings_hit_callback()

    @property
    def warning_count(self) -> int:
        return len(self._warnings_this_session)

    @property
    def is_active(self) -> bool:
        return self._exam_active

    def stop_exam(self) -> Summary:
        """
        Stop monitoring/timer, persist the summary row, generate the PDF
        report and return the Summary object (with pdf_path populated).
        """
        self._exam_active = False
        self.timer.stop()
        self.monitoring.stop()

        fraud_score = self.monitoring.fraud_engine.fraud_score
        blink_count = self.monitoring.blink_detector._blink_count
        duration_seconds = int(self.timer.elapsed())
        total_warnings = len(self._warnings_this_session)

        result = self._determine_result(fraud_score, total_warnings)

        summary = Summary(
            id=None, student_id=self.student.id,
            exam_duration_seconds=duration_seconds, total_blinks=blink_count,
            total_warnings=total_warnings, fraud_score=fraud_score, result=result,
        )

        pdf_path = generate_report(self.student, summary, self._warnings_this_session)
        summary.pdf_path = pdf_path

        self.db.add_summary(summary)
        logger.info(f"Exam stopped for student_id={self.student.id}, result={result}")
        return summary

    @staticmethod
    def _determine_result(fraud_score: int, total_warnings: int) -> str:
        if total_warnings >= MAX_WARNINGS_ALLOWED:
            return "Fraud Suspected"
        if fraud_score >= FRAUD_SCORE_FAIL_THRESHOLD:
            return "Fail"
        return "Pass"

    def close(self):
        """Full teardown, called when leaving the dashboard entirely."""
        self.monitoring.close()
