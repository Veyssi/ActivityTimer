<h1 align="center">Activity Timer — 久坐站立提醒计时器</h1>


<div align="center">

基于 Python + tkinter 开发的纯提醒桌面应用

功能简单：设定时间→循环提醒

<img width="597" height="737" alt="image" src="https://github.com/user-attachments/assets/4d204052-ac99-4cf4-9da9-3b7d6ab94bbe" />

定时起身动动走走。

<img width="237" height="250" alt="image" src="https://github.com/user-attachments/assets/76c5bdce-0e4f-4d22-bd5d-f917c1c13bad" />


关闭窗口默认隐藏到托盘后台运行

<img width="584" height="207" alt="image" src="https://github.com/user-attachments/assets/0dae0041-dbf5-41e7-9143-fd101ce22300" />

调用系统气泡通知和声音，符合日常使用习惯感觉更自然

全屏以及忙碌、专注等状态默认系统提醒设置

**不影响全屏玩游戏和日常使用**

</div>

---

## 技术栈

| 类别 | 库/模块 | 用途 |
|------|---------|------|
| GUI | `tkinter` / `ttk` | 主窗口与控件 |
| 托盘 | `pystray` + `PIL` | 系统托盘图标与菜单 |
| 通知 | `plyer.notification` | 系统级弹窗通知 |
| 音频 | `winsound` | Windows 提示音 |
| 自启 | `winreg` | Windows 注册表开机自启 |
| 并发 | `threading` | 托盘线程（daemon） |

---

## 核心类：ActivityTimerApp

### 状态变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `duration_minutes` | int | 循环时长（默认 45 分钟） |
| `time_left` | int | 剩余秒数 |
| `is_running` | bool | 是否正在运行 |
| `is_paused` | bool | 是否已暂停 |
| `is_window_visible` | bool | 窗口是否可见 |
| `auto_start` | bool | 是否开机自启（注册表） |
| `is_transparent` | bool | 背景透明开关（托盘菜单控制） |
| `_after_id` | str | tkinter `after()` 回调 ID，用于取消 |

### UI 构建流程

```
__init__()
 ├── init_style()          # 暗色主题样式配置
 ├── create_ui()
 │    ├── _create_close_button()   # 右上角自定义关闭按钮（悬停变色）
 │    ├── create_header()       # "STAND UP TIMER" 标题 + 副标题
 │    ├── create_time_display() # Consolas 48px 倒计时
 │    ├── create_progress_bar() # 自定义进度条
 │    ├── create_settings()     # 输入框：循环时长（分钟）
 │    └── create_buttons()      # 开始 / 重置 / 状态 三个按钮
 ├── _init_auto_start()        # 读取注册表初始化开机自启
 ├── _center_window()          # 计算屏幕尺寸并居中显示
 └── protocol(WM_DELETE_WINDOW) # 关闭 → 隐藏而非退出
```

### 窗口特性

- **无系统边框**：使用 `overrideredirect(True)` 移除默认边框，暗色主题
- **居中启动**：程序启动时自动计算屏幕尺寸并居中显示
- **鼠标拖动**：支持在窗口非交互区域（标题区、空白处）点击拖动，设置区的输入框/按钮等控件点击不触发拖动
- **自定义关闭按钮**：右上角暗色 "✕" 按钮，悬停高亮
- **背景透明开关**：托盘菜单中可切换窗口半透明（alpha=0.95）与不透明（alpha=1.0）

### 计时器状态机

```
[就绪] --start_timer()--> [运行中]
                        --pause_timer()--> [已暂停]
                        <--resume_timer()--
[已暂停] --reset_timer()--> [就绪]
[运行中] --time_to_activity()--> 弹出通知 + time_left 重置
```

### 关键方法

| 方法 | 功能 |
|------|------|
| `start_timer()` | 读取输入框值，启动倒计时，更新 UI |
| `pause_timer()` | 取消 `after()` 回调，标记暂停 |
| `resume_timer()` | 恢复倒计时，不重置时间 |
| `reset_timer()` | 停止计时，`time_left` 归零，进度条复位 |
| `toggle_timer()` | 根据当前状态自动切换（开始/暂停/继续） |
| `update_time_display()` | 每秒回调：更新进度条 + 倒计时文本 |
| `show_notification()` | plyer 系统通知 + winsound 提示音 |
| `on_window_close()` | 窗口关闭 → `withdraw()` 隐藏到托盘 |
| `_init_auto_start()` | 读取注册表初始化开机自启状态 |
| `toggle_auto_start()` | 切换注册表自启项，实时更新菜单勾选标记 |

### 托盘功能

- **创建**：`pystray.Icon` + PIL 图像（32x32，霓虹绿 "T"）
- **菜单项**：显示/隐藏、开始/暂停、重置计时、查看状态、**开机自启**、**背景透明**、退出
- **开机自启**：托盘菜单中切换，实时读写 Windows 注册表 `HKCU\...\Run`，无需重启
- **实现方式**：daemon 线程运行 `tray_icon.run()`，主线程通过 `after(500, poll_tray)` 轮询更新

### 启动入口

```python
if __name__ == "__main__":
    app = ActivityTimerApp()
    app.run()
```

---

## 样式主题（暗色）

| 元素 | 背景色 | 前景色 |
|------|--------|--------|
| 主窗口 | `#16213e` | — |
| 卡片/按钮 | `#1f3460` | `#e8e8e8` |
| 时间显示 | `#1f3460` | `#00d9ff`（霓虹蓝） |
| 进度条 | `#00d9ff` | `#0f3460` |
| 设置区 | `#0f3460` | — |

---

## 源码运行以及构建的依赖安装

```bash
pip install plyer pystray Pillow
```

> `tkinter`、`threading`、`time`、`os`、`winsound` 均为 Python 标准库，无需额外安装。

### 源码运行

```bash
python ActivityTimer.py
```

### Windows 构建（打包为 exe）

```bash
pip install pyinstaller
pyinstaller --name "ActivityTimer" --noconsole --onefile --clean --hidden-import=plyer.platforms.win --hidden-import=plyer.platforms.win.notification --hidden-import=plyer.platforms.win.audio ActivityTimer.py
```

- `--onefile`：单文件打包
- `--noconsole`：不弹出控制台窗口
- `--hidden-import=plyer.platforms.win`：静态分析时可能漏掉 plyer 的动态平台模块，手动加入
- `--hidden-import=plyer.platforms.win.notification`：同上，Windows 通知子模块
- `--hidden-import=plyer.platforms.win.audio`：同上，Windows 音频子模块
- 如果不手动指定，打包后的 exe 运行时可能报 ModuleNotFoundError。
- 生成的 `dist/ActivityTimer.exe` 可直接双击运行
