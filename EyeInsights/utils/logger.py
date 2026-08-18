"""
utils/logger.py
----------------
Application-wide logging utility. Every subsystem (camera, AI engine,
database, UI) imports get_logger() so events are timestamped and
written both to console and to a rotating log file under /logs.
"""

import logging
import os
import sys
from datetime import datetime

from config import LOGS_DIR

_LOG_FILE = os.path.join(LOGS_DIR, f"session_{datetime.now().strftime('%Y%m%d')}.log")

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_configured = False


def _configure_root():
    """Configure the root logger once for the whole application."""
    global _configured
    if _configured:
        return

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a named logger that writes to the shared log file."""
    _configure_root()
    return logging.getLogger(name)
