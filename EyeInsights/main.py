"""
main.py
-------
Application entry point for Eye Insights.
"""

import traceback
import customtkinter as ctk

from config import (
    APP_NAME,
    WINDOW_HEIGHT,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_WIDTH,
)

from database.database import Database
from ui.dashboard import DashboardScreen
from ui.login import LoginScreen
from ui.report import ReportScreen
from ui.styles import apply_theme
from utils.logger import get_logger

logger = get_logger("Main")


class EyeInsightsApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        print("Launching Eye Insights...")
        print("✓ App Started")

        apply_theme()
        print("✓ Theme Applied")

        self.title(APP_NAME)
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.protocol("WM_DELETE_WINDOW", self.quit_app)

        print("✓ Creating Database...")
        self.db = Database()
        print("✓ Database Created")

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        # ---------------- LOGIN ----------------

        try:
            print(">>> Creating LoginScreen...")
            self.login_screen = LoginScreen(self.container, self)
            print(">>> LoginScreen Created")

        except Exception as e:

            print("\n")
            print("=" * 70)
            print("LOGIN SCREEN FAILED")
            print("=" * 70)

            print("Exception Type : ", type(e).__name__)
            print("Exception      : ", str(e))

            print("\nFULL TRACEBACK\n")

            traceback.print_exc()

            print("=" * 70)

            input("Press ENTER to close...")

            raise

        # ---------------- DASHBOARD ----------------

        try:
            print(">>> Creating DashboardScreen...")
            self.dashboard_screen = DashboardScreen(self.container, self)
            print(">>> DashboardScreen Created")

        except Exception as e:

            print("\n")
            print("=" * 70)
            print("DASHBOARD FAILED")
            print("=" * 70)

            print("Exception Type : ", type(e).__name__)
            print("Exception      : ", str(e))

            traceback.print_exc()

            input("Press ENTER to close...")

            raise

        # ---------------- REPORT ----------------

        try:
            print(">>> Creating ReportScreen...")
            self.report_screen = ReportScreen(self.container, self)
            print(">>> ReportScreen Created")

        except Exception as e:

            print("\n")
            print("=" * 70)
            print("REPORT FAILED")
            print("=" * 70)

            print("Exception Type : ", type(e).__name__)
            print("Exception      : ", str(e))

            traceback.print_exc()

            input("Press ENTER to close...")

            raise

        for screen in (
            self.login_screen,
            self.dashboard_screen,
            self.report_screen,
        ):
            screen.grid(row=0, column=0, sticky="nsew")

        self.show_login()

        print("✓ Login Screen Visible")

        logger.info("Application Started Successfully")

    # ---------------- NAVIGATION ----------------

    def show_login(self):
        self.login_screen.reset_form()
        self.login_screen.tkraise()

    def show_dashboard(self, student, reset=True):

        if (
            reset
            or self.dashboard_screen.student is None
            or self.dashboard_screen.student.student_id != student.student_id
        ):
            self.dashboard_screen.load_student(student)

        self.dashboard_screen.tkraise()

    def show_report(self, student):
        self.report_screen.load_report(student)
        self.report_screen.tkraise()

    # ---------------- EXIT ----------------

    def quit_app(self):

        try:
            if self.dashboard_screen.exam_controller is not None:
                self.dashboard_screen.exam_controller.close()
        except Exception:
            pass

        try:
            self.db.close()
        except Exception:
            pass

        self.destroy()


def main():
    app = EyeInsightsApp()
    app.mainloop()


if __name__ == "__main__":
    main()