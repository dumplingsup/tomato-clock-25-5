"""Unified notification system for Tomato Clock."""

import time
import os
import platform
import atexit
from typing import Optional, Any
from .utils import get_logger

logger = get_logger(__name__)


class NotificationManager:
    """Unified notification manager for all types of notifications."""
    
    def __init__(self, enabled: bool = False, enable_balloon: bool = False):
        self.enabled = enabled
        self.enable_balloon = enable_balloon
        self._toaster: Optional[Any] = None
        self._fallback_ps = platform.system() == 'Windows'
        self._failed = False
        self.tray_ref: Optional[Any] = None  # Set by overlay when tray icon ready
        
        if enabled and platform.system() == 'Windows':
            self._initialize_windows_notifications()
        
        atexit.register(self._graceful_close)
    
    def _initialize_windows_notifications(self) -> None:
        """Initialize Windows toast notifications if available."""
        try:
            from win10toast import ToastNotifier  # type: ignore
            self._toaster = ToastNotifier()
        except ImportError:
            logger.debug("win10toast not available, using fallback methods")
            self._toaster = None
        except Exception as e:
            logger.warning(f"Failed to initialize ToastNotifier: {e}")
            self._toaster = None
    
    def _graceful_close(self) -> None:
        """Gracefully close notification system."""
        if self.enabled and self._toaster is not None and not self._failed:
            try:
                time.sleep(0.15)  # Allow threaded notifications to finish
            except Exception:
                pass
    
    def notify(self, title: str, message: str, duration: int = 5) -> None:
        """Send a notification with the given title and message."""
        if not self.enabled or self._failed:
            return
        
        # Try Windows toast notification first
        if self._try_toast_notification(title, message, duration):
            return
        
        # Try PowerShell BurntToast
        if self._try_powershell_notification(title, message):
            return
        
        # Try tray balloon notification
        if self._try_balloon_notification(title, message):
            return
        
        # Fallback to console output
        self._console_notification(title, message)
    
    def _try_toast_notification(self, title: str, message: str, duration: int) -> bool:
        """Try to send Windows toast notification."""
        if self._toaster is None:
            return False
        
        try:
            self._toaster.show_toast(title, message, duration=duration, threaded=False)
            return True
        except Exception as e:
            # Handle known Windows API errors
            if any(keyword in repr(e) for keyword in ['WNDPROC', 'LRESULT', 'WPARAM']):
                self._failed = True
            logger.warning(f"Toast notification failed: {e}")
            self._toaster = None
            return False
    
    def _try_powershell_notification(self, title: str, message: str) -> bool:
        """Try to send PowerShell BurntToast notification."""
        if not self._fallback_ps or self._failed:
            return False
        
        try:
            safe_title = title.replace("'", "''")
            safe_message = message.replace("'", "''")
            ps_script = (
                f"if (Get-Module -ListAvailable -Name BurntToast) "
                f"{{ New-BurntToastNotification -Text '{safe_title}', '{safe_message}'; }}"
            )
            result = os.system(f"powershell -NoProfile -ExecutionPolicy Bypass \"{ps_script}\" > NUL 2>&1")
            return result == 0
        except Exception as e:
            logger.warning(f"PowerShell notification failed: {e}")
            return False
    
    def _try_balloon_notification(self, title: str, message: str) -> bool:
        """Try to send tray balloon notification."""
        if not self.enable_balloon or self.tray_ref is None:
            return False
        
        try:
            self.tray_ref.notify(message, title=title)
            return True
        except Exception as e:
            logger.warning(f"Balloon notification failed: {e}")
            return False
    
    def _console_notification(self, title: str, message: str) -> None:
        """Fallback console notification."""
        try:
            print(f"\n[通知] {title}: {message}")
        except Exception:
            self._failed = True
    
    def set_tray_reference(self, tray_ref: Any) -> None:
        """Set reference to tray icon for balloon notifications."""
        self.tray_ref = tray_ref
    
    def is_available(self) -> bool:
        """Check if notification system is available and working."""
        return self.enabled and not self._failed