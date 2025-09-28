"""Core Pomodoro timer logic."""

import time
import signal
from typing import Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass

from .config import PomodoroConfig
from .notifications import NotificationManager
from .utils import get_logger

logger = get_logger(__name__)


class Phase(Enum):
    """Pomodoro timer phases."""
    WORK = "工作"
    REST = "休息"


@dataclass
class TimerState:
    """Current state of the Pomodoro timer."""
    phase: Phase
    cycle: int
    remaining_seconds: int
    total_seconds: int
    is_running: bool = True
    is_paused: bool = False
    start_time: float = 0.0
    
    @property
    def progress(self) -> float:
        """Get progress as a value between 0 and 1."""
        if self.total_seconds <= 0:
            return 1.0
        elapsed = self.total_seconds - self.remaining_seconds
        return min(1.0, max(0.0, elapsed / self.total_seconds))
    
    @property
    def minutes_remaining(self) -> int:
        """Get minutes remaining."""
        return self.remaining_seconds // 60
    
    @property
    def seconds_remaining(self) -> int:
        """Get seconds remaining (modulo 60)."""
        return self.remaining_seconds % 60


class PomodoroTimer:
    """Core Pomodoro timer with configurable behavior."""
    
    def __init__(self, config: PomodoroConfig, notification_manager: Optional[NotificationManager] = None):
        self.config = config
        self.notification_manager = notification_manager
        self._state: Optional[TimerState] = None
        self._callbacks: dict[str, list[Callable[[TimerState], None]]] = {
            'tick': [],
            'phase_start': [],
            'phase_end': [], 
            'timer_complete': [],
            'pre_rest_warning': []
        }
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(sig: int, frame: Any) -> None:
            if self._state:
                self._state.is_running = False
            logger.info("收到退出信号，正在优雅停止...")
        
        signal.signal(signal.SIGINT, signal_handler)
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_handler)
    
    def add_callback(self, event: str, callback: Callable[[TimerState], None]) -> None:
        """Add callback for timer events."""
        if event in self._callbacks:
            self._callbacks[event].append(callback)
        else:
            raise ValueError(f"Unknown event: {event}")
    
    def _trigger_callbacks(self, event: str) -> None:
        """Trigger all callbacks for an event."""
        if self._state and event in self._callbacks:
            for callback in self._callbacks[event]:
                try:
                    callback(self._state)
                except Exception as e:
                    logger.error(f"Callback error for {event}: {e}")
    
    def start(self) -> None:
        """Start the Pomodoro timer."""
        cycle = 1
        
        try:
            while True:
                # Work phase
                if not self._run_phase(Phase.WORK, cycle):
                    break
                
                # Check if we should stop after work phase
                if self.config.cycles and cycle >= self.config.cycles:
                    break
                
                # Rest phase
                if not self._run_phase(Phase.REST, cycle):
                    break
                
                cycle += 1
                
        except KeyboardInterrupt:
            logger.info("用户中断计时器")
        finally:
            self._trigger_callbacks('timer_complete')
    
    def _run_phase(self, phase: Phase, cycle: int) -> bool:
        """Run a single phase (work or rest). Returns False if interrupted."""
        duration_minutes = self.config.work_minutes if phase == Phase.WORK else self.config.rest_minutes
        total_seconds = int(duration_minutes * 60)
        
        # Initialize state
        self._state = TimerState(
            phase=phase,
            cycle=cycle,
            remaining_seconds=total_seconds,
            total_seconds=total_seconds,
            start_time=time.time()
        )
        
        # Notify phase start
        if self.notification_manager:
            message = f"开始{phase.value}：第{cycle}轮"
            self.notification_manager.notify('番茄钟', message)
        
        self._trigger_callbacks('phase_start')
        
        # Handle very short durations
        if total_seconds <= 2:
            time.sleep(total_seconds)
            self._state.remaining_seconds = 0
            self._trigger_callbacks('phase_end')
            return self._state.is_running
        
        # Main countdown loop
        pre_warning_sent = False
        last_tick_time = time.time()
        
        while self._state.remaining_seconds > 0 and self._state.is_running:
            if not self._state.is_paused:
                current_time = time.time()
                elapsed = current_time - self._state.start_time
                self._state.remaining_seconds = max(0, total_seconds - int(elapsed))
                
                # Pre-rest warning
                if (phase == Phase.REST and not pre_warning_sent and 
                    self._state.remaining_seconds <= self.config.pre_rest_warning and
                    self._state.remaining_seconds > 0):
                    if self.notification_manager:
                        message = f"休息即将结束(剩余~{self._state.remaining_seconds}s)，准备工作"
                        self.notification_manager.notify('番茄钟', message)
                    pre_warning_sent = True
                    self._trigger_callbacks('pre_rest_warning')
                
                # Trigger tick callbacks based on configured tick rate
                if current_time - last_tick_time >= self.config.tick:
                    self._trigger_callbacks('tick')
                    last_tick_time = current_time
            
            # Sleep for a short interval
            time.sleep(0.1)
        
        # Phase complete
        if self._state.is_running:
            if self.notification_manager:
                if phase == Phase.WORK:
                    message = f"工作完成，开始休息：第{cycle}轮"
                else:
                    message = f"休息结束，开始工作：第{cycle}轮"
                self.notification_manager.notify('番茄钟', message)
            
            self._trigger_callbacks('phase_end')
        
        return self._state.is_running
    
    def pause(self) -> None:
        """Pause the timer."""
        if self._state:
            self._state.is_paused = True
    
    def resume(self) -> None:
        """Resume the timer."""
        if self._state and self._state.is_paused:
            # Adjust start time to account for pause
            current_time = time.time()
            elapsed_before_pause = self._state.total_seconds - self._state.remaining_seconds
            self._state.start_time = current_time - elapsed_before_pause
            self._state.is_paused = False
    
    def stop(self) -> None:
        """Stop the timer."""
        if self._state:
            self._state.is_running = False
    
    def skip_phase(self) -> None:
        """Skip to the next phase."""
        if self._state:
            self._state.remaining_seconds = 0
    
    @property
    def current_state(self) -> Optional[TimerState]:
        """Get current timer state."""
        return self._state
    
    @property
    def is_running(self) -> bool:
        """Check if timer is currently running."""
        return self._state is not None and self._state.is_running