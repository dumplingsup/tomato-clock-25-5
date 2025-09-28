import time
import threading
import argparse
import tkinter as tk
from tkinter import ttk
import os
import platform
from PIL import Image, ImageDraw
import pystray
import itertools
DEBUG = bool(os.environ.get('TOMATO_DEBUG'))

# Simple always-on-top overlay for Pomodoro progress
# Separate from terminal script; minimal dependencies (Tk built-in)

DEFAULT_WORK = 25
DEFAULT_REST = 5

class Notifier:
    def __init__(self, enabled: bool, balloon: bool = False):
        self.enabled = enabled and platform.system() == 'Windows'
        self.balloon = balloon
        self.tray_ref = None  # will be set by overlay when tray icon ready
    def notify(self, title: str, msg: str):
        if not self.enabled:
            return
        # BurntToast attempt
        try:
            safe_title = title.replace("'","’’")
            safe_msg = msg.replace("'","’’")
            ps_script = (
                f"if (Get-Module -ListAvailable -Name BurntToast) {{ New-BurntToastNotification -Text '{safe_title}', '{safe_msg}'; }}"
            )
            os.system(f"powershell -NoProfile -ExecutionPolicy Bypass \"{ps_script}\" > NUL 2>&1")
        except Exception:
            pass
        # Balloon fallback via tray icon (if requested)
        if self.balloon and self.tray_ref:
            try:
                self.tray_ref.notify(msg, title=title)
            except Exception:
                pass

