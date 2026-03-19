import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import os
import platform
import glob

class ScrollableFrame(ttk.Frame):
    """一个通用的可滚动 Frame 容器"""
    def __init__(self, container, *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        
        # 1. 创建 Canvas 和 Scrollbar
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        # 2. 创建内部真正承载内容的 Frame
        self.scrollable_frame = ttk.Frame(self.canvas)

        # 3. 关键：当内部 Frame 大小改变时，重置 Canvas 的滚动区域
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        # 4. 在 Canvas 中绘制这个 Frame (anchor="nw" 表示左上角对齐)
        # width=canvas.winfo_width() 稍后在 resize 中处理，保证横向填满
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        # 5. 绑定鼠标滚轮事件 (Windows/Linux/Mac)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.bind_mouse_scroll(self.canvas)
        self.bind_mouse_scroll(self.scrollable_frame)

        # 6. 布局
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # 7. 监听 Canvas 大小变化，强制让内部 Frame 宽度与 Canvas 一致 (实现横向自适应)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

    def _on_canvas_configure(self, event):
        # 让内部 Frame 的宽度等于 Canvas 的宽度，这样只有纵向才需要滚动条
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def bind_mouse_scroll(self, widget):
        """递归绑定鼠标滚轮事件"""
        # Windows / Mac
        widget.bind("<MouseWheel>", self._on_mousewheel)
        # Linux
        widget.bind("<Button-4>", self._on_mousewheel)
        widget.bind("<Button-5>", self._on_mousewheel)
        
        for child in widget.winfo_children():
            self.bind_mouse_scroll(child)

    def _on_mousewheel(self, event):
        if platform.system() == "Windows":
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif platform.system() == "Darwin": # Mac
            self.canvas.yview_scroll(int(-1 * event.delta), "units")
        else: # Linux
            if event.num == 4: self.canvas.yview_scroll(-1, "units")
            if event.num == 5: self.canvas.yview_scroll(1, "units")
        
        # 阻止事件冒泡，防止文本框滚动时页面也跟着动 (可选，这里简单起见不阻止)
        # return "break" 

class UltimateSqlmapLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("SQLMap 全能启动器 (Scrollable Edition)")
        self.root.geometry("1100x800") # 默认大小可以稍微小一点，反正能滚动

        self.setup_styles()

        # --- 布局结构 ---
        # 根布局：放一个 ScrollableFrame 填满整个窗口
        self.scroll_container = ScrollableFrame(self.root)
        self.scroll_container.pack(fill="both", expand=True)

        # 获取内部真正的内容容器
        content_frame = self.scroll_container.scrollable_frame
        
        # 给内容容器加 Padding
        # 注意：这里我们再套一层 Frame 或者直接用 content_frame 的 padding
        # 为了美观，我们在 content_frame 里面放一个主 Frame
        self.main_frame = ttk.Frame(content_frame, padding="15 15 15 15")
        self.main_frame.pack(fill="both", expand=True)
        
        # --- 下面就是之前的初始化逻辑，只是父容器变成了 self.main_frame ---
        self.init_target_frame(self.main_frame)
        self.init_logic_frame(self.main_frame)
        self.init_execution_frame(self.main_frame)

        # 初始加载
        self.refresh_tampers()
        self.update_command()
        
        # 重新绑定一下滚轮（因为动态添加了新控件）
        self.root.update_idletasks() # 确保控件已渲染
        self.scroll_container.bind_mouse_scroll(self.main_frame)


    def setup_styles(self):
        style = ttk.Style()
        try: style.theme_use('clam')
        except: pass

        BG_COLOR = "#f5f6f7"
        ACCENT_COLOR = "#0078d4"
        TEXT_COLOR = "#333333"

        self.root.configure(bg=BG_COLOR)
        style.configure(".", font=("Segoe UI", 11), background=BG_COLOR, foreground=TEXT_COLOR)
        style.configure("TLabelframe", background=BG_COLOR, borderwidth=1)
        style.configure("TLabelframe.Label", font=("Segoe UI", 12, "bold"), foreground="#005a9e", background=BG_COLOR)
        style.configure("TEntry", fieldbackground="white", borderwidth=1)
        style.map("TEntry", bordercolor=[('focus', ACCENT_COLOR), ('!focus', '#cccccc')])
        style.configure("TButton", font=("Segoe UI", 11), borderwidth=1, background="#e1e1e1")
        style.map("TButton", background=[('active', '#d0d0d0'), ('pressed', '#c0c0c0')])
        style.configure("Accent.TButton", font=("Segoe UI", 12, "bold"), foreground="white", background=ACCENT_COLOR, borderwidth=0)
        style.map("Accent.TButton", background=[('active', '#006cbd'), ('pressed', '#005a9e')])
        style.configure("TCheckbutton", background=BG_COLOR, font=("Segoe UI", 11))
        style.map("TCombobox", fieldbackground=[('readonly', 'white')])

    def init_target_frame(self, parent):
        frame = ttk.LabelFrame(parent, text=" 1. 攻击目标 (Target) ", padding=15)
        frame.pack(fill="x", pady=(0, 15)) # 改用 pack 布局，因为在滚动容器里垂直排列更简单
        
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="URL 地址:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.url_var = tk.StringVar()
        self.url_var.trace("w", self.update_command)
        ttk.Entry(frame, textvariable=self.url_var).grid(row=0, column=1, sticky="ew", ipady=3)

        ttk.Label(frame, text="数据包粘贴:").grid(row=1, column=0, sticky="nw", pady=(15, 0))
        self.raw_text = scrolledtext.ScrolledText(frame, height=5, font=("Consolas", 10), bg="white", relief="flat", borderwidth=1)
        self.raw_text.grid(row=1, column=1, sticky="ew", pady=(15, 5))
        self.raw_text.bind("<<Modified>>", self.on_text_change)
        
        ttk.Label(frame, text="ℹ️ 提示：粘贴后自动切换为 -r request.txt 模式").grid(row=2, column=1, sticky="w", padx=2)

    def init_logic_frame(self, parent):
        # 逻辑区容器
        container = ttk.Frame(parent)
        container.pack(fill="x", pady=0)
        container.columnconfigure(0, weight=3) # 左侧配置区
        container.columnconfigure(1, weight=2) # 右侧开关区

        # === 左侧：详细配置区 ===
        left_frame = ttk.LabelFrame(container, text=" 2. 注入配置 (Configuration) ", padding=15)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_frame.columnconfigure(1, weight=1)
        left_frame.columnconfigure(3, weight=1)

        # --- 基础参数 (D/T/C) ---
        r = 0
        def add_entry(label, var, col_span=3):
            nonlocal r
            ttk.Label(left_frame, text=label).grid(row=r, column=0, sticky="w", pady=5)
            ttk.Entry(left_frame, textvariable=var).grid(row=r, column=1, columnspan=col_span, sticky="ew", padx=10, ipady=3)
            r += 1

        self.db_var = tk.StringVar(); self.db_var.trace("w", self.update_command)
        self.table_var = tk.StringVar(); self.table_var.trace("w", self.update_command)
        self.col_var = tk.StringVar(); self.col_var.trace("w", self.update_command)
        
        add_entry("数据库 (-D):", self.db_var)
        add_entry("表 名 (-T):", self.table_var)
        add_entry("列 名 (-C):", self.col_var)
        
        ttk.Separator(left_frame).grid(row=r, column=0, columnspan=4, sticky="ew", pady=10)
        r += 1

        # --- 连接与鉴权 ---
        ttk.Label(left_frame, text="Cookie:").grid(row=r, column=0, sticky="w", pady=5)
        self.cookie_var = tk.StringVar(); self.cookie_var.trace("w", self.update_command)
        ttk.Entry(left_frame, textvariable=self.cookie_var).grid(row=r, column=1, columnspan=3, sticky="ew", padx=10, ipady=3)
        r += 1

        ttk.Label(left_frame, text="HTTP代理:").grid(row=r, column=0, sticky="w", pady=5)
        self.proxy_var = tk.StringVar(); self.proxy_var.trace("w", self.update_command)
        ttk.Entry(left_frame, textvariable=self.proxy_var).grid(row=r, column=1, sticky="ew", padx=10, ipady=3)
        
        ttk.Label(left_frame, text="线程数:").grid(row=r, column=2, sticky="w", pady=5) 
        self.threads_var = tk.StringVar(value="") 
        cb_threads = ttk.Combobox(left_frame, textvariable=self.threads_var, values=["", "2", "5", "10"], state="readonly", width=8)
        cb_threads.grid(row=r, column=3, sticky="w", padx=10, ipady=3)
        cb_threads.bind("<<ComboboxSelected>>", self.update_command)
        r += 1
        
        ttk.Separator(left_frame).grid(row=r, column=0, columnspan=4, sticky="ew", pady=10)
        r += 1

        # --- 注入策略 ---
        ttk.Label(left_frame, text="等级/风险:").grid(row=r, column=0, sticky="w")
        box_lr = ttk.Frame(left_frame)
        box_lr.grid(row=r, column=1, columnspan=3, sticky="w")
        
        self.level_var = tk.StringVar(value="默认")
        ttk.Label(box_lr, text="Lv:").pack(side="left", padx=(10, 2))
        cbl = ttk.Combobox(box_lr, textvariable=self.level_var, values=["默认", "1", "2", "3", "5"], state="readonly", width=5)
        cbl.pack(side="left"); cbl.bind("<<ComboboxSelected>>", self.update_command)

        self.risk_var = tk.StringVar(value="默认")
        ttk.Label(box_lr, text="Risk:").pack(side="left", padx=(15, 2))
        cbr = ttk.Combobox(box_lr, textvariable=self.risk_var, values=["默认", "1", "2", "3"], state="readonly", width=5)
        cbr.pack(side="left"); cbr.bind("<<ComboboxSelected>>", self.update_command)
        r += 1

        ttk.Label(left_frame, text="技术/延时:").grid(row=r, column=0, sticky="w", pady=8)
        self.tech_var = tk.StringVar(value="默认(全部)")
        tech_values = ["默认(全部)", "B: 布尔盲注", "E: 报错注入", "U: 联合查询", "S: 堆叠注入", "T: 时间盲注", "EU: 报错+联合"]
        cb_tech = ttk.Combobox(left_frame, textvariable=self.tech_var, values=tech_values, state="readonly", width=12)
        cb_tech.grid(row=r, column=1, sticky="ew", padx=10, ipady=3)
        cb_tech.bind("<<ComboboxSelected>>", self.update_command)

        self.time_var = tk.StringVar()
        self.time_var.trace("w", self.update_command)
        entry_time = ttk.Entry(left_frame, textvariable=self.time_var, width=5)
        entry_time.grid(row=r, column=2, sticky="w")
        ttk.Label(left_frame, text="秒").grid(row=r, column=2, padx=(50,0)) 

        self.dbms_var = tk.StringVar(value="自动")
        cb_dbms = ttk.Combobox(left_frame, textvariable=self.dbms_var, values=["自动", "MySQL", "Oracle", "MSSQL", "PostgreSQL"], state="readonly", width=8)
        cb_dbms.grid(row=r, column=3, sticky="w", padx=10, ipady=3)
        cb_dbms.bind("<<ComboboxSelected>>", self.update_command)
        r += 1

        ttk.Separator(left_frame).grid(row=r, column=0, columnspan=4, sticky="ew", pady=10)
        r += 1

        # --- Tamper & Extra ---
        ttk.Label(left_frame, text="Tamper:").grid(row=r, column=0, sticky="w")
        tamper_box = ttk.Frame(left_frame)
        tamper_box.grid(row=r, column=1, columnspan=3, sticky="ew", padx=10)
        tamper_box.columnconfigure(0, weight=1)
        
        self.tamper_var = tk.StringVar()
        self.tamper_combo = ttk.Combobox(tamper_box, textvariable=self.tamper_var, state="readonly")
        self.tamper_combo.grid(row=0, column=0, sticky="ew", ipady=3)
        self.tamper_combo.bind("<<ComboboxSelected>>", self.update_command)
        ttk.Button(tamper_box, text="❌", width=3, command=lambda: self.set_tamper("")).grid(row=0, column=1, padx=(5,0))
        ttk.Button(tamper_box, text="🔄", width=3, command=self.refresh_tampers).grid(row=0, column=2, padx=(2,0))
        r += 1

        ttk.Label(left_frame, text="额外参数:").grid(row=r, column=0, sticky="w", pady=(10,0))
        self.extra_var = tk.StringVar(); self.extra_var.trace("w", self.update_command)
        ttk.Entry(left_frame, textvariable=self.extra_var).grid(row=r, column=1, columnspan=3, sticky="ew", padx=10, pady=(10,0), ipady=3)

        # === 右侧：功能开关 ===
        right_frame = ttk.LabelFrame(container, text=" 3. 执行选项 (Options) ", padding=15)
        right_frame.grid(row=0, column=1, sticky="nsew")

        self.opts = [
            ("📊  当前数据库 (--current-db)", "--current-db"),
            ("👑  检测 DBA (--is-dba)", "--is-dba"),
            ("👥  列出用户 (--users)", "--users"),
            ("🔑  获取密码哈希 (--passwords)", "--passwords"), 
            ("🛡️查看权限 (--privileges)", "--privileges"),   
            ("", ""),
            ("📚  获取所有数据库 (--dbs)", "--dbs"),
            ("📂  获取所有表 (--tables)", "--tables"),
            ("📝  获取所有列 (--columns)", "--columns"),
            ("💾  获取/导出数据 (--dump)", "--dump"),
            ("🐚  系统 Shell (--os-shell)", "--os-shell"),
            ("", ""),
            ("🚫  忽略缓存 (--fresh-queries)", "--fresh-queries"),
            ("🧹  清除Session (--flush-session)", "--flush-session"), 
            ("⚙️  自动确认 (--batch)", "--batch"),
            ("🎭  随机 UA (--random-agent)", "--random-agent"),
            ("📁  保存到 result 目录", "--output-dir=result"),
            ("🐞  调试模式 (-v 3)", "-v 3"),
        ]

        self.chk_vars = {}
        for text, param in self.opts:
            if text == "":
                ttk.Separator(right_frame).pack(fill="x", pady=8)
                continue
            
            var = tk.BooleanVar()
            if param in ["--batch", "--random-agent"]:
                var.set(True)
            
            var.trace("w", self.update_command)
            self.chk_vars[param] = var
            ttk.Checkbutton(right_frame, text=text, variable=var).pack(anchor="w", pady=2)

    def init_execution_frame(self, parent):
        frame = ttk.LabelFrame(parent, text=" 4. 命令预览与执行 ", padding=15)
        frame.pack(fill="x", pady=(15, 0)) # 改用 pack

        self.cmd_display = ttk.Entry(frame, font=("Consolas", 11))
        self.cmd_display.pack(fill="x", pady=(0, 15), ipady=5)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack()
        
        ttk.Button(btn_frame, text="复制命令", command=self.copy_cmd, width=15).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="🚀 启动 SQLMap", style="Accent.TButton", command=self.run_cmd, width=20).pack(side="left", padx=10)

    # --- Logic Helpers ---
    def set_tamper(self, val):
        self.tamper_combo.set(val)
        self.update_command()

    def refresh_tampers(self):
        tamper_dir = os.path.join(os.getcwd(), "tamper")
        if not os.path.exists(tamper_dir):
            self.tamper_combo['values'] = ["未找到 tamper 目录"]
            return
        files = glob.glob(os.path.join(tamper_dir, "*.py"))
        scripts = [os.path.basename(f) for f in files if "__init__" not in f]
        scripts.sort()
        self.tamper_combo['values'] = scripts if scripts else ["目录为空"]

    def on_text_change(self, event=None):
        self.raw_text.edit_modified(False)
        self.update_command()

    def get_raw_content(self):
        return self.raw_text.get("1.0", "end-1c").strip()

    def update_command(self, *args):
        cmd = ["python", "sqlmap.py"]

        # 1. Target
        raw_content = self.get_raw_content()
        url = self.url_var.get().strip()
        if raw_content:
            cmd.append("-r request.txt")
        elif url:
            cmd.append(f'-u "{url}"')

        # 2. Connection
        cookie = self.cookie_var.get().strip()
        if cookie: cmd.append(f'--cookie="{cookie}"')
        
        proxy = self.proxy_var.get().strip()
        if proxy: cmd.append(f'--proxy="{proxy}"')
        
        threads = self.threads_var.get()
        if threads: cmd.append(f'--threads={threads}')

        # 3. Strategy
        level = self.level_var.get()
        if level != "默认": cmd.append(f"--level={level}")
            
        risk = self.risk_var.get()
        if risk != "默认": cmd.append(f"--risk={risk}")

        dbms = self.dbms_var.get()
        if dbms != "自动": cmd.append(f'--dbms="{dbms}"')

        time_sec = self.time_var.get().strip()
        if time_sec: cmd.append(f"--time-sec={time_sec}")

        tech_map = {"默认(全部)": "", "B: 布尔盲注": "B", "E: 报错注入": "E", "U: 联合查询": "U", "S: 堆叠注入": "S", "T: 时间盲注": "T", "EU: 报错+联合": "EU"}
        tech_sel = self.tech_var.get()
        if tech_sel in tech_map and tech_map[tech_sel]:
            cmd.append(f'--technique={tech_map[tech_sel]}')

        # 4. Filters
        db = self.db_var.get().strip()
        table = self.table_var.get().strip()
        col = self.col_var.get().strip()
        tamper = self.tamper_var.get().strip()
        extra = self.extra_var.get().strip()

        if db: cmd.append(f'-D "{db}"')
        if table: cmd.append(f'-T "{table}"')
        if col: cmd.append(f'-C "{col}"')
        if tamper and tamper not in ["未找到 tamper 目录", "目录为空"]:
            cmd.append(f'--tamper "{tamper}"')

        # 5. Actions
        for param, var in self.chk_vars.items():
            if var.get():
                cmd.append(param)

        if extra: cmd.append(extra)

        full_cmd = " ".join(cmd)
        self.cmd_display.delete(0, tk.END)
        self.cmd_display.insert(0, full_cmd)

    def copy_cmd(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.cmd_display.get())
        messagebox.showinfo("成功", "命令已复制！")

    def run_cmd(self):
        if not os.path.exists("sqlmap.py"):
            if not messagebox.askyesno("文件缺失", "当前目录下未找到 sqlmap.py，是否继续执行？"):
                return
        
        raw_content = self.get_raw_content()
        if raw_content:
            try:
                with open("request.txt", "w", encoding="utf-8") as f:
                    f.write(raw_content)
            except Exception as e:
                messagebox.showerror("错误", f"无法写入 request.txt: {e}")
                return
        elif not self.url_var.get().strip():
            messagebox.showwarning("提示", "请输入 URL 或粘贴数据包")
            return

        final_cmd = self.cmd_display.get()
        if platform.system() == "Windows":
            os.system(f'start cmd /k "{final_cmd}"')
        else:
            messagebox.showinfo("提示", "非Windows系统，命令已复制。")
            self.copy_cmd()

if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    app = UltimateSqlmapLauncher(root)
    root.mainloop()
