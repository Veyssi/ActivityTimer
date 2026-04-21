import tkinter as tk
from tkinter import ttk, messagebox
from plyer import notification
import threading
import time
import pystray
from PIL import Image, ImageDraw
import os
import sys
import winsound
import winreg as wr

class ActivityTimerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("活动计时器")
        self.root.geometry("480x600")
        self.root.configure(bg="#16213e")
        self.root.resizable(False, False)
        self.root.attributes("-alpha", 0.95)
        
        # 数据状态
        self.duration_minutes = 45
        self.time_left = self.duration_minutes * 60
        self.is_running = False
        self.is_paused = False
        self.is_window_visible = True
        self._after_id = None  # 保存 after 回调 ID，用于取消
        
        # 创建托盘图标
        self.icon_image = Image.new('RGB', (32, 32), color=(22, 33, 62))
        self.d = ImageDraw.Draw(self.icon_image)
        self.d.text((8, 8), "T", fill=(100, 255, 200))
        
        # 初始化托盘
        self.tray_icon = None

        # 开机自启状态
        self.auto_start = False

        # 初始化样式
        self.init_style()
        
        # 构建界面
        self.create_ui()

        # 初始化开机自启状态
        self._init_auto_start()

        # 拦截窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)

    def init_style(self):
        """配置现代简约暗色主题样式"""
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # 主框架
        self.style.configure('Main.TFrame', background='#16213e')

        # 标题
        self.style.configure('Title.TLabel',
                           font=('Microsoft YaHei', 18, 'bold'),
                           background='#16213e',
                           foreground='#e8e8e8')

        # 时间显示 - 霓虹绿数字
        self.style.configure('Time.TLabel',
                           font=('Consolas', 48, 'bold'),
                           background='#16213e',
                           foreground='#00d9ff')

        # 状态标签
        self.style.configure('Status.TLabel',
                           font=('Microsoft YaHei', 10),
                           background='#1f3460',
                           foreground='#00d9ff')

        # 按钮 - 暗色背景
        self.style.configure('Control.TButton',
                           padding=(20, 10),
                           font=('Microsoft YaHei', 11),
                           background='#1f3460',
                           foreground='#e8e8e8')

        # 按钮悬停
        self.style.map('Control.TButton',
                      background=[('active', '#2d4a7c'), ('pressed', '#3d5a8c')],
                      foreground=[('active', '#ffffff')])

        # 输入框
        self.style.configure('Input.TEntry',
                           fieldbackground='#0f3460',
                           foreground='#e8e8e8',
                           insertcolor='#00d9ff',
                           padding=8)

        # 进度条
        self.style.configure('Custom.Horizontal.TProgressbar',
                           thickness=8,
                           background='#00d9ff',
                           troughcolor='#0f3460',
                           lightcolor='#00d9ff',
                           darkcolor='#0f3460')

        # 设置区域标签
        self.style.configure('Settings.TLabelframe',
                           background='#16213e',
                           foreground='#e8e8e8')
        self.style.configure('Settings.TLabelframe.Label',
                           background='#16213e',
                           foreground='#00d9ff',
                           font=('Microsoft YaHei', 10))

        # Checkbutton 暗色样式
        self.style.configure('Input.TCheckbutton', background='#16213e', foreground='#e8e8e8')
        self.style.map('Input.TCheckbutton',
                       background=[('active', '#1f3460'), ('selected', '#0f3460')],
                       foreground=[('active', '#ffffff'), ('selected', '#00d9ff')])

    def create_ui(self):
        """构建用户界面"""
        # 标题区
        self.create_header()
        
        # 时间显示
        self.create_time_display()
        
        # 进度条
        self.create_progress_bar()
        
        # 设置区域
        self.create_settings()
        
        # 控制按钮组
        self.create_buttons()

        # 状态显示
        self.status_label = tk.Label(
            self.root,
            text="就绪",
            font=('Microsoft YaHei', 10),
            bg='#16213e',
            fg='#6b7280'
        )
        self.status_label.pack(pady=(5, 0))

    def create_header(self):
        """创建标题区域"""
        header = ttk.Label(
            self.root,
            text="STAND UP TIMER",
            style='Title.TLabel'
        )
        header.pack(pady=(25, 10))

        # 副标题
        sub = tk.Label(
            self.root,
            text="久坐提醒 · 站立活动",
            font=('Microsoft YaHei', 10),
            bg='#16213e',
            fg='#6b7280'
        )
        sub.pack(pady=(0, 15))

    def create_time_display(self):
        """创建时间显示区域"""
        # 时间容器 - 加个底色卡片
        card = tk.Frame(self.root, bg='#1f3460', bd=0)
        card.pack(pady=10, padx=30, fill='x')

        self.time_display = tk.Label(
            card,
            text="00:00:00",
            font=('Consolas', 48, 'bold'),
            bg='#1f3460',
            fg='#00d9ff'
        )
        self.time_display.pack(pady=20)

    def create_progress_bar(self):
        """创建进度条"""
        self.progress_bar = ttk.Progressbar(
            self.root,
            length=380,
            mode='determinate',
            style='Custom.Horizontal.TProgressbar'
        )
        self.progress_bar.pack(pady=15)

    def create_settings(self):
        """创建设置区域"""
        settings_frame = ttk.LabelFrame(
            self.root,
            text="设置",
            padding=15,
            style='Settings.TLabelframe'
        )
        settings_frame.pack(padx=30, pady=10, fill='x')

        # 标签
        tk.Label(
            settings_frame,
            text="循环时长",
            font=('Microsoft YaHei', 10),
            bg='#16213e',
            fg='#9ca3af'
        ).grid(row=0, column=0, padx=(10, 5), pady=8, sticky='e')

        # 输入框
        self.entry_time = ttk.Entry(
            settings_frame,
            width=8,
            style='Input.TEntry'
        )
        self.entry_time.insert(0, str(self.duration_minutes))
        self.entry_time.grid(row=0, column=1, padx=5, pady=8)

        # 单位
        tk.Label(
            settings_frame,
            text="分钟",
            font=('Microsoft YaHei', 10),
            bg='#16213e',
            fg='#9ca3af'
        ).grid(row=0, column=2, padx=(5, 10), pady=8, sticky='w')

    def create_buttons(self):
        """创建控制按钮"""
        btn_frame = tk.Frame(self.root, bg='#16213e')
        btn_frame.pack(pady=20)

        buttons = [
            ("开始", self.toggle_timer),
            ("重置", self.reset_timer),
            ("状态", self.show_current_status),
        ]

        for i, (text, cmd) in enumerate(buttons):
            btn = tk.Button(
                btn_frame,
                text=text,
                command=cmd,
                font=('Microsoft YaHei', 11),
                bg='#1f3460',
                fg='#e8e8e8',
                activebackground='#2d4a7c',
                activeforeground='#ffffff',
                bd=0,
                padx=25,
                pady=10,
                cursor='hand2'
            )
            btn.grid(row=0, column=i, padx=8, pady=5)

        # 保存开始按钮引用用于更新文本
        self.btn_start = btn_frame.grid_slaves(row=0, column=0)[0]

    def toggle_timer(self):
        """切换计时器状态"""
        if self.is_paused:
            self.resume_timer()
        elif self.is_running:
            self.pause_timer()
        else:
            self.start_timer()

    def start_timer(self):
        """启动计时器"""
        try:
            val = int(self.entry_time.get())
            if val <= 0:
                messagebox.showerror("输入错误", "请输入大于0的整数")
                return
            self.duration_minutes = val
            self.time_left = self.duration_minutes * 60
        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的数字")
            return

        self.is_running = True
        self.is_paused = False
        self.btn_start.config(text="暂停", bg='#c0392b')
        # Use determinate progress so we can update its value
        self.progress_bar.config(mode='determinate', maximum=100, value=0)
        self.update_status("运行中")
        self.show_notification("计时器已启动")

        # Start the UI update loop
        self.update_time_display()

    def pause_timer(self):
        """暂停计时器"""
        self.is_paused = True
        self.is_running = False
        if self._after_id:
            self.root.after_cancel(self._after_id)
            self._after_id = None
        self.btn_start.config(text="继续", bg='#1f3460')
        self.update_status("已暂停")

    def resume_timer(self):
        """继续计时，不重置剩余时间"""
        self.is_paused = False
        self.is_running = True
        self.btn_start.config(text="暂停", bg='#c0392b')
        self.progress_bar.config(mode='determinate')
        self.update_status("运行中")
        self.show_notification("计时器已继续")
        self.update_time_display()

    def reset_timer(self):
        """重置计时器"""
        try:
            val = int(self.entry_time.get())
            if val <= 0:
                messagebox.showerror("输入错误", "请输入大于0的整数")
                return
            self.duration_minutes = val
            self.time_left = self.duration_minutes * 60
            self.time_display.config(text="00:00:00")
            self.progress_bar.config(value=0)
            self.is_running = False
            self.is_paused = False
            if self._after_id:
                self.root.after_cancel(self._after_id)
                self._after_id = None
            self.progress_bar.stop()
            self.btn_start.config(text="开始", bg='#1f3460')
            self.update_status("已重置")
        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的数字")

    def update_time_display(self):
        """更新时间显示"""
        if self.is_running and not self.is_paused:
            total_seconds = self.duration_minutes * 60
            progress = int((self.time_left / total_seconds) * 100) if total_seconds > 0 else 0
            self.progress_bar.config(value=progress)

            hours, rem = divmod(self.time_left, 3600)
            minutes, seconds = divmod(rem, 60)
            self.time_display.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

            if self.time_left <= 0:
                self.time_to_activity()
                self.time_left = self.duration_minutes * 60
            else:
                self.time_left -= 1
            self._after_id = self.root.after(1000, self.update_time_display)
        elif not self.is_running:
            self._after_id = None

    def time_to_activity(self):
        """时间到达提示"""
        if self.is_running:
            self.show_notification("时间到！请起身活动一下")

    def show_notification(self, message):
        """显示系统通知"""
        try:
            notification.notify(
                title="活动提醒",
                message=message,
                timeout=0,
                app_name="Activity Timer"
            )
            winsound.MessageBeep(winsound.MB_OK)
        except Exception:
            pass

    def update_status(self, status_text):
        """更新状态标签"""
        self.status_label.config(text=status_text)

    def show_current_status(self):
        """显示当前状态"""
        if self.is_running and not self.is_paused:
            status = "运行中"
        elif self.is_paused:
            status = "已暂停"
        else:
            status = "就绪"

        remaining = int(self.time_left / 60)
        msg = f"当前状态：{status}\n\n循环时长：{self.duration_minutes} 分钟\n剩余时间：{remaining} 分钟"
        messagebox.showinfo("当前状态", msg)

    def toggle_window_visibility(self, icon=None, item=None):
        """切换窗口显示/隐藏"""
        if self.is_window_visible:
            self.root.withdraw()
            self.is_window_visible = False
        else:
            self.root.deiconify()
            self.root.lift()
            self.root.focus()
            self.is_window_visible = True

    def on_window_close(self):
        """窗口关闭事件处理"""
        self.root.withdraw()
        self.is_window_visible = False

    def create_tray_menu(self):
        """创建托盘菜单"""
        menu = (
            pystray.MenuItem("显示/隐藏", self.toggle_window_visibility, default=True),
            pystray.MenuItem("开始/暂停", self.toggle_timer),
            pystray.MenuItem("重置计时", self.reset_timer),
            pystray.MenuItem("查看状态", self.show_current_status),
            pystray.MenuItem(
                "开机自启",
                self.toggle_auto_start,
                checked=lambda _: self.auto_start
            ),
            pystray.MenuItem("退出", self.on_tray_quit)
        )
        return menu

    def on_tray_quit(self, icon=None, item=None):
        """从托盘退出"""
        self.tray_icon.stop()
        self.root.quit()

    # ---------- 开机自启 ----------

    def _get_exe_path(self):
        """获取当前 exe 路径（打包后和开发时都适用）"""
        if getattr(os, 'frozen', False):
            return os.path.abspath(sys.executable)
        return os.path.abspath(__file__)

    def _init_auto_start(self):
        """初始化开机自启状态"""
        try:
            key = wr.OpenKey(wr.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, wr.KEY_READ)
            value, _ = wr.QueryValueEx(key, "ActivityTimer")
            wr.CloseKey(key)
            self.auto_start = bool(value)
        except (FileNotFoundError, OSError):
            self.auto_start = False

    def toggle_auto_start(self, icon=None, item=None):
        """实时切换开机自启（更新注册表）"""
        # item.index 是当前勾选状态的索引：-1=未勾选，>=0=已勾选
        self.auto_start = not (item and item.checked)
        exe_path = self._get_exe_path()

        try:
            key = wr.CreateKey(wr.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run")
            if self.auto_start:
                wr.SetValueEx(key, "ActivityTimer", 0, wr.REG_SZ, exe_path)
            else:
                wr.DeleteValue(key, "ActivityTimer")
            wr.CloseKey(key)
        except OSError as e:
            messagebox.showerror("错误", f"修改开机自启失败：\n{e}")
            # 回滚状态
            self.auto_start = not self.auto_start

    def run(self):
        """运行主程序"""
        # 创建托盘图标
        self.tray_icon = pystray.Icon(
            "ActivityTimer",
            self.icon_image,
            menu=pystray.Menu(*self.create_tray_menu())
        )

        # 用 after 轮询托盘状态，避免独立线程干扰 tkinter
        def poll_tray():
            try:
                self.tray_icon._update_check()
            except Exception:
                pass
            self.root.after(500, poll_tray)

        # 启动托盘（非阻塞）
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
        self.root.after(500, poll_tray)

        # 运行主窗口
        self.root.mainloop()

if __name__ == "__main__":
    app = ActivityTimerApp()
    app.run()
