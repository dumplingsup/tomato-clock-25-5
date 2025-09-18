import time
import argparse
import signal
import sys
from datetime import timedelta

# Default durations (minutes)
DEFAULT_WORK_MIN = 25
DEFAULT_REST_MIN = 5

RUNNING = True

def signal_handler(sig, frame):
    global RUNNING
    RUNNING = False
    print("\n收到退出信号，正在优雅停止... (Finishing current second)")

signal.signal(signal.SIGINT, signal_handler)
if hasattr(signal, 'SIGTERM'):
    signal.signal(signal.SIGTERM, signal_handler)

def format_mmss(seconds: int) -> str:
    return str(timedelta(seconds=seconds))[-5:] if seconds < 3600 else str(timedelta(seconds=seconds))

def countdown(total_seconds: int, phase: str, cycle: int):
    start = time.time()
    remain = total_seconds
    while remain > 0 and RUNNING:
        mins = remain // 60
        secs = remain % 60
        bar_len = 30
        progress = (total_seconds - remain) / total_seconds
        filled = int(bar_len * progress)
        bar = '█' * filled + '░' * (bar_len - filled)
        msg = f"第{cycle}轮 {phase} | 剩余 {mins:02d}:{secs:02d} | {bar} {progress*100:5.1f}%"
        print(msg, end='\r', flush=True)
        # sleep until next second boundary for smoother countdown
        time.sleep(1 - ((time.time() - start) % 1))
        remain = total_seconds - int(time.time() - start)
    if RUNNING:
        print(' ' * 120, end='\r')  # clear line
        if phase == '工作':
            print(f"第{cycle}轮 工作完成！去休息吧！")
        else:
            print(f"第{cycle}轮 休息结束！回来继续！")


def run_pomodoro(work_min: float, rest_min: float):
    cycle = 1
    try:
        while RUNNING:
            countdown(int(work_min * 60), '工作', cycle)
            if not RUNNING:
                break
            countdown(int(rest_min * 60), '休息', cycle)
            cycle += 1
    finally:
        print("已退出番茄钟。")


def parse_args():
    p = argparse.ArgumentParser(description='终端番茄钟 (Pomodoro Timer)')
    p.add_argument('-w', '--work', type=float, default=DEFAULT_WORK_MIN, help='工作时长（分钟，默认25）')
    p.add_argument('-r', '--rest', type=float, default=DEFAULT_REST_MIN, help='休息时长（分钟，默认5）')
    p.add_argument('--no-loop', action='store_true', help='只运行一轮工作+休息后退出')
    p.add_argument('--beep', action='store_true', help='阶段结束时蜂鸣 (可能只在部分终端有效)')
    return p.parse_args()


def beep():
    # Cross-platform attempt; some terminals ignore it.
    print('\a', end='')


def main():
    args = parse_args()
    if args.work <= 0 or args.rest <= 0:
        print('工作或休息时长必须为正数。')
        sys.exit(1)
    if args.no_loop:
        global RUNNING
        countdown(int(args.work * 60), '工作', 1)
        if RUNNING:
            if args.beep:
                beep()
            countdown(int(args.rest * 60), '休息', 1)
            if args.beep:
                beep()
        print('单轮完成。')
    else:
        cycle = 1
        while RUNNING:
            countdown(int(args.work * 60), '工作', cycle)
            if RUNNING and args.beep:
                beep()
            if not RUNNING:
                break
            countdown(int(args.rest * 60), '休息', cycle)
            if RUNNING and args.beep:
                beep()
            cycle += 1
    print('感谢使用。')

if __name__ == '__main__':
    main()