class PomodoroOverlay:
    def __init__(self, work_min: float, rest_min: float, alpha: float, scale: float, no_rounds: int | None, notifier: Notifier, pre_rest:int):
        self.work_s = int(work_min * 60)
        self.rest_s = int(rest_min * 60)
        self.round_limit = no_rounds
        self.round = 1
        self.phase = 'WORK'  # or REST
        self.running = True
        self.paused = False
        self.remaining = self.work_s
        self._start_ts = time.time()

        self.notifier = notifier
        self.pre_rest = pre_rest
        self.pre_notice_sent = False

        self.root = tk.Tk()
        self.root.title('Pomodoro')
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', alpha)
        self.root.resizable(False, False)
        self.root.overrideredirect(True)  # borderless

        # Allow drag move
        self.offset = (0,0)
        def start_move(e):
            self.offset = (e.x, e.y)
        def do_move(e):
            x = e.x_root - self.offset[0]
            y = e.y_root - self.offset[1]
            self.root.geometry(f"+{x}+{y}")
        self.root.bind('<Button-1>', start_move)
        self.root.bind('<B1-Motion>', do_move)

        pad = int(8*scale)
        self.frame = tk.Frame(self.root, bg='#222222')
        self.frame.pack(padx=pad, pady=pad)

        font_base = ('Segoe UI', int(10*scale), 'bold')
        self.label = tk.Label(self.frame, text='Initializing...', fg='#ffffff', bg='#222222', font=font_base)
        self.label.pack(fill='x')

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Red.Horizontal.TProgressbar', troughcolor='#444444', background='#ff7043', bordercolor='#444444', lightcolor='#ff8a65', darkcolor='#d84315')
        style.configure('Green.Horizontal.TProgressbar', troughcolor='#444444', background='#66bb6a', bordercolor='#444444', lightcolor='#81c784', darkcolor='#388e3c')

        self.bar = ttk.Progressbar(self.frame, orient='horizontal', mode='determinate', length=int(240*scale), style='Red.Horizontal.TProgressbar')
        self.bar.pack(fill='x', pady=(int(6*scale), int(4*scale)))

        ctrl_frame = tk.Frame(self.frame, bg='#222222')
        ctrl_frame.pack(fill='x')
        btn_font = ('Segoe UI', int(8*scale))
        self.btn_pause = tk.Button(ctrl_frame, text='Pause', width=6, command=self.toggle_pause, font=btn_font)
        self.btn_pause.pack(side='left', padx=2)
        self.btn_skip = tk.Button(ctrl_frame, text='Skip', width=6, command=self.skip_phase, font=btn_font)
        self.btn_skip.pack(side='left', padx=2)
        self.btn_close = tk.Button(ctrl_frame, text='Close', width=6, command=self.close, font=btn_font)
        self.btn_close.pack(side='right', padx=2)
        # Add Hide button (disabled until tray icon ready to avoid losing window)
        self.btn_hide = tk.Button(ctrl_frame, text='Hide', width=6, command=self.hide_window, font=btn_font, state='disabled')
        self.btn_hide.pack(side='right', padx=2)

        self.update_ui_initial()
        if self.notifier.enabled:
            self.notifier.notify('番茄钟', f'开始工作：第{self.round}轮')
        self.thread = threading.Thread(target=self.timer_loop, daemon=True)
        self.thread.start()

        self.tray_icon = None
        self.tray_ready = threading.Event()
        self.hidden = False  # must exist before tray thread builds menu
        self.tray_thread = threading.Thread(target=self._init_tray, daemon=True)
        self.tray_thread.start()

    def update_ui_initial(self):
        self.phase = 'WORK'
        self.remaining = self.work_s
        self._start_ts = time.time()
        self.update_label()
        self.bar.configure(maximum=self.work_s, value=0, style='Red.Horizontal.TProgressbar')

    def toggle_pause(self):
        self.paused = not self.paused
        self.btn_pause.configure(text='Resume' if self.paused else 'Pause')
        if not self.paused:
            # adjust start timestamp so remaining stays consistent
            self._start_ts = time.time() - (self.phase_duration() - self.remaining)

    def skip_phase(self):
        self.remaining = 0

    def close(self):
        self.running = False
        self.root.destroy()

    def phase_duration(self):
        return self.work_s if self.phase == 'WORK' else self.rest_s

    def switch_phase(self):
        if self.phase == 'WORK':
            self.phase = 'REST'
            self.remaining = self.rest_s
            self._start_ts = time.time()
            self.bar.configure(maximum=self.rest_s, value=0, style='Green.Horizontal.TProgressbar')
            self.pre_notice_sent = False
            if self.notifier.enabled:
                self.notifier.notify('番茄钟', f'开始休息：第{self.round}轮')
        else:
            self.phase = 'WORK'
            self.remaining = self.work_s
            self._start_ts = time.time()
            self.bar.configure(maximum=self.work_s, value=0, style='Red.Horizontal.TProgressbar')
            self.round += 1
            self.pre_notice_sent = False
            if self.round_limit and self.round > self.round_limit:
                self.close()
                return
            if self.notifier.enabled:
                self.notifier.notify('番茄钟', f'开始工作：第{self.round}轮')
        self.update_label()
        self._rebuild_tray_menu()

    def update_label(self):
        mins = self.remaining // 60
        secs = self.remaining % 60
        phase_text = '工作' if self.phase == 'WORK' else '休息'
        self.label.configure(text=f"第{self.round}轮 {phase_text} {mins:02d}:{secs:02d}")

    def _create_icon_image(self):
        img = Image.new('RGBA', (64,64), (0,0,0,0))
        d = ImageDraw.Draw(img)
        # Base circle
        d.ellipse((4,4,60,60), fill=(255,112,67,255))
        # Progress arc approximation by phase
        if self.phase == 'REST':
            d.ellipse((16,16,48,48), fill=(102,187,106,255))
        return img

    def _init_tray(self):
        if DEBUG:
            print('[tray] init thread start', flush=True)
        def on_pause(icon, item):
            self.root.after(0, self.toggle_pause)
            self.root.after(0, self._rebuild_tray_menu)
        def on_skip(icon, item):
            self.root.after(0, self.skip_phase)
        def on_reset(icon, item):
            def _reset():
                self.round = 1
                self.update_ui_initial()
            self.root.after(0, _reset)
        def on_toggle_top(icon, item):
            def _toggle():
                current = bool(self.root.attributes('-topmost'))
                self.root.attributes('-topmost', not current)
            self.root.after(0, _toggle)
        def on_toggle_notify(icon, item):
            self.notifier.enabled = not self.notifier.enabled
            self.root.after(0, self._rebuild_tray_menu)
        def on_toggle_balloon(icon, item):
            self.notifier.balloon = not self.notifier.balloon
            self.root.after(0, self._rebuild_tray_menu)
        def on_show_hide(icon, item):
            self.root.after(0, self.hide_window if not self.hidden else self.show_window)
        def on_quit(icon, item):
            self.root.after(0, self.close)
        self._tray_handlers = {
            'pause': on_pause,
            'skip': on_skip,
            'reset': on_reset,
            'top': on_toggle_top,
            'notify': on_toggle_notify,
            'balloon': on_toggle_balloon,
            'showhide': on_show_hide,
            'quit': on_quit,
        }
        try:
            menu = self._build_tray_menu()
        except Exception:
            menu = pystray.Menu(pystray.MenuItem('Quit', self._tray_handlers['quit']))
        self.tray_icon = pystray.Icon('pomodoro_overlay', self._create_icon_image(), 'Pomodoro Overlay', menu)
        self.notifier.tray_ref = self.tray_icon
        if DEBUG:
            print('[tray] icon object created', flush=True)
        # Mark tray ready and enable Hide button in UI thread
        self.root.after(0, lambda: (self.tray_ready.set(), self.btn_hide.configure(state='normal')))
        if DEBUG:
            print('[tray] entering run()', flush=True)
        self.tray_icon.run()

    def _build_tray_menu(self):
        pause_text = 'Pause' if not self.paused else 'Resume'
        notify_text = '通知 Off' if self.notifier.enabled else '通知 On'
        balloon_text = '气泡 Off' if self.notifier.balloon else '气泡 On'
        showhide = getattr(self, 'hidden', False)
        showhide_text = 'Show' if showhide else 'Hide'
        return pystray.Menu(
            pystray.MenuItem(pause_text, self._tray_handlers['pause']),
            pystray.MenuItem(showhide_text, self._tray_handlers['showhide']),
            pystray.MenuItem('Skip', self._tray_handlers['skip']),
            pystray.MenuItem('Reset', self._tray_handlers['reset']),
            pystray.MenuItem('TopMost Toggle', self._tray_handlers['top']),
            pystray.MenuItem(notify_text, self._tray_handlers['notify']),
            pystray.MenuItem(balloon_text, self._tray_handlers['balloon']),
            pystray.MenuItem('Quit', self._tray_handlers['quit'])
        )

    def _rebuild_tray_menu(self):
        if self.tray_icon:
            try:
                self.tray_icon.menu = self._build_tray_menu()
            except Exception:
                pass

    def _update_tray_icon(self):
        if self.tray_icon and self.tray_icon.visible:
            try:
                self.tray_icon.icon = self._create_icon_image()
            except Exception:
                pass

    def hide_window(self):
        # Prevent hiding before tray icon is available (would make window unreachable)
        if not self.tray_ready.is_set():
            return
        if not self.hidden:
            self.root.withdraw()
            self.hidden = True
        else:
            self.root.deiconify()
            self.hidden = False
        self._rebuild_tray_menu()

    def show_window(self):
        if self.hidden:
            self.root.deiconify()
            self.hidden = False
            self._rebuild_tray_menu()

    def timer_loop(self):
        while self.running:
            if not self.paused:
                elapsed = int(time.time() - self._start_ts)
                dur = self.phase_duration()
                self.remaining = max(0, dur - elapsed)
                progress_val = dur - self.remaining
                self.bar['value'] = progress_val
                self.update_label()
                self._update_tray_icon()
                if self.phase == 'REST' and self.notifier.enabled and (not self.pre_notice_sent) and self.remaining <= self.pre_rest and self.remaining > 0:
                    self.notifier.notify('番茄钟', f'休息即将结束 (剩余~{self.remaining}s)')
                    self.pre_notice_sent = True
                if self.remaining <= 0:
                    self.switch_phase()
            time.sleep(0.25)

    def run(self):
        self.root.mainloop()


