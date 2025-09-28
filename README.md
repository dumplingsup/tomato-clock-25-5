# 终端番茄钟 (Pomodoro Timer) - 优化版

一个经过重构优化的 Python 番茄钟：默认 25 分钟工作 + 5 分钟休息，不断循环；支持自定义时长、只运行一轮、蜂鸣提示、动态刷新频率、彩色输出、Windows 通知提醒，并提供桌面置顶迷你进度条窗口与系统托盘集成。

## 🚀 v1.0.0 重大更新

本版本进行了全面的代码重构，提供了更好的模块化结构和 API 支持：

### ✨ 新特性
- **🏗️ 模块化架构**：完全重构的代码结构，更好的可维护性
- **📦 Python 包**：可以作为库使用，支持编程接口
- **🔧 统一配置**：集中的配置管理系统
- **📢 统一通知**：优化的通知系统，支持多种通知方式
- **🔄 向后兼容**：保持原有命令行接口完全兼容
- **🎯 类型提示**：完整的类型注解支持
- **📝 完善文档**：详细的 API 文档和使用示例

### 📁 新的项目结构
```
tomato-clock-25-5/
├── tomato_clock/              # 主包目录
│   ├── __init__.py           # 包初始化和公共接口
│   ├── core.py               # 核心计时器逻辑
│   ├── config.py             # 配置管理
│   ├── notifications.py      # 统一通知系统
│   ├── utils.py              # 工具函数
│   ├── terminal_ui.py        # 终端界面
│   └── overlay_ui.py         # 覆盖层界面
├── pomodoro.py               # 兼容性入口（终端版）
├── overlay.py                # 兼容性入口（GUI版）
├── example_api_usage.py      # API 使用示例
└── README.md                 # 本文档
```

## 运行要求
- Python 3.7+ （已在 3.12 测试）
- Windows 通知可选：`win10toast` 或 PowerShell 模块 BurntToast
- 托盘功能依赖：`pystray`, `Pillow`

## 📚 使用方式

### 1. 传统命令行方式（向后兼容）

#### 终端版本快速开始
```powershell
python pomodoro.py            # 默认 25/5 循环
python pomodoro.py --no-loop  # 单轮
python pomodoro.py -w 50 -r 10 --color --beep  # 自定义配置
```

#### 覆盖层界面
```powershell
python overlay.py                       # 默认 25/5 循环
python overlay.py -w 50 -r 10           # 自定义时长
python overlay.py --rounds 4            # 限制 4 轮后自动关闭
python overlay.py --alpha 0.85          # 半透明
python overlay.py --scale 1.2           # 放大 UI
python overlay.py --notify --balloon    # 同时启用系统通知 + 托盘气泡
```

### 2. 新的 Python API 方式

```python
from tomato_clock import PomodoroTimer, PomodoroConfig, NotificationManager

# 创建配置
config = PomodoroConfig(
    work_minutes=25,
    rest_minutes=5,
    cycles=4,  # 4 轮后停止
    use_color=True,
    enable_notifications=True
)

# 创建通知管理器
notifier = NotificationManager(config.enable_notifications)

# 创建计时器
timer = PomodoroTimer(config, notifier)

# 添加自定义回调
def on_phase_start(state):
    print(f"开始 {state.phase.value} - 第{state.cycle}轮")

timer.add_callback('phase_start', on_phase_start)

# 启动计时器
timer.start()
```

### 3. 作为模块导入

```python
# 使用终端界面类
from tomato_clock.terminal_ui import TerminalUI
from tomato_clock.config import PomodoroConfig

config = PomodoroConfig.from_terminal_args()
ui = TerminalUI(config)
ui.run()
```

## 📖 API 文档

### 主要类

#### `PomodoroConfig`
配置管理类，支持验证和多种初始化方式。

```python
config = PomodoroConfig(
    work_minutes=25.0,      # 工作时长（分钟）
    rest_minutes=5.0,       # 休息时长（分钟）
    cycles=None,            # 总轮数（None=无限）
    use_ascii=False,        # 使用 ASCII 进度条
    use_color=False,        # 启用彩色输出
    tick=1.0,               # 刷新间隔（秒）
    enable_notifications=False,  # 启用通知
    enable_beep=False,      # 启用蜂鸣
    pre_rest_warning=30,    # 休息结束前提醒（秒）
    alpha=0.95,             # GUI 透明度
    scale=1.0,              # GUI 缩放比例
    enable_balloon=False    # 启用托盘气泡通知
)
```

