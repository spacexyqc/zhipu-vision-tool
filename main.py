"""
# ================================================
# 🧠 智谱 AI 多图分析工具 - 优化版 v3.1
# 文件名: zhipu_vision_tool_v3.py
# 版本: v3.1 (支持配置保存)
# 作者: XYQC and Qwen (Alibaba Cloud)
# 日期: 2025-08-20
# ================================================
"""
import os
import base64
import threading
import time
import json  # 新增：用于配置保存
from tkinter import *
from tkinter import filedialog, scrolledtext, messagebox
from zai import ZhipuAiClient
from concurrent.futures import ThreadPoolExecutor, as_completed

# ======================
# 🌑 暗色主题配色
# ======================
DARK_BG = "#1e1e1e"
DARK_FG = "#dcdcdc"
DARK_FRAME = "#2d2d2d"
BUTTON_HOVER = "#0066cc"
ACCENT_GREEN = "#28a745"
ACCENT_BLUE = "#007ACC"
ACCENT_TEAL = "#17a2b8"
PROGRESS_BG = "#333"
PROGRESS_FILL = "#4CAF50"

# ✅ 配置文件路径（保存在用户主目录，兼容 exe 打包）
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".zhipu_vision_tool_config.json")

class ZhipuVisionTool:
    def __init__(self, root):
        self.root = root
        self.root.title("🧠 智谱 AI 多图分析工具 (v3.1) 🚀")
        self.root.geometry("1020x860")
        self.root.configure(bg=DARK_BG)
        self.image_paths = []
        self.results = {}
        self.completed_count = 0
        self.total_count = 0
        self.current_output_dir = None
        self.setup_ui()
        self.setup_drag_drop()
        self.load_config()  # ✅ 启动时加载上次配置

    def setup_ui(self):
        title = Label(self.root, text="智谱 AI 多图分析工具", font=("Arial", 14, "bold"), bg=DARK_BG, fg="#ffffff")
        title.pack(pady=8)

        param_frame = LabelFrame(self.root, text="🔧 配置参数", padx=10, pady=10, bg=DARK_FRAME, fg=DARK_FG, font=("Arial", 9))
        param_frame.pack(padx=12, pady=6, fill=X)

        # API Key
        Label(param_frame, text="API Key:", font=("Arial", 9), bg=DARK_FRAME, fg=DARK_FG).grid(row=0, column=0, sticky=W, padx=5, pady=2)
        self.api_key_var = StringVar()
        api_entry = Entry(param_frame, textvariable=self.api_key_var, width=70, font=("Arial", 9), show="*")
        api_entry.config(bg="#2a2a2a", fg=DARK_FG, insertbackground="white", highlightthickness=1, highlightbackground="#444")
        api_entry.grid(row=0, column=1, padx=5, pady=2)

        # 模型名称
        Label(param_frame, text="模型名称:", font=("Arial", 9), bg=DARK_FRAME, fg=DARK_FG).grid(row=1, column=0, sticky=W, padx=5, pady=2)
        self.model_var = StringVar()
        model_entry = Entry(param_frame, textvariable=self.model_var, width=70, font=("Arial", 9))
        model_entry.config(bg="#2a2a2a", fg=DARK_FG, insertbackground="white", highlightthickness=1, highlightbackground="#444")
        model_entry.grid(row=1, column=1, padx=5, pady=2)

        # 系统提示词
        Label(param_frame, text="系统提示词:", font=("Arial", 9), bg=DARK_FRAME, fg=DARK_FG).grid(row=2, column=0, sticky=NW, padx=5, pady=2)
        sys_frame = Frame(param_frame, bg=DARK_FRAME)
        sys_frame.grid(row=2, column=1, padx=5, pady=2, sticky=EW)
        self.system_text = Text(sys_frame, height=3, width=70, font=("Arial", 9), wrap=WORD, bg="#2a2a2a", fg=DARK_FG, insertbackground="white")
        sys_scroll = Scrollbar(sys_frame, orient=VERTICAL, command=self.system_text.yview, bg=DARK_FRAME)
        self.system_text.configure(yscrollcommand=sys_scroll.set)
        self.system_text.pack(side=LEFT, fill=BOTH, expand=True)
        sys_scroll.pack(side=RIGHT, fill=Y)

        # 用户问题
        Label(param_frame, text="用户问题:", font=("Arial", 9), bg=DARK_FRAME, fg=DARK_FG).grid(row=3, column=0, sticky=NW, padx=5, pady=2)
        user_frame = Frame(param_frame, bg=DARK_FRAME)
        user_frame.grid(row=3, column=1, padx=5, pady=2, sticky=EW)
        self.user_text = Text(user_frame, height=4, width=70, font=("Arial", 9), wrap=WORD, bg="#2a2a2a", fg=DARK_FG, insertbackground="white")
        user_scroll = Scrollbar(user_frame, orient=VERTICAL, command=self.user_text.yview, bg=DARK_FRAME)
        self.user_text.configure(yscrollcommand=user_scroll.set)
        self.user_text.pack(side=LEFT, fill=BOTH, expand=True)
        user_scroll.pack(side=RIGHT, fill=Y)

        param_frame.grid_columnconfigure(1, weight=1)

        # === 按钮区域 ===
        btn_frame = Frame(self.root, bg=DARK_BG)
        btn_frame.pack(pady=5)
        Button(btn_frame, text="📁 选择图片", command=self.select_images, width=12, bg=ACCENT_BLUE, fg="white", relief=FLAT).pack(side=LEFT, padx=6)
        Button(btn_frame, text="🚀 开始分析", command=self.start_analysis, width=12, bg=ACCENT_GREEN, fg="white", relief=FLAT).pack(side=LEFT, padx=6)
        Button(btn_frame, text="🗑️ 清空结果", command=self.clear_all, width=12, bg="#dc3545", fg="white", relief=FLAT).pack(side=LEFT, padx=6)
        Button(btn_frame, text="📁 打开结果", command=self.open_output_folder, width=12, bg=ACCENT_TEAL, fg="white", relief=FLAT).pack(side=LEFT, padx=6)

        # 图片列表
        Label(self.root, text="📎 已选图片:", font=("Arial", 9, "bold"), bg=DARK_BG, fg=DARK_FG).pack(anchor=W, padx=15, pady=(10, 5))
        self.listbox = Listbox(self.root, height=6, font=("Consolas", 10), bg="#2a2a2a", fg=DARK_FG, selectbackground="#0066cc")
        self.listbox.pack(fill=X, padx=10, pady=5)

        # 进度条
        progress_frame = Frame(self.root, bg=DARK_BG)
        progress_frame.pack(pady=5, fill=X, padx=10)
        self.progress_label = Label(progress_frame, text="进度：0/0", font=("Arial", 9), bg=DARK_BG, fg=DARK_FG)
        self.progress_label.pack(side=LEFT)
        self.progress_bar = Canvas(progress_frame, height=12, bg=PROGRESS_BG, width=400, highlightthickness=0)
        self.progress_bar.pack(side=LEFT, fill=X, expand=True, padx=10)
        self.progress_rect = self.progress_bar.create_rectangle(0, 0, 0, 12, fill=PROGRESS_FILL, outline="")

        # 结果区域
        Label(self.root, text="🔍 实时分析结果:", font=("Arial", 9, "bold"), bg=DARK_BG, fg=DARK_FG).pack(anchor=W, padx=15, pady=(10, 5))
        self.result_area = scrolledtext.ScrolledText(
            self.root, height=18, font=("Consolas", 10), wrap=WORD,
            bg="#2a2a2a", fg=DARK_FG, insertbackground="white"
        )
        self.result_area.pack(fill=BOTH, expand=True, padx=10, pady=5)

    def setup_drag_drop(self):
        try:
            from tkinter import dnd
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.on_drop)
        except:
            pass

    def on_drop(self, event):
        data = self.root.tk.splitlist(event.data)
        image_paths = []
        for item in data:
            ext = os.path.splitext(item)[1].lower()
            if ext in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
                image_paths.append(item)
        if image_paths:
            self.image_paths.extend(image_paths)
            self.update_listbox()

    def update_listbox(self):
        self.listbox.delete(0, END)
        for p in self.image_paths:
            self.listbox.insert(END, os.path.basename(p))

    def select_images(self):
        paths = filedialog.askopenfilenames(
            title="选择一张或多张图片",
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.webp")]
        )
        if paths:
            self.image_paths.extend(paths)
            self.update_listbox()

    def clean_text(self, text):
        if not isinstance(text, str):
            return str(text)
        text = text.replace("<|begin_of_box|>", "").replace("<|end_of_box|>", "")
        text = text.replace("<|begin_of_thought|>", "").replace("<|end_of_thought|>", "")
        return text.strip()

    def encode_image_to_base64_url(self, image_path):
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        ext = os.path.splitext(image_path)[1].lower()
        mime = "image/jpeg"
        if ext == ".png": mime = "image/png"
        elif ext == ".webp": mime = "image/webp"
        return f"data:{mime};base64,{b64}"

    def call_single_image(self, index, image_path, api_key, model, system_prompt, user_prompt):
        try:
            client = ZhipuAiClient(api_key=api_key)
            image_url = self.encode_image_to_base64_url(image_path)
            messages = []
            if system_prompt.strip():
                messages.append({"role": "system", "content": system_prompt})
            messages.append({
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_url}},
                    {"type": "text", "text": user_prompt}
                ]
            })
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                thinking={"type": "enabled"}
            )
            msg = response.choices[0].message
            content = self.clean_text(getattr(msg, 'content', '无内容'))
            thinking = self.clean_text(getattr(msg, 'thinking', 'N/A'))
            return {
                "index": index,
                "image_path": image_path,
                "content": content,
                "thinking": thinking,
                "success": True,
                "error": None
            }
        except Exception as e:
            return {
                "index": index,
                "image_path": image_path,
                "content": None,
                "thinking": None,
                "success": False,
                "error": str(e)
            }

    def start_analysis(self):
        if not self.image_paths:
            messagebox.showwarning("⚠️ 警告", "请先选择至少一张图片！")
            return
        api_key = self.api_key_var.get().strip()
        model = self.model_var.get().strip()
        system_prompt = self.system_text.get(1.0, END).strip()
        user_prompt = self.user_text.get(1.0, END).strip()
        if not api_key:
            messagebox.showerror("❌ 错误", "API Key 不能为空！")
            return

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        desktop = os.path.expanduser("~/Desktop")
        output_dir = os.path.join(desktop, f"zhipu_ai_analysis_{timestamp}")
        os.makedirs(output_dir, exist_ok=True)
        self.current_output_dir = output_dir
        self.result_area.delete(1.0, END)
        self.result_area.insert(END, f"🔄 开始分析，结果将保存至：\n{output_dir}\n\n")
        self.set_buttons_state(DISABLED)
        self.results.clear()
        self.completed_count = 0
        self.total_count = len(self.image_paths)
        self.update_progress()

        thread = threading.Thread(
            target=self.run_analysis,
            args=(api_key, model, system_prompt, user_prompt, output_dir),
            daemon=True
        )
        thread.start()

    def run_analysis(self, api_key, model, system_prompt, user_prompt, output_dir):
        try:
            with ThreadPoolExecutor(max_workers=min(5, len(self.image_paths))) as executor:
                futures = {
                    executor.submit(
                        self.call_single_image, idx, img_path, api_key, model, system_prompt, user_prompt
                    ): idx for idx, img_path in enumerate(self.image_paths, 1)
                }
                for future in as_completed(futures):
                    result = future.result()
                    self.root.after(0, self.update_ui_with_result, result, output_dir)
                    self.completed_count += 1
                    self.update_progress()
        finally:
            # ✅ 无论成功失败，都恢复按钮 + 保存配置
            self.root.after(0, self.set_buttons_state, NORMAL)
            self.root.after(0, self.save_config)  # 保存当前配置

    def update_ui_with_result(self, result, output_dir):
        index = result["index"]
        src_path = result["image_path"]
        basename = os.path.basename(src_path)
        img_dst = os.path.join(output_dir, f"{index}.jpg")
        try:
            from shutil import copyfile
            copyfile(src_path, img_dst)
        except Exception as e:
            img_dst = f"复制失败: {e}"
        txt_dst = os.path.join(output_dir, f"{index}.txt")
        content = result["content"] if result["success"] else f"❌ 错误: {result['error']}"
        try:
            with open(txt_dst, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            content = f"保存失败: {e}"
        display = f"📌【完成 {index}】 {basename}\n"
        if result["success"]:
            display += f"💬 回答：\n{result['content']}\n"
            if result['thinking'] != 'N/A':
                display += f"🧠 思考：{result['thinking']}\n"
        else:
            display += f"❌ 失败：{result['error']}\n"
        display += f"💾 已保存 → {index}.jpg & {index}.txt\n"
        display += "─" * 60 + "\n"
        self.result_area.insert(END, display)
        self.result_area.see(END)

    def update_progress(self):
        self.progress_label.config(text=f"进度：{self.completed_count}/{self.total_count}")
        if self.total_count > 0:
            width = max(1, self.progress_bar.winfo_width())
            filled = int((self.completed_count / self.total_count) * width)
            self.progress_bar.coords(self.progress_rect, 0, 0, filled, 12)
        self.root.update_idletasks()

    def open_output_folder(self):
        if self.current_output_dir and os.path.exists(self.current_output_dir):
            os.startfile(self.current_output_dir)
        else:
            messagebox.showinfo("ℹ️", "暂无结果文件夹。")

    def clear_all(self):
        self.image_paths.clear()
        self.listbox.delete(0, END)
        self.result_area.delete(1.0, END)
        self.progress_label.config(text="进度：0/0")
        self.progress_bar.coords(self.progress_rect, 0, 0, 0, 12)
        self.current_output_dir = None
        self.set_buttons_state(NORMAL)
        self.results.clear()
        self.completed_count = 0
        self.total_count = 0
        messagebox.showinfo("✅", "已清空所有内容，可重新开始。")

    def set_buttons_state(self, state):
        for widget in self.root.winfo_children():
            if isinstance(widget, Frame):
                for btn in widget.winfo_children():
                    if isinstance(btn, Button):
                        btn.config(state=state)

    # ✅ 新增：保存配置
    def save_config(self):
        config = {
            "api_key": self.api_key_var.get(),
            "model": self.model_var.get(),
            "system_prompt": self.system_text.get(1.0, END).strip(),
            "user_prompt": self.user_text.get(1.0, END).strip(),
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ 配置保存失败: {e}")

    # ✅ 新增：加载配置
    def load_config(self):
        if not os.path.exists(CONFIG_FILE):
            # 设置默认值
            self.api_key_var.set("")
            self.model_var.set("glm-4.5v")
            self.system_text.insert(END, "你是一个强大的图文理解助手。")
            self.user_text.insert(END, "请描述图片内容，并在需要时提供物体坐标 [[xmin,ymin,xmax,ymax]]。")
            return
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            self.api_key_var.set(config.get("api_key", ""))
            self.model_var.set(config.get("model", "glm-4.5v"))
            self.system_text.delete(1.0, END)
            self.system_text.insert(END, config.get("system_prompt", "你是一个强大的图文理解助手。"))
            self.user_text.delete(1.0, END)
            self.user_text.insert(END, config.get("user_prompt", "请描述图片内容，并在需要时提供物体坐标 [[xmin,ymin,xmax,ymax]]。"))
        except Exception as e:
            print(f"⚠️ 配置读取失败: {e}")
            # 失败时也设默认值
            self.api_key_var.set("")
            self.model_var.set("glm-4.5v")
            self.system_text.insert(END, "你是一个强大的图文理解助手。")
            self.user_text.insert(END, "请描述图片内容，并在需要时提供物体坐标 [[xmin,ymin,xmax,ymax]]。")

# ======================
# ✅ 启动程序
# ======================
if __name__ == "__main__":
    root = Tk()
    root.configure(bg=DARK_BG)
    app = ZhipuVisionTool(root)

    root.mainloop()
