import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

POSITIONS = ["左上", "右上", "左下", "右下"]


def resolve_output_path(output_path):
    if not os.path.exists(output_path):
        return output_path
    base, ext = os.path.splitext(output_path)
    counter = 1
    while os.path.exists(f"{base}_{counter}{ext}"):
        counter += 1
    return f"{base}_{counter}{ext}"


def calc_xy(pos, img_w, img_h, overlay_w, overlay_h, padding):
    if pos == "左上":
        return padding, padding
    elif pos == "右上":
        return img_w - overlay_w - padding, padding
    elif pos == "左下":
        return padding, img_h - overlay_h - padding
    elif pos == "右下":
        return img_w - overlay_w - padding, img_h - overlay_h - padding


def add_overlays(image_path, logo, logo_pos, bar, bar_pos, output_path=None, padding=20):
    base_img = Image.open(image_path).convert("RGBA")
    base_w, base_h = base_img.size
    composite = base_img.copy()

    lx, ly = calc_xy(logo_pos, base_w, base_h, logo.width, logo.height, padding)
    composite.paste(logo, (lx, ly), mask=logo)

    bx, by = calc_xy(bar_pos, base_w, base_h, bar.width, bar.height, padding)
    composite.paste(bar, (bx, by), mask=bar)

    if output_path is None:
        base, ext = os.path.splitext(image_path)
        output_path = f"{base}_with_logo.png"

    output_path = resolve_output_path(output_path)

    if output_path.lower().endswith(".png"):
        composite.save(output_path, format="PNG")
    else:
        composite.convert("RGB").save(output_path)

    return output_path


