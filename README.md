# 终端番茄钟 (Pomodoro Timer)

一个简单的 Python 终端番茄钟：默认 25 分钟工作 + 5 分钟休息，不断循环；支持自定义时长、只运行一轮、蜂鸣提示、动态刷新频率、彩色输出、Windows 通知提醒，并提供桌面置顶迷你进度条窗口与系统托盘集成。

## 迷你置顶窗口 overlay
使用 Tkinter 创建一个无边框、可拖拽、始终置顶的小组件显示当前轮次、阶段与进度条，并支持：
- 系统托盘图标 (pystray)
- 阶段切换系统通知（BurntToast 或托盘气泡）
- 托盘菜单操作与隐藏/显示

示例：
```powershell
python overlay.py                       # 默认 25/5 循环
python overlay.py -w 50 -r 10           # 自定义时长
python overlay.py --rounds 4            # 限制 4 轮后自动关闭
python overlay.py --alpha 0.85          # 半透明
python overlay.py --scale 1.2           # 放大 UI
python overlay.py --notify --balloon    # 同时启用系统通知 + 托盘气泡
python overlay.py -w 0.1 -r 0.05 --rounds 1 --scale 0.9 --notify --balloon --pre-rest 5
```

### Overlay 额外参数
```text
--notify          阶段切换系统通知 (尝试 BurntToast; 无则忽略)
--balloon         使用托盘气泡 (icon.notify) 作为额外提醒
--pre-rest <秒>   休息结束前提醒秒数 (默认30)
```

### Overlay 窗口操作
- 拖动：鼠标左键按住任意空白区域拖拽
- Pause / Resume：暂停 / 继续
- Skip：跳过当前阶段
- Hide：最小化到托盘 (托盘菜单可 Show 恢复)
- Close：关闭窗口

### 托盘菜单项
- Pause / Resume
- Show / Hide (切换窗口显示)
- Skip / Reset / TopMost Toggle
- 通知 On/Off（系统通知开关）
- 气泡 On/Off（托盘气泡开关）
- Quit

### 通知策略
启用 `--notify`：
- 开始工作 / 开始休息
- 休息即将结束（<= `--pre-rest` 秒）
启用 `--balloon`：同上事件会使用托盘气泡，作为额外或替代提示。

> 提示：若需系统原生 Toast，PowerShell 管理员执行：`Install-Module -Name BurntToast -Force`。

(以下为终端版本说明)

## 运行要求
- Python 3.7+ （已在 3.13 测试）
- Windows 通知可选：`win10toast` 或 PowerShell 模块 BurntToast（overlay 使用 BurntToast/托盘气泡；终端版本有回退策略）
- 托盘功能依赖：`pystray`, `Pillow`

## 终端版本快速开始
```powershell
python pomodoro.py            # 默认 25/5 循环
python pomodoro.py --no-loop  # 单轮
```

## 参数说明 (终端版本)
```text
-w, --work <分钟>     工作时长 (默认 25)
-r, --rest <分钟>     休息时长 (默认 5)
--no-loop             只运行一轮（工作+休息）
--beep                每阶段结束蜂鸣
--ascii               ASCII 进度条
--tick <秒>           刷新间隔 (默认 1.0，最小 0.05)
--color               彩色输出
--notify              Windows 通知
--pre-rest <秒>       休息结束提前提醒 (默认 30)
```

## 通知行为 (终端)
阶段开始/结束 + 休息即将结束（阈值内）。问题库 (win10toast) 不稳定时会退化为控制台提示。

## 示例 (终端)
```powershell
python pomodoro.py -w 50 -r 10
python pomodoro.py --tick 0.2
python pomodoro.py --color --beep
python pomodoro.py -w 15 -r 3 --no-loop
python pomodoro.py -w 0.1 -r 0.05 --no-loop --tick 0.2 --ascii
python pomodoro.py --notify --pre-rest 20
```

## TODO / 可扩展想法
- 每 4 轮长休息
- 日志统计 / 导出
- 托盘图标动态显示剩余时间百分比（文字叠加）
- 自定义阶段配置
- 声音文件播放

欢迎继续提出你想要的功能！
