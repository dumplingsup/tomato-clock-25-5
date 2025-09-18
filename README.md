# 终端番茄钟 (Pomodoro Timer)

一个简单的 Python 终端番茄钟：默认 25 分钟工作 + 5 分钟休息，不断循环；支持自定义时长、只运行一轮、蜂鸣提示、动态刷新频率、彩色输出、Windows 通知提醒。

## 运行要求
- Python 3.7+ （已在 3.13 测试）
- 可选 Windows 通知：安装 `win10toast` (使用 `--notify` 时自动需要)

## 安装通知依赖（如需）
```powershell
pip install win10toast
```

## 快速开始
```powershell
python pomodoro.py            # 默认 25/5 循环
python pomodoro.py --no-loop  # 单轮
```

## 参数说明
```text
-w, --work <分钟>     工作时长 (默认 25)
-r, --rest <分钟>     休息时长 (默认 5)
--no-loop             只运行一轮（工作+休息）
--beep                每阶段结束蜂鸣 (终端支持时)
--ascii               使用 ASCII 进度条 (# / -)，避免某些终端宽字符换行
--tick <秒>           刷新间隔 (默认 1.0，可设 0.2 更平滑；最小 0.05)
--color               启用彩色阶段文字与进度条 (Windows 自动尝试打开 ANSI)
--notify              Windows 桌面通知：阶段开始/结束 & 休息即将结束提醒
--pre-rest <秒>       休息结束提前提醒秒数 (默认 30)
-h, --help            查看帮助
```

## 通知行为
启用 `--notify` 后：
- 开始工作：弹出“开始工作：第N轮”
- 工作结束：弹出“工作完成，开始休息：第N轮”
- 开始休息：弹出“开始休息：第N轮”
- 休息剩余 <= `--pre-rest` 秒：弹出“休息即将结束…”
- 休息结束：弹出“休息结束，开始工作：第N轮”

## 示例
```powershell
python pomodoro.py -w 50 -r 10
python pomodoro.py --tick 0.2
python pomodoro.py --color --beep
python pomodoro.py -w 15 -r 3 --no-loop
python pomodoro.py -w 0.1 -r 0.05 --no-loop --tick 0.2 --ascii
python pomodoro.py --notify --pre-rest 20  # 启用通知并设置休息结束提前 20 秒提醒
```

## 显示行为
- 单行实时刷新，宽度不足时缩短进度条或省略
- 极短 (≤2s) 简化输出
- `Ctrl + C` 优雅停止
- 彩色模式在不支持 ANSI 的终端可能降级

## TODO / 可扩展想法
- 每 4 轮长休息
- 日志记录与统计
- 系统托盘图标 / 富通知
- 自定义阶段配置文件
- 声音文件播放

欢迎继续提出你想要的功能！
