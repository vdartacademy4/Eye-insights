"""
tests/test_core.py
-------------------
Lightweight unit tests for the parts of Eye Insights that do not need
a real webcam or display: helpers, the timer, the fraud engine and
the database layer. Run with:

    python -m unittest discover tests
"""

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.fraud_engine import FraudEngine
from database.database import Database
from database.models import Student
from utils.helper import (
    clamp,
    euclidean_distance,
    format_seconds,
    safe_divide,
    validate_non_empty,
    validate_register_number,
)
from utils.timer import ExamTimer


class TestHelpers(unittest.TestCase):
    def test_euclidean_distance(self):
        self.assertAlmostEqual(euclidean_distance((0, 0), (3, 4)), 5.0)

    def test_safe_divide(self):
        self.assertEqual(safe_divide(10, 2), 5.0)
        self.assertEqual(safe_divide(10, 0, default=-1), -1)

    def test_clamp(self):
        self.assertEqual(clamp(5, 0, 10), 5)
        self.assertEqual(clamp(-5, 0, 10), 0)
        self.assertEqual(clamp(15, 0, 10), 10)

    def test_format_seconds(self):
        self.assertEqual(format_seconds(65), "00:01:05")
        self.assertEqual(format_seconds(3661), "01:01:01")

    def test_validate_non_empty(self):
        self.assertTrue(validate_non_empty("Ananya"))
        self.assertFalse(validate_non_empty("   "))

    def test_validate_register_number(self):
        self.assertTrue(validate_register_number("21CS1042"))
        self.assertFalse(validate_register_number("ab"))


class TestExamTimer(unittest.TestCase):
    def test_start_and_elapsed(self):
        timer = ExamTimer(duration_minutes=1)
        timer.start()
        time.sleep(0.2)
        self.assertGreater(timer.elapsed(), 0.15)
        self.assertLess(timer.remaining(), 60)

    def test_is_time_up(self):
        timer = ExamTimer(duration_minutes=0)
        timer.duration_seconds = 0
        timer.start()
        time.sleep(0.05)
        self.assertTrue(timer.is_time_up())


class TestFraudEngine(unittest.TestCase):
    def test_face_missing_raises_warning_after_sustain(self):
        engine = FraudEngine()
        # First call only starts the sustain timer -> no warning yet.
        analysis_1 = engine.evaluate(
            face_count=0, gaze_direction="CENTER", head_direction="NORMAL",
            ear=0.3, eyes_closed=False, eyes_closed_duration=0.0, blink_count=0,
        )
        self.assertIsNone(analysis_1.new_warning)

        time.sleep(1.1)  # exceed VIOLATION_MIN_DURATION

        analysis_2 = engine.evaluate(
            face_count=0, gaze_direction="CENTER", head_direction="NORMAL",
            ear=0.3, eyes_closed=False, eyes_closed_duration=0.0, blink_count=0,
        )
        self.assertIsNotNone(analysis_2.new_warning)
        self.assertEqual(analysis_2.new_warning.warning_type, "FACE_MISSING")
        self.assertGreater(engine.fraud_score, 0)


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.test_db_path = os.path.join(os.path.dirname(__file__), "test_eye_insights.db")
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        self.db = Database(db_path=self.test_db_path)

    def tearDown(self):
        self.db.close()
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_add_and_get_student(self):
        student = Student(id=None, name="Test Student", register_number="TS0001",
                           department="CSE", subject="AI")
        student_id = self.db.add_student(student)
        fetched = self.db.get_student(student_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.register_number, "TS0001")


if __name__ == "__main__":
    unittest.main()
