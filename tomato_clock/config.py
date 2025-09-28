"""Configuration management for Tomato Clock."""

import argparse
from dataclasses import dataclass
from typing import Optional


@dataclass
class PomodoroConfig:
    """Configuration class for Pomodoro timer settings."""
    
    # Timer settings
    work_minutes: float = 25.0
    rest_minutes: float = 5.0
    cycles: Optional[int] = None  # None for infinite
    
    # Display settings  
    use_ascii: bool = False
    use_color: bool = False
    tick: float = 1.0
    
    # Notification settings
    enable_notifications: bool = False
    enable_beep: bool = False
    pre_rest_warning: int = 30
    
    # GUI settings (for overlay)
    alpha: float = 0.95
    scale: float = 1.0
    enable_balloon: bool = False
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self.validate()
    
    def validate(self) -> None:
        """Validate configuration values."""
        if self.work_minutes <= 0:
            raise ValueError("工作时长必须为正数")
        if self.rest_minutes <= 0:
            raise ValueError("休息时长必须为正数")
        if self.tick < 0.05:
            self.tick = 0.05  # Minimum tick rate
        if not 0.0 <= self.alpha <= 1.0:
            raise ValueError("透明度必须在0-1之间")
        if self.scale <= 0:
            raise ValueError("缩放比例必须为正数")
        if self.pre_rest_warning < 0:
            raise ValueError("提前提醒时间不能为负数")
    
    @classmethod
    def from_terminal_args(cls) -> 'PomodoroConfig':
        """Create configuration from terminal command line arguments."""
        parser = argparse.ArgumentParser(description='终端番茄钟 (Pomodoro Timer)')
        parser.add_argument('-w', '--work', type=float, default=25.0, 
                          help='工作时长（分钟，默认25）')
        parser.add_argument('-r', '--rest', type=float, default=5.0, 
                          help='休息时长（分钟，默认5）')
        parser.add_argument('--no-loop', action='store_true', 
                          help='只运行一轮工作+休息后退出')
        parser.add_argument('--beep', action='store_true', 
                          help='阶段结束时蜂鸣 (可能只在部分终端有效)')
        parser.add_argument('--ascii', action='store_true', 
                          help='使用 ASCII 进度条 (避免某些终端宽度问题)')
        parser.add_argument('--tick', type=float, default=1.0, 
                          help='刷新间隔秒(默认1.0, 可小于1获得更平滑显示)')
        parser.add_argument('--color', action='store_true', 
                          help='启用彩色进度与阶段文本 (ANSI)')
        parser.add_argument('--notify', action='store_true', 
                          help='Windows 通知: 阶段切换提醒 (需要 win10toast)')
        parser.add_argument('--pre-rest', type=int, default=30, 
                          help='休息结束前多少秒提前提醒 (默认30)')
        
        args = parser.parse_args()
        
        return cls(
            work_minutes=args.work,
            rest_minutes=args.rest,
            cycles=1 if args.no_loop else None,
            use_ascii=args.ascii,
            use_color=args.color,
            tick=args.tick,
            enable_notifications=args.notify,
            enable_beep=args.beep,
            pre_rest_warning=args.pre_rest
        )
    
    @classmethod
    def from_overlay_args(cls) -> 'PomodoroConfig':
        """Create configuration from overlay command line arguments."""
        parser = argparse.ArgumentParser(description='Always-on-top mini Pomodoro overlay window.')
        parser.add_argument('-w', '--work', type=float, default=25.0, 
                          help='工作分钟 (默认25)')
        parser.add_argument('-r', '--rest', type=float, default=5.0, 
                          help='休息分钟 (默认5)')
        parser.add_argument('--rounds', type=int, default=None, 
                          help='限定总轮数，默认无限')
        parser.add_argument('--alpha', type=float, default=0.95, 
                          help='窗口透明度 0~1 (默认0.95)')
        parser.add_argument('--scale', type=float, default=1.0, 
                          help='UI缩放 (默认1.0)')
        parser.add_argument('--notify', action='store_true', 
                          help='阶段切换系统通知 (Windows BurntToast)')
        parser.add_argument('--balloon', action='store_true', 
                          help='托盘气泡提醒')
        parser.add_argument('--pre-rest', type=int, default=30, 
                          help='休息结束提前提醒秒数 (默认30)')
        
        args = parser.parse_args()
        
        return cls(
            work_minutes=args.work,
            rest_minutes=args.rest,
            cycles=args.rounds,
            alpha=args.alpha,
            scale=args.scale,
            enable_notifications=args.notify,
            enable_balloon=args.balloon,
            pre_rest_warning=args.pre_rest
        )