"""
ui/report.py
------------
Report screen: shows the final exam summary (with a small matplotlib
chart of warning types) and lets the user open/download the generated
PDF report.
"""

import os
import subprocess
import sys
from collections import Counter

import customtkinter as ctk
import matplotlib
matplotlib.use("Agg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from config import COLOR_BACKGROUND, COLOR_DANGER, COLOR_SUCCESS, COLOR_WARNING, FONT_SUBTITLE
from ui.styles import (
    body_label_kwargs,
    card_frame_kwargs,
    heading_label_kwargs,
    primary_button_kwargs,
    secondary_button_kwargs,
)
from utils.logger import get_logger

logger = get_logger("ReportScreen")


class ReportScreen(ctk.CTkFrame):
    """Displays the stored summary/warnings for a student and opens the PDF."""

    def __init__(self, master, controller):
        super().__init__(master, fg_color=COLOR_BACKGROUND)
        self.controller = controller
        self.student = None
        self.summary = None
        self._pdf_path = None

        self._build_layout()

    def _build_layout(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(18, 6))

        ctk.CTkLabel(header, text="Exam Report", **heading_label_kwargs()).pack(side="left")

        back_button = ctk.CTkButton(
            header, text="⬅ Back to Dashboard", width=170,
            command=self._on_back, **secondary_button_kwargs(),
        )
        back_button.pack(side="right")

        self.body = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.body.pack(fill="both", expand=True, padx=24, pady=(0, 20))

    def load_report(self, student):
        """Fetch the latest summary + warnings for `student` and render them."""
        self.student = student
        for widget in self.body.winfo_children():
            widget.destroy()

        self.summary = self.controller.db.get_summary_for_student(student.id)
        warnings = self.controller.db.get_warnings_for_student(student.id)

        if self.summary is None:
            ctk.CTkLabel(
                self.body, text="No exam has been completed for this student yet.",
                **body_label_kwargs(),
            ).pack(pady=40)
            return

        self._pdf_path = self.summary.pdf_path

        self._render_summary_card(warnings)
        self._render_chart(warnings)
        self._render_warning_list(warnings)
        self._render_download_button()

    def _render_summary_card(self, warnings):
        card = ctk.CTkFrame(self.body, **card_frame_kwargs())
        card.pack(fill="x", pady=(10, 16))

        ctk.CTkLabel(
            card, text=f"{self.student.name}  ({self.student.register_number})",
            **heading_label_kwargs(),
        ).pack(anchor="w", padx=20, pady=(18, 2))
        ctk.CTkLabel(
            card, text=f"{self.student.department} • {self.student.subject}",
            **body_label_kwargs(),
        ).pack(anchor="w", padx=20, pady=(0, 14))

        result_color = {
            "Pass": COLOR_SUCCESS, "Fail": COLOR_DANGER, "Fraud Suspected": COLOR_DANGER,
        }.get(self.summary.result, COLOR_WARNING)

        stats_row = ctk.CTkFrame(card, fg_color="transparent")
        stats_row.pack(fill="x", padx=20, pady=(0, 20))

        minutes, seconds = divmod(self.summary.exam_duration_seconds, 60)
        stats = [
            ("Duration", f"{minutes}m {seconds}s"),
            ("Total Blinks", str(self.summary.total_blinks)),
            ("Warnings", str(self.summary.total_warnings)),
            ("Fraud Score", f"{self.summary.fraud_score}/100"),
            ("Result", self.summary.result),
        ]
        for i, (label, value) in enumerate(stats):
            stat_frame = ctk.CTkFrame(stats_row, fg_color="transparent")
            stat_frame.grid(row=0, column=i, padx=14, sticky="w")
            ctk.CTkLabel(stat_frame, text=label, font=FONT_SUBTITLE,
                         text_color="#486581").pack(anchor="w")
            value_color = result_color if label == "Result" else "#102A43"
            ctk.CTkLabel(stat_frame, text=value, font=("Segoe UI", 16, "bold"),
                         text_color=value_color).pack(anchor="w")

    def _render_chart(self, warnings):
        card = ctk.CTkFrame(self.body, **card_frame_kwargs())
        card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(card, text="Warning Breakdown", **heading_label_kwargs()).pack(
            anchor="w", padx=20, pady=(16, 4)
        )

        counts = Counter(w.warning_type for w in warnings)

        figure = Figure(figsize=(6, 2.6), dpi=100)
        axis = figure.add_subplot(111)

        if counts:
            labels = list(counts.keys())
            values = list(counts.values())
            bars = axis.bar(labels, values, color="#1565C0")
            axis.set_ylabel("Count")
            axis.tick_params(axis="x", labelrotation=20, labelsize=8)
            for bar in bars:
                height = bar.get_height()
                axis.annotate(str(int(height)), (bar.get_x() + bar.get_width() / 2, height),
                               ha="center", va="bottom", fontsize=8)
        else:
            axis.text(0.5, 0.5, "No warnings recorded", ha="center", va="center")
            axis.set_xticks([])
            axis.set_yticks([])

        figure.tight_layout()

        canvas = FigureCanvasTkAgg(figure, master=card)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="x", padx=16, pady=(0, 16))

    def _render_warning_list(self, warnings):
        card = ctk.CTkFrame(self.body, **card_frame_kwargs())
        card.pack(fill="x", pady=(0, 16))

        ctk.CTkLabel(card, text=f"Warning Log ({len(warnings)})", **heading_label_kwargs()).pack(
            anchor="w", padx=20, pady=(16, 8)
        )

        if not warnings:
            ctk.CTkLabel(card, text="No suspicious activity was recorded.",
                         **body_label_kwargs()).pack(anchor="w", padx=20, pady=(0, 16))
            return

        for warning in warnings:
            row = ctk.CTkFrame(card, fg_color="#F4F7FB", corner_radius=8)
            row.pack(fill="x", padx=20, pady=4)
            ctk.CTkLabel(
                row, text=f"[{warning.warning_type}]  {warning.message}",
                font=FONT_SUBTITLE, text_color="#102A43", anchor="w",
            ).pack(side="left", padx=12, pady=8)
            ctk.CTkLabel(
                row, text=warning.timestamp, font=FONT_SUBTITLE, text_color="#829AB1",
            ).pack(side="right", padx=12)

        ctk.CTkFrame(card, height=6, fg_color="transparent").pack()

    def _render_download_button(self):
        button = ctk.CTkButton(
            self.body, text="📄  Open / Download PDF Report",
            command=self._open_pdf, **primary_button_kwargs(),
        )
        button.pack(pady=(4, 24))

    def _open_pdf(self):
        if not self._pdf_path or not os.path.exists(self._pdf_path):
            logger.error("PDF path missing or file does not exist.")
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(self._pdf_path)  # noqa: S606
            elif sys.platform == "darwin":
                subprocess.run(["open", self._pdf_path], check=False)
            else:
                subprocess.run(["xdg-open", self._pdf_path], check=False)
        except Exception as exc:  # noqa: BLE001
            logger.error(f"Failed to open PDF: {exc}")

    def _on_back(self):
        self.controller.show_dashboard(self.student, reset=False)
