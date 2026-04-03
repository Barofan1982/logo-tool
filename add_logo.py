from PIL import Image
import argparse
import os

SUPPORTED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}


def resolve_output_path(output_path):
    """若文件已存在，自动追加 _1 _2 ..."""
    if not os.path.exists(output_path):
        return output_path
    base, ext = os.path.splitext(output_path)
    counter = 1
    while os.path.exists(f"{base}_{counter}{ext}"):
        counter += 1
    new_path = f"{base}_{counter}{ext}"
    print(f"  已存在同名文件，自动重命名为: {os.path.basename(new_path)}")
    return new_path


def add_overlays(image_path, logo, bar, output_path=None, padding=20):
    """
    左上角放 logo，右下角放下载栏（均使用原始尺寸）
    logo/bar 可传已打开的 Image 对象，避免批量处理时重复读取。
    """
    base_img = Image.open(image_path).convert("RGBA")
    base_w, base_h = base_img.size
    composite = base_img.copy()

    # 左上角：logo
    composite.paste(logo, (padding, padding), mask=logo)
    print(f"  logo    → 左上角 ({padding}, {padding})，尺寸 {logo.size}")

    # 右下角：下载栏
    bar_x = base_w - bar.width - padding
    bar_y = base_h - bar.height - padding
    composite.paste(bar, (bar_x, bar_y), mask=bar)
    print(f"  下载栏  → 右下角 ({bar_x}, {bar_y})，尺寸 {bar.size}")

    # 确定输出路径
    if output_path is None:
        base, ext = os.path.splitext(image_path)
        output_path = f"{base}_with_logo.png"

    output_path = resolve_output_path(output_path)

    if output_path.lower().endswith(".png"):
        composite.save(output_path, format="PNG")
    else:
        composite.convert("RGB").save(output_path)

    print(f"  已保存: {output_path}\n")
    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="左上角加 logo，右下角加下载栏；支持单张图片或整个目录")
    parser.add_argument("image", help="原始图片路径，或包含图片的目录")
    parser.add_argument("logo", help="Logo PNG 路径（左上角）")
    parser.add_argument("bar", help="下载栏 PNG 路径（右下角）")
    parser.add_argument("-o", "--output", help="输出路径：单图时指定文件名，目录时指定输出目录（可选）", default=None)
    parser.add_argument("-p", "--padding", type=int, default=20, help="距边缘像素距离，默认 20")
    parser.add_argument("--invoke-dir", default=None, help=argparse.SUPPRESS)

    args = parser.parse_args()

    def resolve(path):
        if os.path.isabs(path):
            return path
        base = args.invoke_dir if args.invoke_dir else os.getcwd()
        return os.path.join(base, path)

    args.image = resolve(args.image)
    args.logo  = resolve(args.logo)
    args.bar   = resolve(args.bar)
    if args.output:
        args.output = resolve(args.output)

    # 预加载 logo 和下载栏（批量时只读一次）
    logo_img = Image.open(args.logo).convert("RGBA")
    bar_img = Image.open(args.bar).convert("RGBA")

    if os.path.isdir(args.image):
        # ── 目录模式 ──
        image_files = [
            f for f in os.listdir(args.image)
            if os.path.splitext(f)[1].lower() in SUPPORTED_EXTS
        ]
        if not image_files:
            print(f"目录 {args.image} 中没有找到支持的图片文件。")
            exit(1)

        # 输出目录：默认在原目录下建 output 子文件夹
        out_dir = args.output if args.output else os.path.join(args.image, "output")
        os.makedirs(out_dir, exist_ok=True)

        print(f"目录模式：共找到 {len(image_files)} 张图片，输出到 {out_dir}\n")
        for i, fname in enumerate(image_files, 1):
            src = os.path.join(args.image, fname)
            base, _ = os.path.splitext(fname)
            dst = os.path.join(out_dir, f"{base}_with_logo.png")
            print(f"[{i}/{len(image_files)}] {fname}")
            add_overlays(src, logo_img, bar_img, output_path=dst, padding=args.padding)

        print(f"全部完成，共处理 {len(image_files)} 张。")

    else:
        # ── 单图模式 ──
        print(f"图片:   {args.image}")
        print(f"Logo:   {args.logo}")
        print(f"下载栏: {args.bar}")
        print(f"边距:   {args.padding}px\n")
        add_overlays(args.image, logo_img, bar_img, output_path=args.output, padding=args.padding)
