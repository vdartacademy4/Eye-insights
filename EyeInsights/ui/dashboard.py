"""
ui/dashboard.py
----------------
The main exam dashboard: student details on the left, live webcam
feed + live status cards on the right, and controls to start/stop
monitoring, generate the PDF report, and exit.
"""

import customtkinter as ctk
from PIL import Image
from tkinter import messagebox

from config import (
    COLOR_BACKGROUND,
    COLOR_DANGER,
    COLOR_SUCCESS,
    COLOR_TEXT_SECONDARY,
    CAMERA_HEIGHT,
    CAMERA_WIDTH,
    FONT_SUBTITLE,
    MAX_WARNINGS_ALLOWED,
)
from ui.exam import ExamController
from ui.styles import (
    body_label_kwargs,
    card_frame_kwargs,
    danger_button_kwargs,
    heading_label_kwargs,
    primary_button_kwargs,
    secondary_button_kwargs,
    status_level_color,
)
from ui.warning import MaxWarningsDialog, WarningToast
from ui.widgets import StatusCard
from utils.logger import get_logger

logger = get_logger("DashboardScreen")

_POLL_INTERVAL_MS = 30  # ~33 FPS UI refresh target


class DashboardScreen(ctk.CTkFrame):
    """Live monitoring dashboard shown after a successful login."""

    def __init__(self, master, controller):
        super().__init__(master, fg_color=COLOR_BACKGROUND)
        self.controller = controller
        self.student = None
        self.exam_controller = None

        self._poll_job = None
        self._max_warnings_dialog_shown = False

        self._build_layout()

    # ------------------------------------------------------------------
    # LAYOUT
    # ------------------------------------------------------------------
    def _build_layout(self):
        header = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header.pack(fill="x", padx=24, pady=(18, 6))

        ctk.CTkLabel(header, text="Exam Monitoring Dashboard", **heading_label_kwargs()).pack(side="left")

        self.exit_button = ctk.CTkButton(
            header, text="Exit", width=90, command=self._on_exit, **danger_button_kwargs(),
        )
        self.exit_button.pack(side="right")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        body.grid_columnconfigure(0, weight=0)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self._build_left_panel(body)
        self._build_right_panel(body)

        # Warning toast floats above everything
        self.warning_toast = WarningToast(self)

    def _build_left_panel(self, parent):
        panel = ctk.CTkFrame(parent, width=280, **card_frame_kwargs())
        panel.grid(row=0, column=0, sticky="ns", padx=(0, 16))
        panel.grid_propagate(False)

        ctk.CTkLabel(panel, text="Student Details", **heading_label_kwargs()).pack(
            anchor="w", padx=20, pady=(20, 14)
        )

        self.detail_labels = {}
        for key in ("Name", "Register No.", "Department", "Subject"):
            row = ctk.CTkFrame(panel, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=6)
            ctk.CTkLabel(row, text=key, font=FONT_SUBTITLE, text_color=COLOR_TEXT_SECONDARY,
                         anchor="w").pack(fill="x")
            value_label = ctk.CTkLabel(row, text="-", **body_label_kwargs(), anchor="w",
                                        wraplength=230, justify="left")
            value_label.configure(text_color="#102A43", font=("Segoe UI", 14, "bold"))
            value_label.pack(fill="x")
            self.detail_labels[key] = value_label

        ctk.CTkFrame(panel, height=2, fg_color="#D9E2EC").pack(fill="x", padx=20, pady=16)

        ctk.CTkLabel(panel, text="Session Controls", **heading_label_kwargs()).pack(
            anchor="w", padx=20, pady=(0, 10)
        )

        self.start_button = ctk.CTkButton(
            panel, text="▶  Start Monitoring", command=self._on_start_monitoring,
            **primary_button_kwargs(),
        )
        self.start_button.pack(fill="x", padx=20, pady=6)

        self.stop_button = ctk.CTkButton(
            panel, text="■  Stop Monitoring", command=self._on_stop_monitoring,
            state="disabled", **danger_button_kwargs(),
        )
        self.stop_button.pack(fill="x", padx=20, pady=6)

        self.report_button = ctk.CTkButton(
            panel, text="📄  View Report", command=self._on_view_report,
            state="disabled", **secondary_button_kwargs(),
        )
        self.report_button.pack(fill="x", padx=20, pady=6)

    def _build_right_panel(self, parent):
        panel = ctk.CTkFrame(parent, fg_color="transparent")
        panel.grid(row=0, column=1, sticky="nsew")
        panel.grid_rowconfigure(0, weight=3)
        panel.grid_rowconfigure(1, weight=1)
        panel.grid_columnconfigure(0, weight=1)

        # Webcam feed ------------------------------------------------------
        feed_card = ctk.CTkFrame(panel, **card_frame_kwargs())
        feed_card.grid(row=0, column=0, sticky="nsew", pady=(0, 16))

        self.feed_label = ctk.CTkLabel(
            feed_card, text="Camera feed will appear here once monitoring starts.",
            fg_color="#0D1B2A", text_color="white", corner_radius=10,
        )
        self.feed_label.pack(fill="both", expand=True, padx=14, pady=14)
        self._placeholder_image = None

        # Status cards -------------------------------------------------------
        cards_frame = ctk.CTkFrame(panel, fg_color="transparent")
        cards_frame.grid(row=1, column=0, sticky="nsew")
        for i in range(6):
            cards_frame.grid_columnconfigure(i, weight=1)

        self.card_blinks = StatusCard(cards_frame, "Blink Count", "0", "👁")
        self.card_eye_dir = StatusCard(cards_frame, "Eye Direction", "Center", "➡")
        self.card_head_pos = StatusCard(cards_frame, "Head Position", "Normal", "🧭")
        self.card_warnings = StatusCard(cards_frame, "Warnings", "0", "⚠")
        self.card_fraud_score = StatusCard(cards_frame, "Fraud Score", "0", "📊")
        self.card_timer = StatusCard(cards_frame, "Timer", "00:00:00", "⏱")

        cards = [self.card_blinks, self.card_eye_dir, self.card_head_pos,
                 self.card_warnings, self.card_fraud_score, self.card_timer]
        for i, card in enumerate(cards):
            card.grid(row=0, column=i, sticky="nsew", padx=6)

    # ------------------------------------------------------------------
    # LIFECYCLE
    # ------------------------------------------------------------------
    def load_student(self, student):
        """Called by the App controller right before this screen is shown."""
        self.student = student
        self.exam_controller = ExamController(self.controller.db, student)
        self.exam_controller.set_max_warnings_callback(self._on_max_warnings_hit)
        self._max_warnings_dialog_shown = False

        self.detail_labels["Name"].configure(text=student.name)
        self.detail_labels["Register No."].configure(text=student.register_number)
        self.detail_labels["Department"].configure(text=student.department)
        self.detail_labels["Subject"].configure(text=student.subject)

        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.report_button.configure(state="disabled")
        self._reset_cards()

    def _reset_cards(self):
        self.card_blinks.set_value("0")
        self.card_eye_dir.set_value("Center")
        self.card_head_pos.set_value("Normal")
        self.card_warnings.set_value("0")
        self.card_fraud_score.set_value("0")
        self.card_timer.set_value("00:00:00")
        for card in (self.card_eye_dir, self.card_head_pos, self.card_warnings,
                     self.card_fraud_score):
            card.set_status_level("OK")

    # ------------------------------------------------------------------
    # MONITORING CONTROLS
    # ------------------------------------------------------------------
    def _on_start_monitoring(self):
        if self.exam_controller is None:
            return

        started = self.exam_controller.start_exam()
        if not started:
            messagebox.showerror(
                "Camera Error",
                "Could not access the webcam. Please check that it is connected "
                "and not being used by another application.",
            )
            return

        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.report_button.configure(state="disabled")

        self._poll_job = self.after(_POLL_INTERVAL_MS, self._poll_loop)
        logger.info("Monitoring UI loop started.")

    def _poll_loop(self):
        if self.exam_controller is None or not self.exam_controller.is_active:
            return

        result = self.exam_controller.poll()
        if result is not None:
            self._update_feed(result)
            self._update_cards(result)

            if result.analysis.new_warning is not None:
                self.warning_toast.show(result.analysis.new_warning.message)

        self.card_timer.set_value(self.exam_controller.timer.elapsed_formatted())

        self._poll_job = self.after(_POLL_INTERVAL_MS, self._poll_loop)

    def _update_feed(self, result):
        pil_image = Image.fromarray(result.frame_rgb)
        ctk_image = ctk.CTkImage(
            light_image=pil_image, dark_image=pil_image,
            size=(CAMERA_WIDTH, CAMERA_HEIGHT),
        )
        self.feed_label.configure(image=ctk_image, text="")
        self.feed_label.image = ctk_image  # keep a reference alive

    def _update_cards(self, result):
        analysis = result.analysis

        self.card_blinks.set_value(analysis.blink_count)
        self.card_eye_dir.set_value(analysis.gaze_direction.title())
        self.card_head_pos.set_value(analysis.head_direction.title())
        self.card_warnings.set_value(self.exam_controller.warning_count)
        self.card_fraud_score.set_value(f"{analysis.fraud_score}")

        self.card_eye_dir.set_status_level("OK" if analysis.gaze_direction == "CENTER" else "CAUTION")
        self.card_head_pos.set_status_level("OK" if analysis.head_direction == "NORMAL" else "CAUTION")
        self.card_warnings.set_status_level(
            "DANGER" if self.exam_controller.warning_count >= MAX_WARNINGS_ALLOWED else
            ("CAUTION" if self.exam_controller.warning_count > 0 else "OK")
        )
        self.card_fraud_score.set_status_level(
            "DANGER" if analysis.fraud_score >= 60 else
            ("CAUTION" if analysis.fraud_score >= 30 else "OK")
        )

    def _on_max_warnings_hit(self):
        if self._max_warnings_dialog_shown:
            return
        self._max_warnings_dialog_shown = True
        MaxWarningsDialog(self, on_end_exam=self._on_stop_monitoring)

    def _on_stop_monitoring(self):
        if self._poll_job is not None:
            self.after_cancel(self._poll_job)
            self._poll_job = None

        if self.exam_controller is None or not self.exam_controller.is_active:
            return

        summary = self.exam_controller.stop_exam()

        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="disabled")
        self.report_button.configure(state="normal")

        self._last_summary = summary
        messagebox.showinfo(
            "Exam Ended",
            f"Exam completed.\n\nResult: {summary.result}\n"
            f"Fraud Score: {summary.fraud_score}/100\n"
            f"Warnings: {summary.total_warnings}",
        )

    def _on_view_report(self):
        if self.student is None:
            return
        self.controller.show_report(self.student)

    def _on_exit(self):
        if self.exam_controller is not None and self.exam_controller.is_active:
            confirm = messagebox.askyesno(
                "Exit", "An exam is currently in progress. Stop it and exit?"
            )
            if not confirm:
                return
            self._on_stop_monitoring()

        if self.exam_controller is not None:
            self.exam_controller.close()

        self.controller.quit_app()
