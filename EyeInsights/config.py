"""
config.py
----------
Central configuration file for Eye Insights.
Holds colors, thresholds, window sizes, camera settings and paths.
Every other module imports from here so that behaviour can be tuned
in a single place without touching business logic.
"""

import os

# ----------------------------------------------------------------------
# BASE PATHS
# ----------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

ASSETS_DIR = os.path.join(BASE_DIR, "assets")
ICONS_DIR = os.path.join(ASSETS_DIR, "icons")
IMAGES_DIR = os.path.join(ASSETS_DIR, "images")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")

MODELS_DIR = os.path.join(BASE_DIR, "models")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

DATABASE_PATH = os.path.join(BASE_DIR, "eye_insights.db")

# Make sure all runtime folders exist as soon as config is imported.
for _folder in (ASSETS_DIR, ICONS_DIR, IMAGES_DIR, SOUNDS_DIR, MODELS_DIR,
                 REPORTS_DIR, SCREENSHOTS_DIR, LOGS_DIR):
    os.makedirs(_folder, exist_ok=True)

# ----------------------------------------------------------------------
# WINDOW SETTINGS
# ----------------------------------------------------------------------
APP_NAME = "Eye Insights - AI Based Exam Fraud Detection"
APP_VERSION = "1.0.0"

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 720
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 640

APPEARANCE_MODE = "light"          # "light" | "dark" | "system"
COLOR_THEME = "blue"               # base CustomTkinter theme

# ----------------------------------------------------------------------
# COLOR PALETTE (Blue - White professional theme)
# ----------------------------------------------------------------------
COLOR_PRIMARY = "#1565C0"          # deep blue
COLOR_PRIMARY_DARK = "#0D47A1"
COLOR_PRIMARY_LIGHT = "#42A5F5"
COLOR_ACCENT = "#00ACC1"
COLOR_BACKGROUND = "#F4F7FB"
COLOR_SURFACE = "#FFFFFF"
COLOR_TEXT_PRIMARY = "#102A43"
COLOR_TEXT_SECONDARY = "#486581"
COLOR_SUCCESS = "#2E7D32"
COLOR_WARNING = "#F9A825"
COLOR_DANGER = "#C62828"
COLOR_BORDER = "#D9E2EC"

# ----------------------------------------------------------------------
# CAMERA SETTINGS
# ----------------------------------------------------------------------
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS_TARGET = 30

# ----------------------------------------------------------------------
# MEDIAPIPE FACE MESH SETTINGS
# ----------------------------------------------------------------------
MAX_NUM_FACES = 2                  # detect up to 2 so "multiple faces" can be flagged
FACEMESH_REFINE_LANDMARKS = True
MIN_DETECTION_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5

# ----------------------------------------------------------------------
# EYE / BLINK THRESHOLDS
# ----------------------------------------------------------------------
EAR_BLINK_THRESHOLD = 0.21         # below this -> eye considered closed
EAR_CONSEC_FRAMES = 2              # consecutive frames below threshold to count a blink
EYES_CLOSED_ALERT_SECONDS = 3.0    # eyes closed continuously longer than this -> suspicious

# Horizontal / vertical gaze ratio thresholds (0.0 - 1.0 across eye width/height)
GAZE_LEFT_THRESHOLD = 0.38
GAZE_RIGHT_THRESHOLD = 0.62
GAZE_UP_THRESHOLD = 0.38
GAZE_DOWN_THRESHOLD = 0.65

# ----------------------------------------------------------------------
# HEAD POSE THRESHOLDS (degrees)
# ----------------------------------------------------------------------
HEAD_YAW_LEFT_THRESHOLD = -15.0
HEAD_YAW_RIGHT_THRESHOLD = 15.0
HEAD_PITCH_DOWN_THRESHOLD = 12.0
HEAD_PITCH_UP_THRESHOLD = -12.0

# ----------------------------------------------------------------------
# FRAUD ENGINE SETTINGS
# ----------------------------------------------------------------------
FRAUD_SCORE_MAX = 100

FRAUD_POINTS_LOOK_LEFT = 3
FRAUD_POINTS_LOOK_RIGHT = 3
FRAUD_POINTS_LOOK_DOWN = 4
FRAUD_POINTS_FACE_MISSING = 6
FRAUD_POINTS_MULTIPLE_FACES = 10
FRAUD_POINTS_EYES_CLOSED_LONG = 5
FRAUD_POINTS_HEAD_TURNED = 4

# Minimum seconds between two warnings of the SAME type (avoid spamming)
WARNING_COOLDOWN_SECONDS = 4.0

# A sustained violation must last at least this long (seconds) before it
# is counted as a genuine event rather than a single noisy frame.
VIOLATION_MIN_DURATION = 1.0

MAX_WARNINGS_ALLOWED = 8            # exam auto-flagged as "Fraud Suspected" after this
FRAUD_SCORE_FAIL_THRESHOLD = 60     # fraud score >= this -> result = Fail / Suspicious

# ----------------------------------------------------------------------
# SCREENSHOT SETTINGS
# ----------------------------------------------------------------------
SCREENSHOT_ON_WARNING = True
SCREENSHOT_JPEG_QUALITY = 90

# ----------------------------------------------------------------------
# TIMER / EXAM SETTINGS
# ----------------------------------------------------------------------
DEFAULT_EXAM_DURATION_MINUTES = 60

# ----------------------------------------------------------------------
# FONTS
# ----------------------------------------------------------------------
FONT_FAMILY = "Segoe UI"
FONT_TITLE = (FONT_FAMILY, 26, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 15, "normal")
FONT_HEADING = (FONT_FAMILY, 18, "bold")
FONT_BODY = (FONT_FAMILY, 13, "normal")
FONT_SMALL = (FONT_FAMILY, 11, "normal")
FONT_BUTTON = (FONT_FAMILY, 14, "bold")
FONT_CARD_VALUE = (FONT_FAMILY, 22, "bold")
FONT_CARD_LABEL = (FONT_FAMILY, 12, "normal")
