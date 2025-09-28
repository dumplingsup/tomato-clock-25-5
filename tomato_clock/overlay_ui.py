"""Overlay GUI for Pomodoro timer with system tray integration."""

import time
import threading
import os
from typing import Optional, Any

from .core import PomodoroTimer, TimerState, Phase
from .config import PomodoroConfig
from .notifications import NotificationManager
from .utils import get_logger

logger = get_logger(__name__)

# Optional GUI imports - gracefully handle missing dependencies
try:
    import tkinter as tk
    from tkinter import ttk
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False
    logger.warning("tkinter not available - overlay GUI disabled")

try:
    from PIL import Image, ImageDraw
    import pystray
    import itertools
    HAS_TRAY_SUPPORT = True
except ImportError:
    HAS_TRAY_SUPPORT = False
    logger.warning("PIL/pystray not available - system tray disabled")

DEBUG = bool(os.environ.get('TOMATO_DEBUG'))


class OverlayUI:
    """GUI overlay for Pomodoro timer with system tray integration."""
    
    def __init__(self, config: PomodoroConfig):
        if not HAS_TKINTER:
            raise ImportError("tkinter is required for overlay GUI")
        
        self.config = config
        self.root = tk.Tk()
        self.setup_window()
        
        # Timer state
        self.is_paused = False
        
        # Tray icon support
        self.tray_icon: Optional[Any] = None
        self.tray_ready = threading.Event()
        self.hidden = False
        
        # Pre-warning state
        self.pre_notice_sent = False
        
        # Setup notification manager with tray support
        self.notification_manager = NotificationManager(
            config.enable_notifications, 
            config.enable_balloon
        )
        
        # Setup timer with callbacks
        self.timer = PomodoroTimer(config, self.notification_manager)
        self._setup_callbacks()
        
        # Start UI components
        self._create_ui_elements()
        self._start_tray_thread()
        
        # Start timer in background
        self.timer_thread = threading.Thread(target=self.timer.start, daemon=True)
        self.timer_thread.start()
    
    def setup_window(self) -> None:
        """Setup the main overlay window."""
        self.root.title("番茄钟")
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)  # Remove window decorations
        self.root.attributes('-alpha', self.config.alpha)
        
        # Calculate window size based on scale
        base_width, base_height = 280, 120
        width = int(base_width * self.config.scale)
        height = int(base_height * self.config.scale)
        
        # Position window (top-right corner)
        x = self.root.winfo_screenwidth() - width - 20
        y = 20
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        
        # Configure for dragging
        self.root.bind('<Button-1>', self._start_drag)
        self.root.bind('<B1-Motion>', self._drag_window)
    
    def _create_ui_elements(self) -> None:
        """Create UI elements."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.bind('<Button-1>', self._start_drag)
        main_frame.bind('<B1-Motion>', self._drag_window)
        
        # Phase and cycle label
        self.phase_label = ttk.Label(main_frame, text="准备开始...", font=('Arial', 12, 'bold'))
        self.phase_label.pack(pady=5)
        self.phase_label.bind('<Button-1>', self._start_drag)
        self.phase_label.bind('<B1-Motion>', self._drag_window)
        
        # Time label
        self.time_label = ttk.Label(main_frame, text="00:00", font=('Arial', 16))
        self.time_label.pack(pady=2)
        self.time_label.bind('<Button-1>', self._start_drag)
        self.time_label.bind('<B1-Motion>', self._drag_window)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(main_frame, mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.pause_button = ttk.Button(button_frame, text="暂停", command=self._toggle_pause)
        self.pause_button.pack(side=tk.LEFT, padx=2)
        
        self.skip_button = ttk.Button(button_frame, text="跳过", command=self._skip_phase)
        self.skip_button.pack(side=tk.LEFT, padx=2)
        
        self.close_button = ttk.Button(button_frame, text="关闭", command=self._close_window)
        self.close_button.pack(side=tk.RIGHT, padx=2)
        
        # Configure progress bar styles
        style = ttk.Style()
        style.configure('Work.Horizontal.TProgressbar', background='red')
        style.configure('Rest.Horizontal.TProgressbar', background='green')
    
    def _setup_callbacks(self) -> None:
        """Setup timer callbacks for UI updates."""
        self.timer.add_callback('tick', self._on_tick)
        self.timer.add_callback('phase_start', self._on_phase_start)
        self.timer.add_callback('phase_end', self._on_phase_end)
        self.timer.add_callback('timer_complete', self._on_timer_complete)
        self.timer.add_callback('pre_rest_warning', self._on_pre_rest_warning)
    
    def _on_tick(self, state: TimerState) -> None:
        """Handle timer tick updates."""
        self.root.after(0, lambda: self._update_display(state))
        
        # Update tray icon
        if HAS_TRAY_SUPPORT and self.tray_icon:
            self._update_tray_icon(state)
    
    def _on_phase_start(self, state: TimerState) -> None:
        """Handle phase start."""
        self.pre_notice_sent = False
        self.root.after(0, lambda: self._update_phase_display(state))
        if HAS_TRAY_SUPPORT:
            self.root.after(0, self._rebuild_tray_menu)
    
    def _on_phase_end(self, state: TimerState) -> None:
        """Handle phase end."""
        if HAS_TRAY_SUPPORT:
            self.root.after(0, self._rebuild_tray_menu)
    
    def _on_timer_complete(self, state: TimerState) -> None:
        """Handle timer completion."""
        self.root.after(0, self._close_window)
    
    def _on_pre_rest_warning(self, state: TimerState) -> None:
        """Handle pre-rest warning."""
        self.pre_notice_sent = True
    
    def _update_display(self, state: TimerState) -> None:
        """Update the display with current timer state."""
        # Update time
        minutes = state.remaining_seconds // 60
        seconds = state.remaining_seconds % 60
        self.time_label.config(text=f"{minutes:02d}:{seconds:02d}")
        
        # Update progress bar
        self.progress_bar.config(value=state.progress * 100, maximum=100)
        
        # Check for pre-rest warning
        if (state.phase == Phase.REST and not self.pre_notice_sent and 
            state.remaining_seconds <= self.config.pre_rest_warning and 
            state.remaining_seconds > 0):
            if self.notification_manager:
                message = f"休息即将结束 (剩余~{state.remaining_seconds}s)"
                self.notification_manager.notify('番茄钟', message)
            self.pre_notice_sent = True
    
    def _update_phase_display(self, state: TimerState) -> None:
        """Update phase-specific display elements."""
        phase_text = f"第{state.cycle}轮 - {state.phase.value}"
        self.phase_label.config(text=phase_text)
        
        # Update progress bar style
        if state.phase == Phase.WORK:
            self.progress_bar.config(style='Work.Horizontal.TProgressbar')
        else:
            self.progress_bar.config(style='Rest.Horizontal.TProgressbar')
    
    def _toggle_pause(self) -> None:
        """Toggle pause/resume."""
        if self.is_paused:
            self.timer.resume()
            self.pause_button.config(text="暂停")
        else:
            self.timer.pause()
            self.pause_button.config(text="恢复")
        self.is_paused = not self.is_paused
        
        if HAS_TRAY_SUPPORT:
            self._rebuild_tray_menu()
    
    def _skip_phase(self) -> None:
        """Skip current phase."""
        self.timer.skip_phase()
    
    def _close_window(self) -> None:
        """Close the overlay window."""
        self.timer.stop()
        if HAS_TRAY_SUPPORT and self.tray_icon:
            self.tray_icon.stop()
        self.root.destroy()
    
    def _start_drag(self, event) -> None:
        """Start window dragging."""
        self.root.start_x = event.x
        self.root.start_y = event.y
    
    def _drag_window(self, event) -> None:
        """Handle window dragging."""
        x = self.root.winfo_x() + event.x - self.root.start_x
        y = self.root.winfo_y() + event.y - self.root.start_y
        self.root.geometry(f"+{x}+{y}")
    
    def _start_tray_thread(self) -> None:
        """Start system tray thread if supported."""
        if HAS_TRAY_SUPPORT:
            self.tray_thread = threading.Thread(target=self._init_tray, daemon=True)
            self.tray_thread.start()
    
    def _init_tray(self) -> None:
        """Initialize system tray icon."""
        if not HAS_TRAY_SUPPORT:
            return
        
        try:
            # Create tray icon
            icon_image = self._create_tray_icon()
            menu = self._build_tray_menu()
            
            self.tray_icon = pystray.Icon("tomato_clock", icon_image, "番茄钟", menu)
            
            # Set tray reference for notifications
            self.notification_manager.set_tray_reference(self.tray_icon)
            
            self.tray_ready.set()
            self.tray_icon.run()
        except Exception as e:
            logger.error(f"Failed to initialize tray icon: {e}")
    
    def _create_tray_icon(self) -> Any:
        """Create tray icon image.""" 
        if not HAS_TRAY_SUPPORT:
            return None
        
        # Create a simple red circle icon
        size = (64, 64)
        image = Image.new('RGBA', size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse([8, 8, 56, 56], fill='red', outline='darkred')
        return image
    
    def _build_tray_menu(self) -> Any:
        """Build tray context menu."""
        if not HAS_TRAY_SUPPORT:
            return None
        
        pause_text = '恢复' if self.is_paused else '暂停'
        show_text = '显示' if self.hidden else '隐藏'
        
        return pystray.Menu(
            pystray.MenuItem(pause_text, self._tray_toggle_pause),
            pystray.MenuItem(show_text, self._tray_toggle_show),
            pystray.MenuItem('跳过阶段', self._tray_skip_phase),
            pystray.MenuItem('重置', self._tray_reset),
            pystray.MenuItem('退出', self._tray_quit)
        )
    
    def _tray_toggle_pause(self, icon, item) -> None:
        """Tray menu: toggle pause."""
        self.root.after(0, self._toggle_pause)
        self.root.after(0, self._rebuild_tray_menu)
    
    def _tray_toggle_show(self, icon, item) -> None:
        """Tray menu: toggle show/hide window."""
        def toggle():
            if self.hidden:
                self.root.deiconify()
                self.hidden = False
            else:
                self.root.withdraw()
                self.hidden = True
        
        self.root.after(0, toggle)
        self.root.after(0, self._rebuild_tray_menu)
    
    def _tray_skip_phase(self, icon, item) -> None:
        """Tray menu: skip phase."""
        self.root.after(0, self._skip_phase)
    
    def _tray_reset(self, icon, item) -> None:
        """Tray menu: reset timer."""
        # Not implemented in this version - would need timer reset functionality
        pass
    
    def _tray_quit(self, icon, item) -> None:
        """Tray menu: quit application."""
        self.root.after(0, self._close_window)
    
    def _rebuild_tray_menu(self) -> None:
        """Rebuild tray menu with current state."""
        if HAS_TRAY_SUPPORT and self.tray_icon:
            self.tray_icon.menu = self._build_tray_menu()
    
    def _update_tray_icon(self, state: TimerState) -> None:
        """Update tray icon based on current state."""
        # Simple implementation - could be enhanced with progress indication
        pass
    
    def run(self) -> None:
        """Run the overlay UI."""
        try:
            self.config.validate()
        except ValueError as e:
            logger.error(f"配置错误: {e}")
            return
        
        logger.info("启动番茄钟覆盖层界面")
        self.root.mainloop()


def main() -> None:
    """Main entry point for overlay version."""
    if not HAS_TKINTER:
        print("错误：需要 tkinter 支持才能运行覆盖层界面")
        print("请安装 python3-tk 包或使用终端版本")
        return
    
    try:
        config = PomodoroConfig.from_overlay_args()
        ui = OverlayUI(config)
        ui.run()
    except KeyboardInterrupt:
        print("\n用户中断程序")
    except Exception as e:
        logger.error(f"程序错误: {e}")


if __name__ == '__main__':
    main()