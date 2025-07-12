# 视音频分割器

一个简洁、高效的桌面应用，用于快速分割视频和音频文件。基于 Python、pywebview 和 ffmpeg 构建，提供清爽的用户界面和流畅的操作体验。

## ✨ 主要功能

- **文件支持**: 支持导入 `MP4`, `MOV`, `MP3`, `WAV` 格式的文件。
- **时间戳分割**: 输入多个时间点（如 `MM:SS` 或 `HH:MM:SS`），应用会自动将文件在这些时间点进行切割。
- **灵活的导出选项**:
  - 仅分割视频（速度最快）。
  - 分割视频，并同时提取对应的 `MP3` 音频。
  - 从视频中仅提取并分割音频为 `MP3`。
- **拖拽上传**: 支持拖拽文件到应用窗口直接加载。
- **跨平台**: 基于 Web 技术，可打包为 Windows 和 macOS 应用。

## 🛠️ 技术栈

- **后端**: Python
- **GUI框架**: `pywebview` (一个使用 WebView 组件构建桌面应用的库)
- **Web框架**: `Flask` (用于后端逻辑处理)
- **核心处理**: `ffmpeg` (用于所有音视频操作)
- **前端**: HTML, `TailwindCSS`, JavaScript

## 🚀 如何使用

1.  **启动应用**: 打开应用。
2.  **选择文件**: 点击“选择文件”按钮或直接将文件拖拽到窗口中。
3.  **输入时间戳**: 在输入框中添加一个或多个分割时间点，按 `空格`、`回车` 或 `逗号` 确认。
4.  **选择导出选项**: 根据需要勾选“同时导出音频”或“仅导出音频”。
5.  **开始分割**: 点击“开始分割”按钮。
6.  **完成**: 分割后的文件将保存在与原始文件相同的目录下。

## 📦 安装与运行

### 先决条件

- Python 3.x
- `ffmpeg` 必须安装并配置在系统的 PATH 中。

### 从源码运行

1.  **克隆仓库**
    ```bash
    git clone https://github.com/your-username/video_spliter.git
    cd video_spliter
    ```

2.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

3.  **运行应用**
    ```bash
    python app.py
    ```

### 打包为应用

如果您想将此项目打包为可执行的桌面应用，可以使用 `pyinstaller`：

```bash
# 安装 pyinstaller
pip install pyinstaller

# 使用提供的 .spec 文件进行打包
pyinstaller app.spec
