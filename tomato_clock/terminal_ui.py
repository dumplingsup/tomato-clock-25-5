"""Terminal UI for Pomodoro timer."""

import sys
from typing import Optional

from .core import PomodoroTimer, TimerState, Phase
from .config import PomodoroConfig
from .notifications import NotificationManager
from .utils import (
    Colors, enable_windows_ansi, beep, get_terminal_size,
    format_time, create_progress_bar, get_logger
)

logger = get_logger(__name__)


class TerminalUI:
    """Terminal-based user interface for Pomodoro timer."""
    
    MAX_BAR_WIDTH = 30
    
    def __init__(self, config: PomodoroConfig):
        self.config = config
        self._prev_line_len = 0
        
        # Enable color support if requested
        if config.use_color:
            enable_windows_ansi()
        
        # Setup notification manager
        self.notification_manager = NotificationManager(config.enable_notifications)
        
        # Setup timer
        self.timer = PomodoroTimer(config, self.notification_manager)
        self._setup_callbacks()
    
    def _setup_callbacks(self) -> None:
        """Setup timer callbacks for UI updates."""
        self.timer.add_callback('tick', self._on_tick)
        self.timer.add_callback('phase_start', self._on_phase_start)
        self.timer.add_callback('phase_end', self._on_phase_end)
        self.timer.add_callback('timer_complete', self._on_timer_complete)
    
    def _on_tick(self, state: TimerState) -> None:
        """Handle timer tick updates."""
        self._update_display(state)
    
    def _on_phase_start(self, state: TimerState) -> None:
        """Handle phase start."""
        logger.info(f"开始{state.phase.value}：第{state.cycle}轮")
    
    def _on_phase_end(self, state: TimerState) -> None:
        """Handle phase end."""
        # Clear progress line
        self._clear_progress_line()
        
        # Show completion message
        if state.phase == Phase.WORK:
            message = f"第{state.cycle}轮 工作完成！去休息吧！"
        else:
            message = f"第{state.cycle}轮 休息结束！回来继续！"
        
        if self.config.use_color:
            color = Colors.WORK if state.phase == Phase.WORK else Colors.REST
            message = f"{color}{message}{Colors.RESET}"
        
        print(message)
        
        # Beep if enabled
        if self.config.enable_beep:
            beep()
    
    def _on_timer_complete(self, state: TimerState) -> None:
        """Handle timer completion."""
        self._clear_progress_line()
        print("已退出番茄钟。")
        print("感谢使用。")
    
    def _update_display(self, state: TimerState) -> None:
        """Update the terminal display with current state."""
        term_width, _ = get_terminal_size()
        
        # Format time
        time_str = format_time(state.remaining_seconds)
        
        # Create phase label with color if enabled
        phase_label = state.phase.value
        if self.config.use_color:
            color = Colors.WORK if state.phase == Phase.WORK else Colors.REST
            phase_label = f"{color}{state.phase.value}{Colors.RESET}"
        
        # Create prefix
        prefix = f"第{state.cycle}轮 {phase_label} | 剩余 {time_str} | "
        
        # Create percentage
        percent = f"{state.progress * 100:5.1f}%"
        suffix = ' ' + percent
        
        # Calculate available space for progress bar
        available_width = term_width - len(prefix) - len(suffix) - 1
        
        if available_width < 5:
            # Not enough space for progress bar
            message = f"第{state.cycle}轮 {phase_label} {time_str} {percent}"
        else:
            # Create progress bar
            bar_width = min(available_width, self.MAX_BAR_WIDTH)
            progress_bar = create_progress_bar(
                state.progress, bar_width, 
                self.config.use_ascii, self.config.use_color
            )
            message = prefix + progress_bar + suffix
        
        # Truncate if too long
        if len(message) > term_width:
            message = message[:term_width - 1]
        
        # Pad to clear previous line
        padded_message = message + ' ' * max(0, self._prev_line_len - len(message))
        
        # Print with carriage return (overwrite current line)
        print('\r' + padded_message, end='', flush=True)
        self._prev_line_len = len(message)
    
    def _clear_progress_line(self) -> None:
        """Clear the current progress line."""
        print('\r' + ' ' * self._prev_line_len + '\r', end='', flush=True)
        self._prev_line_len = 0
    
    def run(self) -> None:
        """Run the terminal UI."""
        # Validate configuration
        try:
            self.config.validate()
        except ValueError as e:
            print(f"配置错误: {e}")
            sys.exit(1)
        
        logger.info("启动番茄钟终端版本")
        
        # Start the timer
        self.timer.start()


def main() -> None:
    """Main entry point for terminal version."""
    try:
        config = PomodoroConfig.from_terminal_args()
        ui = TerminalUI(config)
        ui.run()
    except KeyboardInterrupt:
        print("\n用户中断程序")
    except Exception as e:
        logger.error(f"程序错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()