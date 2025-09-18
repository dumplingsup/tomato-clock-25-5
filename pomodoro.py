import time
import argparse
import signal
import sys
import shutil
import os
import platform
import atexit

# Default durations (minutes)
DEFAULT_WORK_MIN = 25
DEFAULT_REST_MIN = 5

RUNNING = True
_prev_line_len = 0  # track previously printed status line length
MAX_BAR = 30
COLOR_RESET = '\x1b[0m'
COLOR_PHASE_WORK = '\x1b[38;5;208m'  # orange
COLOR_PHASE_REST = '\x1b[38;5;42m'   # green
COLOR_BAR_FILL = '\x1b[38;5;33m'     # blue
COLOR_BAR_EMPTY = '\x1b[38;5;240m'   # grey

def signal_handler(sig, frame):
    global RUNNING
    RUNNING = False
    print("\n收到退出信号，正在优雅停止... (Finishing current second)")

signal.signal(signal.SIGINT, signal_handler)
if hasattr(signal, 'SIGTERM'):
    signal.signal(signal.SIGTERM, signal_handler)

def countdown(total_seconds: int, phase: str, cycle: int, use_ascii: bool, tick: float, use_color: bool, notifier: 'Notifier|None'=None, pre_rest:int=30):
    global _prev_line_len
    start = time.time()
    remain = total_seconds
    if notifier:
        if phase == '工作':
            notifier.notify('番茄钟', f'开始工作：第{cycle}轮', duration=5)
        else:
            notifier.notify('番茄钟', f'开始休息：第{cycle}轮', duration=5)
    full_block = '#' if use_ascii else '█'
    empty_block = '-' if use_ascii else '░'
    if total_seconds <= 2:
        time_label = f"{remain//60:02d}:{remain%60:02d}"
        msg = f"第{cycle}轮 {phase} {time_label} 开始" if remain > 0 else f"第{cycle}轮 {phase} 结束"
        print(msg)
        time.sleep(total_seconds)
        return
    last_render_second = -1
    pre_notice_sent = False
    while remain > 0 and RUNNING:
        now = time.time()
        elapsed = now - start
        remain = max(0, total_seconds - elapsed)
        if phase == '休息' and notifier and (not pre_notice_sent) and remain <= pre_rest:
            notifier.notify('番茄钟', f'休息即将结束(剩余~{int(remain)}s)，准备工作', duration=5)
            pre_notice_sent = True
        if (tick <= 0.05) or (elapsed // tick) != (last_render_second // tick) or remain <= 0:
            last_render_second = elapsed
            term_width = shutil.get_terminal_size(fallback=(80, 20)).columns
            whole_seconds_left = int(remain + 0.999)
            mins = whole_seconds_left // 60
            secs = whole_seconds_left % 60
            progress = min(1.0, max(0.0, elapsed / total_seconds)) if total_seconds > 0 else 1.0
            prefix_phase = phase
            if use_color:
                if phase == '工作':
                    prefix_phase = f"{COLOR_PHASE_WORK}{phase}{COLOR_RESET}"
                else:
                    prefix_phase = f"{COLOR_PHASE_REST}{phase}{COLOR_RESET}"
            prefix = f"第{cycle}轮 {prefix_phase} | 剩余 {mins:02d}:{secs:02d} | "
            percent = f"{progress*100:5.1f}%"
            suffix = ' ' + percent
            available_for_bar = term_width - len(prefix) - len(suffix) - 1
            if available_for_bar < 5:
                msg = f"第{cycle}轮 {prefix_phase} {mins:02d}:{secs:02d} {percent}"
            else:
                bar_len = min(available_for_bar, MAX_BAR)
                filled = int(bar_len * progress)
                bar_fill = full_block * filled
                bar_empty = empty_block * (bar_len - filled)
                if use_color and not use_ascii:
                    bar = f"{COLOR_BAR_FILL}{bar_fill}{COLOR_RESET}{COLOR_BAR_EMPTY}{bar_empty}{COLOR_RESET}"
                else:
                    bar = bar_fill + bar_empty
                msg = prefix + bar + suffix
            if len(msg) > term_width:
                msg = msg[: term_width - 1]
            padded = msg + ' ' * max(0, _prev_line_len - len(msg))
            print('\r' + padded, end='', flush=True)
            _prev_line_len = len(msg)
        if remain <= 0 or not RUNNING:
            break
        to_next = tick - ((time.time() - start) % tick)
        if to_next < 0.01:
            to_next = 0.01
        time.sleep(min(to_next, remain))
    print('\r' + ' ' * _prev_line_len + '\r', end='', flush=True)
    if RUNNING:
        end_msg = (
            f"第{cycle}轮 工作完成！去休息吧！" if phase == '工作' else f"第{cycle}轮 休息结束！回来继续！"
        )
        if notifier:
            if phase == '工作':
                notifier.notify('番茄钟', f'工作完成，开始休息：第{cycle}轮', duration=5)
            else:
                notifier.notify('番茄钟', f'休息结束，开始工作：第{cycle}轮', duration=5)
        if use_color:
            color = COLOR_PHASE_WORK if phase == '工作' else COLOR_PHASE_REST
            end_msg = f"{color}{end_msg}{COLOR_RESET}"
        print(end_msg)


def run_pomodoro(work_min: float, rest_min: float, use_ascii: bool, tick: float, use_color: bool, notifier: 'Notifier|None', pre_rest:int):
    cycle = 1
    try:
        while RUNNING:
            countdown(int(work_min * 60), '工作', cycle, use_ascii, tick, use_color, notifier, pre_rest)
            if not RUNNING:
                break
            countdown(int(rest_min * 60), '休息', cycle, use_ascii, tick, use_color, notifier, pre_rest)
            cycle += 1
    finally:
        print("已退出番茄钟。")


def parse_args():
    p = argparse.ArgumentParser(description='终端番茄钟 (Pomodoro Timer)')
    p.add_argument('-w', '--work', type=float, default=DEFAULT_WORK_MIN, help='工作时长（分钟，默认25）')
    p.add_argument('-r', '--rest', type=float, default=DEFAULT_REST_MIN, help='休息时长（分钟，默认5）')
    p.add_argument('--no-loop', action='store_true', help='只运行一轮工作+休息后退出')
    p.add_argument('--beep', action='store_true', help='阶段结束时蜂鸣 (可能只在部分终端有效)')
    p.add_argument('--ascii', action='store_true', help='使用 ASCII 进度条 (避免某些终端宽度问题)')
    p.add_argument('--tick', type=float, default=1.0, help='刷新间隔秒(默认1.0, 可小于1获得更平滑显示)')
    p.add_argument('--color', action='store_true', help='启用彩色进度与阶段文本 (ANSI)')
    p.add_argument('--notify', action='store_true', help='Windows 通知: 阶段切换提醒 (需要 win10toast)')
    p.add_argument('--pre-rest', type=int, default=30, help='休息结束前多少秒提前提醒 (默认30)')
    return p.parse_args()


def beep():
    # Cross-platform attempt; some terminals ignore it.
    print('\a', end='')


def enable_windows_ansi():
    if platform.system() == 'Windows':
        try:
            import msvcrt  # noqa: F401
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE = -11
            mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                new_mode = mode.value | 0x0004  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
                kernel32.SetConsoleMode(handle, new_mode)
        except Exception:
            pass

try:
    from typing import Optional
except ImportError:
    Optional = None  # type: ignore

class Notifier:
    def __init__(self, enabled: bool):
        self.enabled = enabled
        self._toaster = None
        self._fallback_ps = platform.system() == 'Windows'
        self._failed = False
        if enabled and platform.system() == 'Windows':
            try:
                from win10toast import ToastNotifier  # type: ignore
                self._toaster = ToastNotifier()
            except Exception:
                self._toaster = None
        atexit.register(self._graceful_close)

    def _graceful_close(self):
        # Short sleep to allow threaded notifications to finish
        if self.enabled and self._toaster is not None and not self._failed:
            try:
                time.sleep(0.15)
            except Exception:
                pass

    def notify(self, title: str, msg: str, duration: int = 5):
        if not self.enabled or self._failed:
            return
        if self._toaster is not None:
            try:
                self._toaster.show_toast(title, msg, duration=duration, threaded=False)
                return
            except Exception as e:
                if 'WNDPROC' in repr(e) or 'LRESULT' in repr(e) or 'WPARAM' in repr(e):
                    self._failed = True
                self._toaster = None
        # PowerShell BurntToast
        if self._fallback_ps and not self._failed:
            try:
                safe_title = title.replace("'", "’’")
                safe_msg = msg.replace("'", "’’")
                ps_script = (
                    f"if (Get-Module -ListAvailable -Name BurntToast) "
                    f"{{ New-BurntToastNotification -Text '{safe_title}', '{safe_msg}'; }}"
                )
                os.system(f"powershell -NoProfile -ExecutionPolicy Bypass \"{ps_script}\" > NUL 2>&1")
                return
            except Exception:
                pass
        try:
            print(f"\n[通知] {title}: {msg}")
        except Exception:
            self._failed = True


def main():
    args = parse_args()
    if args.color:
        enable_windows_ansi()
    if args.work <= 0 or args.rest <= 0:
        print('工作或休息时长必须为正数。')
        sys.exit(1)
    tick = max(0.05, args.tick)
    notifier = Notifier(args.notify)
    if args.no_loop:
        countdown(int(args.work * 60), '工作', 1, args.ascii, tick, args.color, notifier, args.pre_rest)
        if RUNNING:
            if args.beep:
                beep()
            countdown(int(args.rest * 60), '休息', 1, args.ascii, tick, args.color, notifier, args.pre_rest)
            if args.beep:
                beep()
        print('单轮完成。')
    else:
        cycle = 1
        while RUNNING:
            countdown(int(args.work * 60), '工作', cycle, args.ascii, tick, args.color, notifier, args.pre_rest)
            if RUNNING and args.beep:
                beep()
            if not RUNNING:
                break
            countdown(int(args.rest * 60), '休息', cycle, args.ascii, tick, args.color, notifier, args.pre_rest)
            if RUNNING and args.beep:
                beep()
            cycle += 1
    print('感谢使用。')

if __name__ == '__main__':
    main()
