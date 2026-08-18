"""
ui/styles.py
------------
Small helpers that centralise CustomTkinter styling keyword-argument
bundles, so every screen looks consistent without repeating the same
color/font dictionaries everywhere.
"""

import customtkinter as ctk

from config import (
    COLOR_ACCENT,
    COLOR_BORDER,
    COLOR_DANGER,
    COLOR_PRIMARY,
    COLOR_PRIMARY_DARK,
    COLOR_SUCCESS,
    COLOR_SURFACE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_WARNING,
    FONT_BODY,
    FONT_BUTTON,
    FONT_HEADING,
    FONT_TITLE,
)


def primary_button_kwargs():
    return dict(
        fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_DARK,
        text_color="white", font=FONT_BUTTON, corner_radius=10, height=42,
    )


def danger_button_kwargs():
    return dict(
        fg_color=COLOR_DANGER, hover_color="#8E1F1F",
        text_color="white", font=FONT_BUTTON, corner_radius=10, height=42,
    )


def secondary_button_kwargs():
    return dict(
        fg_color="transparent", hover_color="#E3F2FD",
        text_color=COLOR_PRIMARY, border_width=2, border_color=COLOR_PRIMARY,
        font=FONT_BUTTON, corner_radius=10, height=42,
    )


def card_frame_kwargs():
    return dict(fg_color=COLOR_SURFACE, corner_radius=14, border_width=1,
                border_color=COLOR_BORDER)


def title_label_kwargs():
    return dict(text_color=COLOR_PRIMARY_DARK, font=FONT_TITLE)


def heading_label_kwargs():
    return dict(text_color=COLOR_TEXT_PRIMARY, font=FONT_HEADING)


def body_label_kwargs():
    return dict(text_color=COLOR_TEXT_SECONDARY, font=FONT_BODY)


def entry_kwargs():
    return dict(
        corner_radius=8, border_color=COLOR_BORDER, border_width=1,
        fg_color="white", text_color=COLOR_TEXT_PRIMARY, height=40, font=FONT_BODY,
    )


def status_level_color(level: str) -> str:
    return {
        "OK": COLOR_SUCCESS,
        "CAUTION": COLOR_WARNING,
        "DANGER": COLOR_DANGER,
    }.get(level, COLOR_ACCENT)


def apply_theme():
    """Apply the global CustomTkinter appearance settings."""
    from config import APPEARANCE_MODE, COLOR_THEME
    ctk.set_appearance_mode(APPEARANCE_MODE)
    ctk.set_default_color_theme(COLOR_THEME)
