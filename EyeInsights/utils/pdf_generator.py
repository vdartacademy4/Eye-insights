"""
utils/pdf_generator.py
-----------------------
Builds the final exam report as a PDF using ReportLab: student
details, exam duration, blink count, warnings (with screenshots),
fraud score and final result.
"""

import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from config import REPORTS_DIR
from database.models import Student, Summary, Warning
from utils.helper import now_filename_stamp
from utils.logger import get_logger

logger = get_logger("PDFGenerator")


def generate_report(student: Student, summary: Summary, warnings: list) -> str:
    """
    Build a full PDF exam report.

    Args:
        student: Student dataclass instance.
        summary: Summary dataclass instance (score, duration, result, etc.).
        warnings: list of Warning dataclass instances raised during the exam.

    Returns:
        Absolute path of the generated PDF file.
    """
    filename = f"report_{_sanitize(student.register_number)}_{now_filename_stamp()}.pdf"
    filepath = os.path.join(REPORTS_DIR, filename)

    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleStyle", parent=styles["Title"], textColor=colors.HexColor("#1565C0"),
    )
    heading_style = ParagraphStyle(
        "HeadingStyle", parent=styles["Heading2"], textColor=colors.HexColor("#0D47A1"),
        spaceBefore=14, spaceAfter=8,
    )
    normal_style = styles["Normal"]

    story = []

    story.append(Paragraph("Eye Insights", title_style))
    story.append(Paragraph("AI Based Exam Fraud Detection Report", styles["Heading3"]))
    story.append(Spacer(1, 0.5 * cm))

    # ---------------- Student details ----------------
    story.append(Paragraph("Student Details", heading_style))
    student_data = [
        ["Name", student.name],
        ["Register Number", student.register_number],
        ["Department", student.department],
        ["Subject", student.subject],
        ["Report Generated", summary.timestamp or "-"],
    ]
    story.append(_build_kv_table(student_data))

    # ---------------- Exam summary ----------------
    story.append(Paragraph("Exam Summary", heading_style))
    minutes, seconds = divmod(int(summary.exam_duration_seconds), 60)
    summary_data = [
        ["Exam Duration", f"{minutes} min {seconds} sec"],
        ["Total Blinks", str(summary.total_blinks)],
        ["Total Warnings", str(summary.total_warnings)],
        ["Fraud Score", f"{summary.fraud_score} / 100"],
        ["Final Result", summary.result],
    ]
    table = _build_kv_table(summary_data)
    result_color = _result_color(summary.result)
    table.setStyle(TableStyle([
        ("TEXTCOLOR", (1, 4), (1, 4), result_color),
        ("FONTNAME", (1, 4), (1, 4), "Helvetica-Bold"),
    ]))
    story.append(table)

    # ---------------- Warnings ----------------
    story.append(Paragraph(f"Warnings Recorded ({len(warnings)})", heading_style))
    if not warnings:
        story.append(Paragraph("No suspicious activity was recorded during this exam.", normal_style))
    else:
        for index, warning in enumerate(warnings, start=1):
            story.append(Paragraph(
                f"<b>{index}. [{warning.warning_type}]</b> {warning.message} "
                f"<i>({warning.timestamp})</i>",
                normal_style,
            ))
            if warning.screenshot_path and os.path.exists(warning.screenshot_path):
                try:
                    story.append(Spacer(1, 0.15 * cm))
                    story.append(Image(warning.screenshot_path, width=7 * cm, height=5.25 * cm))
                except Exception as exc:  # noqa: BLE001
                    logger.error(f"Could not embed screenshot in PDF: {exc}")
            story.append(Spacer(1, 0.3 * cm))

    doc.build(story)
    logger.info(f"PDF report generated at {filepath}")
    return filepath


def _build_kv_table(rows) -> Table:
    table = Table(rows, colWidths=[5 * cm, 10 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E3F2FD")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#0D47A1")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9E2EC")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def _result_color(result: str):
    mapping = {
        "Pass": colors.HexColor("#2E7D32"),
        "Fail": colors.HexColor("#C62828"),
        "Fraud Suspected": colors.HexColor("#C62828"),
    }
    return mapping.get(result, colors.black)


def _sanitize(value: str) -> str:
    keep = "-_"
    return "".join(c for c in str(value) if c.isalnum() or c in keep) or "unknown"
