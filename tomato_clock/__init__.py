"""
Tomato Clock - A Pomodoro Timer Package

This package provides both terminal and GUI-based Pomodoro timer functionality
with notifications, customizable intervals, and system tray integration.
"""

__version__ = "1.0.0"
__author__ = "dumplingsup"
__email__ = "95017643+dumplingsup@users.noreply.github.com"

from .core import PomodoroTimer
from .config import PomodoroConfig
from .notifications import NotificationManager

__all__ = ['PomodoroTimer', 'PomodoroConfig', 'NotificationManager']