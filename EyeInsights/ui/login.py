"""
ui/login.py
-----------
Student login / exam-entry screen for Eye Insights.

Collects:
- Student Name
- Register Number
- Department
- Subject

Validates the information, saves the student to SQLite,
and opens the dashboard.
"""

import customtkinter as ctk

from config import (
    COLOR_BACKGROUND,
    COLOR_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_SUBTITLE,
)

from database.models import Student

from ui.styles import (
    card_frame_kwargs,
    primary_button_kwargs,
    title_label_kwargs,
)

from ui.widgets import (
    LabeledDropdown,
    LabeledEntry,
)

from utils.helper import (
    validate_non_empty,
    validate_register_number,
)

from utils.logger import get_logger


logger = get_logger("LoginScreen")


# ---------------------------------------------------------
# DEPARTMENTS
# ---------------------------------------------------------

DEPARTMENTS = [
    "Computer Science",
    "Information Technology",
    "Electronics & Communication",
    "Electrical Engineering",
    "Mechanical Engineering",
    "Civil Engineering",
    "Other",
]


# ---------------------------------------------------------
# LOGIN SCREEN
# ---------------------------------------------------------

class LoginScreen(ctk.CTkFrame):

    def __init__(self, master, controller):

        super().__init__(
            master,
            fg_color=COLOR_BACKGROUND
        )

        self.controller = controller

        self._build_layout()


    # -----------------------------------------------------
    # BUILD UI
    # -----------------------------------------------------

    def _build_layout(self):

        # Main center container
        outer = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        outer.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )


        # -------------------------------------------------
        # LOGIN CARD
        # -------------------------------------------------

        card = ctk.CTkFrame(
            outer,
            width=460,
            height=650,
            **card_frame_kwargs()
        )

        card.pack(
            padx=20,
            pady=20
        )

        card.pack_propagate(False)


        # -------------------------------------------------
        # HEADER
        # -------------------------------------------------

        header = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        header.pack(
            fill="x",
            padx=36,
            pady=(30, 10)
        )


        # Logo
        logo_circle = ctk.CTkLabel(
            header,
            text="EI",
            font=("Arial", 26, "bold"),
            fg_color=COLOR_PRIMARY,
            text_color="white",
            width=64,
            height=64,
            corner_radius=32,
        )

        logo_circle.pack()


        # Application title
        title = ctk.CTkLabel(
            header,
            text="Eye Insights",
            **title_label_kwargs()
        )

        title.pack(
            pady=(12, 0)
        )


        # Subtitle
        subtitle = ctk.CTkLabel(
            header,
            text="AI Based Exam Fraud Detection System",
            font=FONT_SUBTITLE,
            text_color=COLOR_TEXT_SECONDARY,
        )

        subtitle.pack(
            pady=(3, 5)
        )


        # -------------------------------------------------
        # FORM
        # -------------------------------------------------

        form = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        form.pack(
            fill="both",
            expand=True,
            padx=36,
            pady=10
        )


        # Student Name
        self.name_field = LabeledEntry(
            form,
            "Student Name",
            placeholder="e.g. Ananya Sharma"
        )

        self.name_field.pack(
            fill="x",
            pady=7
        )


        # Register Number
        self.register_field = LabeledEntry(
            form,
            "Register Number",
            placeholder="e.g. 21CS1042"
        )

        self.register_field.pack(
            fill="x",
            pady=7
        )


        # Department
        self.department_field = LabeledDropdown(
            form,
            "Department",
            DEPARTMENTS
        )

        self.department_field.pack(
            fill="x",
            pady=7
        )


        # Subject
        self.subject_field = LabeledEntry(
            form,
            "Subject",
            placeholder="e.g. Data Structures"
        )

        self.subject_field.pack(
            fill="x",
            pady=7
        )


        # -------------------------------------------------
        # ERROR MESSAGE
        # -------------------------------------------------

        self.error_label = ctk.CTkLabel(
            form,
            text="",
            text_color="#C62828",
            font=FONT_SUBTITLE
        )

        self.error_label.pack(
            fill="x",
            pady=(5, 0)
        )


        # -------------------------------------------------
        # ACTION BUTTON
        # -------------------------------------------------

        actions = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )

        actions.pack(
            fill="x",
            padx=36,
            pady=(5, 30)
        )


        self.start_button = ctk.CTkButton(
            actions,
            text="Start Exam",
            command=self._on_start_clicked,
            **primary_button_kwargs()
        )

        self.start_button.pack(
            fill="x"
        )


        # IMPORTANT:
        # Do NOT use:
        #
        # self.bind_all(...)
        #
        # CustomTkinter does not allow bind_all on CTk widgets.
        #
        # Bind Enter directly to the root application instead.

        try:
            self.controller.bind(
                "<Return>",
                self._on_enter_pressed
            )
        except Exception as exc:
            logger.warning(
                f"Could not bind Enter key: {exc}"
            )


    # -----------------------------------------------------
    # ENTER KEY
    # -----------------------------------------------------

    def _on_enter_pressed(self, event=None):

        self._on_start_clicked()


    # -----------------------------------------------------
    # START EXAM
    # -----------------------------------------------------

    def _on_start_clicked(self):

        # Read form values
        name = self.name_field.get().strip()

        register_number = (
            self.register_field
            .get()
            .strip()
        )

        department = (
            self.department_field
            .get()
            .strip()
        )

        subject = (
            self.subject_field
            .get()
            .strip()
        )


        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not validate_non_empty(name):

            self._show_error(
                "Please enter the student's name."
            )

            return


        if not validate_register_number(
            register_number
        ):

            self._show_error(
                "Register number must be "
                "4-20 alphanumeric characters."
            )

            return


        if not validate_non_empty(department):

            self._show_error(
                "Please select a department."
            )

            return


        if not validate_non_empty(subject):

            self._show_error(
                "Please enter the exam subject."
            )

            return


        # -------------------------------------------------
        # CREATE STUDENT
        # -------------------------------------------------

        student = Student(
            id=None,
            name=name,
            register_number=register_number,
            department=department,
            subject=subject,
        )


        # -------------------------------------------------
        # SAVE TO DATABASE
        # -------------------------------------------------

        try:

            student_id = (
                self.controller.db
                .add_student(student)
            )

            student.id = student_id

            logger.info(
                f"Student created: "
                f"{register_number}"
            )


        except Exception as exc:

            logger.error(
                f"Failed to save student: {exc}"
            )

            self._show_error(
                "Could not save student details. "
                "Please try again."
            )

            return


        # -------------------------------------------------
        # OPEN DASHBOARD
        # -------------------------------------------------

        self._show_error("")

        try:

            self.controller.show_dashboard(
                student
            )

        except Exception as exc:

            logger.error(
                f"Failed to open dashboard: {exc}"
            )

            self._show_error(
                "Dashboard could not be opened."
            )


    # -----------------------------------------------------
    # ERROR DISPLAY
    # -----------------------------------------------------

    def _show_error(
        self,
        message: str
    ):

        self.error_label.configure(
            text=message
        )


    # -----------------------------------------------------
    # RESET LOGIN FORM
    # -----------------------------------------------------

    def reset_form(self):

        try:

            self.name_field.entry.delete(
                0,
                "end"
            )

            self.register_field.entry.delete(
                0,
                "end"
            )

            self.subject_field.entry.delete(
                0,
                "end"
            )

            self.error_label.configure(
                text=""
            )

        except Exception as exc:

            logger.warning(
                f"Could not reset login form: {exc}"
            )