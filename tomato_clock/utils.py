"""Utility functions and helpers for Tomato Clock."""

import logging
import platform
import shutil
import sys
from typing import Tuple


# ANSI color codes
class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\x1b[0m'
    WORK = '\x1b[38;5;208m'     # orange
    REST = '\x1b[38;5;42m'      # green
    BAR_FILL = '\x1b[38;5;33m'  # blue
    BAR_EMPTY = '\x1b[38;5;240m'  # grey


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def enable_windows_ansi() -> None:
    """Enable ANSI color support on Windows terminals."""
    if platform.system() == 'Windows':
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE = -11
            mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                new_mode = mode.value | 0x0004  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
                kernel32.SetConsoleMode(handle, new_mode)
        except Exception:
            pass


def beep() -> None:
    """Cross-platform beep sound."""
    print('\a', end='')


def get_terminal_size() -> Tuple[int, int]:
    """Get terminal size with fallback."""
    return shutil.get_terminal_size(fallback=(80, 20))


def format_time(seconds: int) -> str:
    """Format seconds as MM:SS."""
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def create_progress_bar(progress: float, width: int, use_ascii: bool = False, use_color: bool = False) -> str:
    """Create a progress bar string."""
    if width < 1:
        return ""
    
    full_block = '#' if use_ascii else '█'
    empty_block = '-' if use_ascii else '░'
    
    filled = int(width * progress)
    bar_fill = full_block * filled
    bar_empty = empty_block * (width - filled)
    
    if use_color and not use_ascii:
        return f"{Colors.BAR_FILL}{bar_fill}{Colors.RESET}{Colors.BAR_EMPTY}{bar_empty}{Colors.RESET}"
    else:
        return bar_fill + bar_empty


def safe_exit(code: int = 0) -> None:
    """Safe exit that works in different contexts."""
    try:
        sys.exit(code)
    except SystemExit:
        pass