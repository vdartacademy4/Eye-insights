"""
database/database.py
---------------------
SQLite persistence layer for Eye Insights. Provides a single
`Database` class used by the whole application to create tables and
perform CRUD operations for students, exam logs, warnings and the
final per-exam summary.
"""

import sqlite3
from typing import List, Optional

from config import DATABASE_PATH
from database.models import ExamLog, Student, Summary, Warning
from utils.helper import now_timestamp
from utils.logger import get_logger

logger = get_logger("Database")


class Database:
    """Thin wrapper around sqlite3 for all Eye Insights persistence needs."""

    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._create_tables()
        logger.info(f"Database initialised at {self.db_path}")

    # ------------------------------------------------------------------
    # SCHEMA
    # ------------------------------------------------------------------
    def _create_tables(self):
        cursor = self._connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                register_number TEXT NOT NULL,
                department TEXT NOT NULL,
                subject TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS exam_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                details TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                warning_type TEXT NOT NULL,
                message TEXT,
                screenshot_path TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                exam_duration_seconds INTEGER,
                total_blinks INTEGER,
                total_warnings INTEGER,
                fraud_score INTEGER,
                result TEXT,
                pdf_path TEXT,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students (id)
            )
        """)

        self._connection.commit()

    # ------------------------------------------------------------------
    # STUDENTS
    # ------------------------------------------------------------------
    def add_student(self, student: Student) -> int:
        cursor = self._connection.cursor()
        cursor.execute(
            """INSERT INTO students (name, register_number, department, subject, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (student.name, student.register_number, student.department,
             student.subject, now_timestamp()),
        )
        self._connection.commit()
        student_id = cursor.lastrowid
        logger.info(f"Student added: id={student_id}, reg={student.register_number}")
        return student_id

    def get_student(self, student_id: int) -> Optional[Student]:
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM students WHERE id = ?", (student_id,))
        row = cursor.fetchone()
        return self._row_to_student(row) if row else None

    def get_all_students(self) -> List[Student]:
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM students ORDER BY id DESC")
        return [self._row_to_student(r) for r in cursor.fetchall()]

    @staticmethod
    def _row_to_student(row) -> Student:
        return Student(
            id=row["id"], name=row["name"], register_number=row["register_number"],
            department=row["department"], subject=row["subject"], created_at=row["created_at"],
        )

    # ------------------------------------------------------------------
    # EXAM LOGS
    # ------------------------------------------------------------------
    def add_log(self, log: ExamLog) -> int:
        cursor = self._connection.cursor()
        cursor.execute(
            """INSERT INTO exam_logs (student_id, event_type, details, timestamp)
               VALUES (?, ?, ?, ?)""",
            (log.student_id, log.event_type, log.details, now_timestamp()),
        )
        self._connection.commit()
        return cursor.lastrowid

    def get_logs_for_student(self, student_id: int) -> List[ExamLog]:
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT * FROM exam_logs WHERE student_id = ? ORDER BY id ASC", (student_id,)
        )
        return [
            ExamLog(id=r["id"], student_id=r["student_id"], event_type=r["event_type"],
                     details=r["details"], timestamp=r["timestamp"])
            for r in cursor.fetchall()
        ]

    # ------------------------------------------------------------------
    # WARNINGS
    # ------------------------------------------------------------------
    def add_warning(self, warning: Warning) -> int:
        cursor = self._connection.cursor()
        cursor.execute(
            """INSERT INTO warnings (student_id, warning_type, message, screenshot_path, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (warning.student_id, warning.warning_type, warning.message,
             warning.screenshot_path, now_timestamp()),
        )
        self._connection.commit()
        return cursor.lastrowid

    def get_warnings_for_student(self, student_id: int) -> List[Warning]:
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT * FROM warnings WHERE student_id = ? ORDER BY id ASC", (student_id,)
        )
        return [
            Warning(id=r["id"], student_id=r["student_id"], warning_type=r["warning_type"],
                    message=r["message"], screenshot_path=r["screenshot_path"],
                    timestamp=r["timestamp"])
            for r in cursor.fetchall()
        ]

    def count_warnings(self, student_id: int) -> int:
        cursor = self._connection.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM warnings WHERE student_id = ?", (student_id,))
        return cursor.fetchone()["cnt"]

    # ------------------------------------------------------------------
    # SUMMARY
    # ------------------------------------------------------------------
    def add_summary(self, summary: Summary) -> int:
        cursor = self._connection.cursor()
        cursor.execute(
            """INSERT INTO summary (student_id, exam_duration_seconds, total_blinks,
               total_warnings, fraud_score, result, pdf_path, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (summary.student_id, summary.exam_duration_seconds, summary.total_blinks,
             summary.total_warnings, summary.fraud_score, summary.result,
             summary.pdf_path, now_timestamp()),
        )
        self._connection.commit()
        logger.info(f"Summary stored for student_id={summary.student_id}, result={summary.result}")
        return cursor.lastrowid

    def get_summary_for_student(self, student_id: int) -> Optional[Summary]:
        cursor = self._connection.cursor()
        cursor.execute(
            "SELECT * FROM summary WHERE student_id = ? ORDER BY id DESC LIMIT 1", (student_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        return Summary(
            id=row["id"], student_id=row["student_id"],
            exam_duration_seconds=row["exam_duration_seconds"],
            total_blinks=row["total_blinks"], total_warnings=row["total_warnings"],
            fraud_score=row["fraud_score"], result=row["result"],
            pdf_path=row["pdf_path"], timestamp=row["timestamp"],
        )

    def close(self):
        self._connection.close()
        logger.info("Database connection closed.")