def parse_args():
    ap = argparse.ArgumentParser(description='Always-on-top mini Pomodoro overlay window.')
    ap.add_argument('-w','--work', type=float, default=DEFAULT_WORK, help='工作分钟 (默认25)')
    ap.add_argument('-r','--rest', type=float, default=DEFAULT_REST, help='休息分钟 (默认5)')
    ap.add_argument('--rounds', type=int, default=None, help='限定总轮数，默认无限')
    ap.add_argument('--alpha', type=float, default=0.95, help='窗口透明度 0~1 (默认0.95)')
    ap.add_argument('--scale', type=float, default=1.0, help='UI缩放 (默认1.0)')
    ap.add_argument('--notify', action='store_true', help='阶段切换系统通知 (Windows BurntToast)')
    ap.add_argument('--pre-rest', type=int, default=30, help='休息结束提前提醒秒数 (默认30)')
    ap.add_argument('--balloon', action='store_true', help='同时使用托盘气泡提示 (pystray icon.notify)')
    return ap.parse_args()


def main():
    args = parse_args()
    notifier = Notifier(args.notify, args.balloon)
    overlay = PomodoroOverlay(args.work, args.rest, args.alpha, args.scale, args.rounds, notifier, args.pre_rest)
    overlay.run()

if __name__ == '__main__':
    main()