#### `PomodoroTimer`
核心计时器类，支持事件回调。

```python
timer = PomodoroTimer(config, notification_manager)

# 支持的事件类型
timer.add_callback('tick', callback_function)           # 每次刷新
timer.add_callback('phase_start', callback_function)    # 阶段开始
timer.add_callback('phase_end', callback_function)      # 阶段结束
timer.add_callback('timer_complete', callback_function) # 计时器完成
timer.add_callback('pre_rest_warning', callback_function) # 休息结束提醒

# 控制方法
timer.start()        # 开始计时
timer.pause()        # 暂停
timer.resume()       # 恢复
timer.stop()         # 停止
timer.skip_phase()   # 跳过当前阶段
```

#### `NotificationManager`
统一通知管理器，支持多种通知方式。

```python
notifier = NotificationManager(enabled=True, enable_balloon=False)
notifier.notify("标题", "消息内容")
```

## 🔧 技术改进

### 代码优化
- **消除重复代码**：统一了 `Notifier` 类实现，移除了代码重复
- **更好的封装**：使用类和模块封装，消除全局变量依赖
- **分离关注点**：UI 逻辑与业务逻辑完全分离
- **配置集中化**：统一的配置管理和验证系统
- **错误处理**：改进的异常处理和日志记录

### 架构优势
- **可扩展性**：模块化设计便于添加新功能
- **可测试性**：各组件独立，便于单元测试
- **可维护性**：清晰的代码结构和职责分离
- **可重用性**：核心组件可用于其他项目

### 向后兼容
- 保持原有命令行接口 100% 兼容
- 原有的所有参数和功能均正常工作
- 无需修改现有脚本或使用习惯

## 参数说明

### 终端版本 (pomodoro.py)
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

### 覆盖层版本 (overlay.py)
```text
-w, --work <分钟>     工作时长 (默认 25)
-r, --rest <分钟>     休息时长 (默认 5)
--rounds <数量>       限定总轮数，默认无限
--alpha <0-1>         窗口透明度 (默认 0.95)
--scale <倍数>        UI缩放 (默认 1.0)
--notify              阶段切换系统通知
--balloon             托盘气泡提醒
--pre-rest <秒>       休息结束提前提醒 (默认 30)
```

## 示例

### 终端版本
```powershell
python pomodoro.py -w 50 -r 10
python pomodoro.py --tick 0.2
python pomodoro.py --color --beep
python pomodoro.py -w 15 -r 3 --no-loop
python pomodoro.py -w 0.1 -r 0.05 --no-loop --tick 0.2 --ascii
python pomodoro.py --notify --pre-rest 20
```

### 覆盖层版本
```powershell
python overlay.py -w 0.1 -r 0.05 --rounds 1 --scale 0.9 --notify --balloon --pre-rest 5
```

### API 示例
参见 `example_api_usage.py` 文件。

## 通知系统

### 支持的通知方式
1. **Windows Toast 通知** (win10toast)
2. **PowerShell BurntToast** 模块
3. **系统托盘气泡** (overlay 版本)
4. **控制台输出** (fallback)

### 通知触发时机
- 工作/休息阶段开始
- 工作/休息阶段结束
- 休息即将结束提醒（可配置提前时间）

## 系统托盘功能 (覆盖层版本)

### 窗口操作
- **拖拽**：鼠标左键按住任意区域拖拽窗口
- **暂停/恢复**：点击暂停按钮或托盘菜单
- **跳过阶段**：点击跳过按钮或托盘菜单
- **隐藏/显示**：最小化到托盘或从托盘恢复

### 托盘菜单
- 暂停/恢复计时器
- 显示/隐藏窗口
- 跳过当前阶段
- 重置计时器
- 切换置顶状态
- 通知开关
- 气泡提醒开关
- 退出程序

## TODO / 扩展想法

- [ ] 每 4 轮长休息功能
- [ ] 使用统计和日志导出
- [ ] 托盘图标显示进度百分比
- [ ] 自定义阶段配置文件
- [ ] 声音文件播放支持
- [ ] 配置文件持久化
- [ ] 多语言支持
- [ ] 主题系统

## 贡献

欢迎提出功能建议、报告问题或提交改进！

---

**享受你的番茄工作法时光！** 🍅⏰