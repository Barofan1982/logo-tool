# CLAUDE.md — Logo Tool 批量加水印工具

## 项目概述
图片批量添加 Logo 和下载栏水印工具，支持 GUI 和命令行两种模式。

## 技术栈
- Python 3.12+ / tkinter / Pillow
- PyInstaller 打包为 exe

## 文件结构
```
logo_gui.py       # GUI 主程序
add_logo.py       # 命令行版本
run_gui.vbs       # 静默启动（自动探测 Python 路径）
LogoTool.spec     # PyInstaller 打包配置
```

## 功能要点
- 双水印叠加（Logo + 下载栏）
- 四角定位（左上、右上、左下、右下）
- 单张 / 批量文件夹处理
- 自动防覆盖（同名文件追加 `_1`、`_2` 编号）
- 支持 JPG、PNG、WEBP、BMP、TIFF

## 规则
- **未经用户明确许可，不得擅自重建 exe**

## Approach
- Think before acting. Read existing files before writing code.
- Be concise in output but thorough in reasoning.
- Prefer editing over rewriting whole files.
- Do not re-read files you have already read unless the file may have changed.
- Test your code before declaring done.
- No sycophantic openers or closing fluff.
- Keep solutions simple and direct.
- User instructions always override this file.
