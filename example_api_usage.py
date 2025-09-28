#!/usr/bin/env python3
"""
Example of using the new Tomato Clock API.

This demonstrates how to use the modular structure programmatically.
"""

from tomato_clock import PomodoroTimer, PomodoroConfig, NotificationManager

def main():
    # Create configuration
    config = PomodoroConfig(
        work_minutes=0.1,  # 6 seconds for demo
        rest_minutes=0.1,  # 6 seconds for demo 
        cycles=2,          # Only 2 cycles for demo
        use_color=True,
        enable_notifications=False  # Disabled for demo
    )
    
    print("🍅 番茄钟 API 使用示例")
    print(f"工作时长: {config.work_minutes} 分钟")
    print(f"休息时长: {config.rest_minutes} 分钟")
    print(f"总轮数: {config.cycles}")
    print("-" * 30)
    
    # Create notification manager
    notifier = NotificationManager(config.enable_notifications)
    
    # Create timer
    timer = PomodoroTimer(config, notifier)
    
    # Add custom callbacks
    def on_phase_start(state):
        print(f"📅 开始 {state.phase.value} - 第{state.cycle}轮")
    
    def on_phase_end(state):
        print(f"✅ {state.phase.value} 完成 - 第{state.cycle}轮")
    
    def on_timer_complete(state):
        print("🎉 番茄钟完成！")
    
    timer.add_callback('phase_start', on_phase_start)
    timer.add_callback('phase_end', on_phase_end)
    timer.add_callback('timer_complete', on_timer_complete)
    
    # Start timer
    print("启动计时器...")
    timer.start()

if __name__ == '__main__':
    main()