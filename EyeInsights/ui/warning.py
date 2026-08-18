"""
ui/warning.py
-------------
A transient warning toast/popup that appears on the dashboard whenever
the fraud engine raises a new warning, plus a modal dialog shown when
the maximum allowed warnings is exceeded.
"""

import customtkinter as ctk

from config import COLOR_DANGER, COLOR_WARNING, FONT_BODY, FONT_HEADING


class WarningToast(ctk.CTkFrame):
    """A small, self-dismissing banner shown at the top of the dashboard."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=COLOR_WARNING, corner_radius=10, **kwargs)

        self._message_var = ctk.StringVar(value="")
        self.label = ctk.CTkLabel(
            self, textvariable=self._message_var, font=FONT_BODY,
            text_color="white", anchor="w",
        )
        self.label.pack(fill="both", expand=True, padx=14, pady=8)

        self._hide_job = None
        self.place_forget()

    def show(self, message: str, duration_ms: int = 3500):
        """Display the toast with `message`, auto-hiding after `duration_ms`."""
        self._message_var.set(f"⚠  {message}")
        self.place(relx=0.5, rely=0.02, anchor="n")
        self.lift()

        if self._hide_job is not None:
            self.after_cancel(self._hide_job)
        self._hide_job = self.after(duration_ms, self.hide)

    def hide(self):
        self.place_forget()
        self._hide_job = None


class MaxWarningsDialog(ctk.CTkToplevel):
    """Modal dialog shown once the maximum warning count has been exceeded."""

    def __init__(self, master, on_end_exam):
        super().__init__(master)
        self.title("Exam Flagged")
        self.geometry("420x220")
        self.resizable(False, False)
        self.grab_set()

        ctk.CTkLabel(
            self, text="⚠  Maximum Warnings Exceeded",
            font=FONT_HEADING, text_color=COLOR_DANGER,
        ).pack(pady=(24, 8))

        ctk.CTkLabel(
            self,
            text="This exam session has been flagged for suspicious activity.\n"
                 "The exam will now be ended and a report generated.",
            font=FONT_BODY, wraplength=360, justify="center",
        ).pack(pady=8, padx=20)

        ctk.CTkButton(
            self, text="OK - End Exam", fg_color=COLOR_DANGER, hover_color="#8E1F1F",
            command=lambda: self._confirm(on_end_exam),
        ).pack(pady=16)

    def _confirm(self, on_end_exam):
        self.destroy()
        on_end_exam()