class PositionPicker(ttk.LabelFrame):
    """四个角的位置选择器（2×2 单选按钮），支持禁用某个选项"""
    def __init__(self, parent, label, default, on_change=None, **kwargs):
        super().__init__(parent, text=label, padding=6, **kwargs)
        self.var = tk.StringVar(value=default)
        self._on_change = on_change
        self._buttons = {}
        positions = [("左上", 0, 0), ("右上", 0, 1),
                     ("左下", 1, 0), ("右下", 1, 1)]
        for text, row, col in positions:
            btn = ttk.Radiobutton(self, text=text, variable=self.var, value=text,
                                  command=self._changed)
            btn.grid(row=row, column=col, padx=8, pady=2, sticky="w")
            self._buttons[text] = btn

    def _changed(self):
        if self._on_change:
            self._on_change()

    def get(self):
        return self.var.get()

    def disable_option(self, pos):
        """禁用某个位置按钮（对方已占用）"""
        self._buttons[pos].configure(state="disabled")

    def enable_option(self, pos):
        """启用某个位置按钮"""
        self._buttons[pos].configure(state="normal")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Logo 添加工具")
        self.resizable(False, False)
        self._build()

    def _build(self):
        pad = {"padx": 10, "pady": 6}

        # ── 文件输入区 ──
        file_frame = ttk.LabelFrame(self, text="文件", padding=10)
        file_frame.grid(row=0, column=0, columnspan=2, sticky="ew", **pad)

        self.image_var = tk.StringVar()
        self.logo_var  = tk.StringVar()
        self.bar_var   = tk.StringVar()
        self.out_var   = tk.StringVar()
        self.padding_var = tk.IntVar(value=20)

        rows = [
            ("图片 / 目录",      self.image_var, self._pick_image),
            ("Logo PNG",         self.logo_var,  lambda: self._pick_file(self.logo_var)),
            ("下载栏 PNG",       self.bar_var,   lambda: self._pick_file(self.bar_var)),
            ("输出目录（可选）", self.out_var,   self._pick_outdir),
        ]
        for i, (label, var, cmd) in enumerate(rows):
            ttk.Label(file_frame, text=label, width=14, anchor="e").grid(row=i, column=0, sticky="e")
            ttk.Entry(file_frame, textvariable=var, width=42).grid(row=i, column=1, padx=4)
            ttk.Button(file_frame, text="浏览", command=cmd, width=6).grid(row=i, column=2)

        ttk.Label(file_frame, text="边距 (px)", width=14, anchor="e").grid(row=4, column=0, sticky="e")
        ttk.Spinbox(file_frame, from_=0, to=200, textvariable=self.padding_var, width=6).grid(
            row=4, column=1, sticky="w", padx=4)

        # ── 位置选择区 ──
        self.logo_pos = PositionPicker(self, "Logo 位置", default="左上",
                                       on_change=self._sync_positions)
        self.logo_pos.grid(row=1, column=0, padx=10, pady=(0, 6), sticky="n")

        self.bar_pos = PositionPicker(self, "下载栏位置", default="右下",
                                      on_change=self._sync_positions)
        self.bar_pos.grid(row=1, column=1, padx=10, pady=(0, 6), sticky="n")

        # 初始化：互相禁用对方已选的位置
        self._sync_positions()

        # ── 开始按钮 ──
        self.btn = ttk.Button(self, text="开始处理", command=self._start)
        self.btn.grid(row=2, column=0, columnspan=2, pady=(0, 6))

        # ── 进度条 ──
        self.progress = ttk.Progressbar(self, length=460, mode="determinate")
        self.progress.grid(row=3, column=0, columnspan=2, padx=10, pady=(0, 4))

        # ── 日志 ──
        log_frame = ttk.LabelFrame(self, text="日志", padding=6)
        log_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10))
        self.log = tk.Text(log_frame, height=10, width=62, state="disabled", wrap="word")
        sb = ttk.Scrollbar(log_frame, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        self.log.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")

    def _sync_positions(self):
        """任意一侧改变时，重新同步禁用状态"""
        logo_sel = self.logo_pos.get()
        bar_sel  = self.bar_pos.get()
        for pos in POSITIONS:
            self.logo_pos.enable_option(pos)
            self.bar_pos.enable_option(pos)
        # 各自禁用对方当前选中的位置
        self.logo_pos.disable_option(bar_sel)
        self.bar_pos.disable_option(logo_sel)

    def _pick_image(self):
        path = filedialog.askdirectory(title="选择图片目录")
        if not path:
            path = filedialog.askopenfilename(
                title="或选择单张图片",
                filetypes=[("图片文件", "*.jpg *.jpeg *.png *.webp *.bmp *.tiff")]
            )
        if path:
            self.image_var.set(path)

    def _pick_file(self, var):
        path = filedialog.askopenfilename(filetypes=[("PNG 文件", "*.png")])
        if path:
            var.set(path)

    def _pick_outdir(self):
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            self.out_var.set(path)

    def _log(self, msg):
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _start(self):
        image = self.image_var.get().strip()
        logo  = self.logo_var.get().strip()
        bar   = self.bar_var.get().strip()

        if not image or not logo or not bar:
            messagebox.showwarning("缺少输入", "请先选择图片/目录、Logo 和下载栏。")
            return

        self.btn.configure(state="disabled")
        self.progress["value"] = 0
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        image    = self.image_var.get().strip()
        logo     = self.logo_var.get().strip()
        bar      = self.bar_var.get().strip()
        out_dir  = self.out_var.get().strip() or None
        padding  = self.padding_var.get()
        logo_pos = self.logo_pos.get()
        bar_pos  = self.bar_pos.get()

        try:
            logo_img = Image.open(logo).convert("RGBA")
            bar_img  = Image.open(bar).convert("RGBA")
        except Exception as e:
            self._log(f"[错误] 加载素材失败: {e}")
            self.btn.configure(state="normal")
            return

        self._log(f"Logo → {logo_pos}，下载栏 → {bar_pos}\n")

        if os.path.isdir(image):
            files = [f for f in os.listdir(image)
                     if os.path.splitext(f)[1].lower() in SUPPORTED_EXTS]
            if not files:
                self._log("[错误] 目录中没有支持的图片文件。")
                self.btn.configure(state="normal")
                return

            save_dir = out_dir or os.path.join(image, "output")
            os.makedirs(save_dir, exist_ok=True)
            self._log(f"找到 {len(files)} 张图片，输出到: {save_dir}\n")
            self.progress["maximum"] = len(files)

            for i, fname in enumerate(files, 1):
                src = os.path.join(image, fname)
                base, _ = os.path.splitext(fname)
                dst = os.path.join(save_dir, f"{base}_with_logo.png")
                try:
                    result = add_overlays(src, logo_img, logo_pos, bar_img, bar_pos,
                                          output_path=dst, padding=padding)
                    self._log(f"[{i}/{len(files)}] ✓ {os.path.basename(result)}")
                except Exception as e:
                    self._log(f"[{i}/{len(files)}] ✗ {fname}: {e}")
                self.progress["value"] = i

            self._log(f"\n全部完成，共处理 {len(files)} 张。")

        else:
            self.progress["maximum"] = 1
            dst = None
            if out_dir:
                base, _ = os.path.splitext(os.path.basename(image))
                dst = os.path.join(out_dir, f"{base}_with_logo.png")
            try:
                result = add_overlays(image, logo_img, logo_pos, bar_img, bar_pos,
                                      output_path=dst, padding=padding)
                self._log(f"✓ 已保存: {result}")
            except Exception as e:
                self._log(f"✗ 失败: {e}")
            self.progress["value"] = 1

        self.btn.configure(state="normal")


if __name__ == "__main__":
    app = App()
    app.mainloop()
