"""
ui/widgets.py
-------------
Reusable custom widgets shared across screens: status cards for the
dashboard's live metrics, and a labeled input field for forms.
"""

import customtkinter as ctk

from config import (
    COLOR_BORDER,
    COLOR_SURFACE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_CARD_LABEL,
    FONT_CARD_VALUE,
)
from ui.styles import body_label_kwargs, entry_kwargs, status_level_color


class StatusCard(ctk.CTkFrame):
    """A small metric card: big value on top, label underneath."""

    def __init__(self, master, label: str, initial_value: str = "-", icon: str = "", **kwargs):
        super().__init__(master, fg_color=COLOR_SURFACE, corner_radius=12,
                          border_width=1, border_color=COLOR_BORDER, **kwargs)

        self._value_var = ctk.StringVar(value=initial_value)

        self.icon_label = ctk.CTkLabel(self, text=icon, font=("Segoe UI Emoji", 20))
        self.icon_label.pack(pady=(12, 0))

        self.value_label = ctk.CTkLabel(
            self, textvariable=self._value_var, font=FONT_CARD_VALUE, text_color=COLOR_TEXT_PRIMARY
        )
        self.value_label.pack(pady=(2, 0))

        self.desc_label = ctk.CTkLabel(
            self, text=label, font=FONT_CARD_LABEL, text_color=COLOR_TEXT_SECONDARY
        )
        self.desc_label.pack(pady=(0, 12))

    def set_value(self, value):
        self._value_var.set(str(value))

    def set_value_color(self, color: str):
        self.value_label.configure(text_color=color)

    def set_status_level(self, level: str):
        self.set_value_color(status_level_color(level))


class LabeledEntry(ctk.CTkFrame):
    """A form field: label above, styled entry below."""

    def __init__(self, master, label_text: str, placeholder: str = "", show=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.label = ctk.CTkLabel(self, text=label_text, anchor="w", **body_label_kwargs())
        self.label.pack(fill="x", pady=(0, 4))

        self.entry = ctk.CTkEntry(self, placeholder_text=placeholder, show=show, **entry_kwargs())
        self.entry.pack(fill="x")

    def get(self) -> str:
        return self.entry.get().strip()

    def set(self, value: str):
        self.entry.delete(0, "end")
        self.entry.insert(0, value)

    def focus(self):
        self.entry.focus_set()


class LabeledDropdown(ctk.CTkFrame):
    """A form field: label above, styled dropdown below."""

    def __init__(self, master, label_text: str, values, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.label = ctk.CTkLabel(self, text=label_text, anchor="w", **body_label_kwargs())
        self.label.pack(fill="x", pady=(0, 4))

        self._var = ctk.StringVar(value=values[0] if values else "")
        self.dropdown = ctk.CTkOptionMenu(self, values=values, variable=self._var, height=40)
        self.dropdown.pack(fill="x")

    def get(self) -> str:
        return self._var.get().strip()
