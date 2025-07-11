#!/usr/bin/env python3
"""
build_app.py

自动化打包脚本：将 Flask + pywebview 项目打包为 macOS 可用的 .app 应用。

功能：
- 自动检测 PyInstaller 是否安装
- 支持自定义图标（可选）
- 自动包含 templates 文件夹
- 兼容 Flask-SocketIO、pywebview、moviepy
- 详细命令行参数说明
- 自动处理 RecursionError（递归深度问题）

用法：
    python build_app.py [--icon youricon.icns] [--clean]

依赖：
    pip install pyinstaller

注意：
    需确保 ffmpeg 已在系统可用（brew install ffmpeg）
"""
import os
import sys
import subprocess
import shutil
import argparse

APP_NAME = "app"
ENTRY_SCRIPT = "app.py"
TEMPLATES_DIR = "templates"
SPEC_FILE = f"{APP_NAME}.spec"


def check_pyinstaller():
    """检查 PyInstaller 是否已安装。"""
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("[INFO] 未检测到 PyInstaller，正在自动安装...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])


def clean_build():
    """清理 build/ dist/ __pycache__ 等临时文件。"""
    for folder in ["build", "dist", "__pycache__"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
    if os.path.exists(SPEC_FILE):
        os.remove(SPEC_FILE)


def ensure_spec_file(icon_path=None):
    """
    如果 .spec 文件不存在，先用 pyinstaller 生成一次。
    :param icon_path: 可选，.icns 图标文件路径
    """
    if not os.path.exists(SPEC_FILE):
        hidden_imports = [  # 移除这里的逗号错误
            'flask',
            'flask_socketio',
            'pywebview',
            'pywebview.platforms.cocoa',
            'pywebview.platforms.qt',
            'pywebview.platforms.gtk',
            'moviepy.editor',
            'moviepy.video.io.ffmpeg_reader',
            'moviepy.video.io.ffmpeg_writer',
            'moviepy.audio.io.ffmpeg_audiowriter',
            'imageio',
            'imageio_ffmpeg',
            'PIL',
            # Add more moviepy related modules to ensure they are included
            'moviepy.video.fx.all',
            'moviepy.audio.fx.all',
            'moviepy.video.compositing.CompositeVideoClip',
            'numpy'
        ]  # 这里不需要逗号
        # Add templates folder
        cmd = [
            "pyinstaller",
            "--noconfirm",
            "--windowed",
            f"--add-data={TEMPLATES_DIR}:{TEMPLATES_DIR}",
        ]
        for imp in hidden_imports:
            cmd.append(f"--hidden-import={imp}")
        
        cmd.append(ENTRY_SCRIPT)

        if icon_path:
            cmd.insert(-1, f"--icon={icon_path}")
        print(f"[INFO] 生成 .spec 文件: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)


def patch_spec_file():
    """
    在 .spec 文件顶部插入递归深度设置，防止 RecursionError。
    """
    if not os.path.exists(SPEC_FILE):
        raise FileNotFoundError(f"未找到 {SPEC_FILE}")
    with open(SPEC_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    # 检查是否已插入递归设置
    patch_line = "import sys ; sys.setrecursionlimit(sys.getrecursionlimit() * 5)\n"
    if not any("setrecursionlimit" in l for l in lines[:3]):
        lines.insert(0, patch_line)
        with open(SPEC_FILE, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"[INFO] 已自动修正递归深度设置到 {SPEC_FILE}")
    else:
        print(f"[INFO] {SPEC_FILE} 已包含递归深度设置，无需重复插入。")


def build_with_spec():
    """
    用 .spec 文件重新打包。
    """
    cmd = ["pyinstaller", SPEC_FILE]
    print(f"[INFO] 用 .spec 文件重新打包: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    print(f"[SUCCESS] 打包完成，应用位于 dist/{APP_NAME}.app")


def main():
    parser = argparse.ArgumentParser(description="自动化打包 Flask+pywebview 项目为 macOS 应用")
    parser.add_argument("--icon", type=str, default=None, help="自定义 .icns 图标文件路径（可选）")
    parser.add_argument("--clean", action="store_true", help="打包前先清理旧的 build/dist 文件夹")
    args = parser.parse_args()

    if args.clean:
        print("[INFO] 正在清理旧的构建文件...")
        clean_build()

    check_pyinstaller()
    ensure_spec_file(icon_path=args.icon)
    patch_spec_file()
    build_with_spec()


if __name__ == "__main__":
    main()