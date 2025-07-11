# -*- coding: utf-8 -*-

import os
import sys
import traceback
import webview
from flask import Flask, render_template
import time
import subprocess
import json
import threading

# --- 全局变量 ---
# 用于在 pywebview 和 Flask 之间共享状态
class Api:
    def __init__(self):
        self._window = None
        self.file_path = None

    def set_window(self, window):
        self._window = window

    def get_video_duration(self, file_path):
        """
        使用 ffprobe 获取视频时长
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                file_path
            ]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if result.returncode != 0:
                raise Exception(f"ffprobe 执行失败: {result.stderr}")
            data = json.loads(result.stdout)
            duration = float(data['format']['duration'])
            return duration
        except Exception as e:
            raise Exception(f"获取视频时长失败: {str(e)}")

    def select_file(self):
        """
        打开一个文件对话框让用户选择 MP4 文件。
        此函数由前端 JavaScript 调用。
        """
        file_types = ('MP4 视频 (*.mp4)',)
        result = self._window.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
        if result and len(result) > 0:
            self.file_path = result[0]
            try:
                duration = self.get_video_duration(self.file_path)
                filename = os.path.basename(self.file_path)
                self._window.evaluate_js(f'handleFileSelected("{filename}", {duration})')
            except Exception as e:
                error_message = str(e).replace('"', "'").replace('\\', '/')
                self._window.evaluate_js(f'handleError("无法读取视频文件: {error_message}")')
                self.file_path = None
        return None

    def start_split(self, timestamps, export_audio):
        """
        前端调用，启动分割任务。异步线程执行。
        """
        if not self.file_path:
            self._window.evaluate_js('onError("未选择视频文件")')
            return False
        if not timestamps:
            self._window.evaluate_js('onError("未提供时间戳")')
            return False
        # 启动后台线程
        t = threading.Thread(target=self.split_video_task, args=(self.file_path, timestamps, export_audio))
        t.start()
        return True

    def split_video_task(self, file_path, timestamps, export_audio):
        try:
            self._window.evaluate_js('onProgress("开始处理视频...", 0)')
            time.sleep(1)
            timestamps_list = [t.strip() for t in timestamps]
            split_points_in_seconds = [self.time_to_seconds(t) for t in timestamps_list]
            split_points_in_seconds = [t for t in split_points_in_seconds if t is not None]
            if not split_points_in_seconds:
                self._window.evaluate_js('onError("未提供有效的时间点")')
                return
            folder_path = os.path.dirname(file_path)
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            duration = self.get_video_duration(file_path)
            valid_split_points = sorted([t for t in split_points_in_seconds if t < duration])
            full_split_list = sorted(list(set([0] + valid_split_points + [duration])))
            total_parts = len(full_split_list) - 1
            if total_parts <= 0:
                self._window.evaluate_js('onError("没有有效的分割点")')
                return
            for i in range(total_parts):
                start_time = full_split_list[i]
                end_time = full_split_list[i+1]
                if start_time >= end_time:
                    continue
                part_num = i + 1
                output_video_filename = os.path.join(folder_path, f"{base_name}_part{part_num}.mp4")
                cmd = [
                    'ffmpeg',
                    '-y',
                    '-ss', str(start_time),
                    '-to', str(end_time),
                    '-i', file_path,
                    '-c', 'copy',
                    output_video_filename
                ]
                result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if result.returncode != 0:
                    error_msg = result.stderr.decode(errors='ignore')
                    self._window.evaluate_js(f'onError("ffmpeg 分割第{part_num}段失败: {error_msg}")')
                    continue
                if export_audio:
                    output_audio_filename = os.path.join(folder_path, f"{base_name}_part{part_num}.mp3")
                    cmd_audio = [
                        'ffmpeg',
                        '-y',
                        '-i', output_video_filename,
                        '-q:a', '0',
                        '-map', 'a',
                        output_audio_filename
                    ]
                    result_audio = subprocess.run(cmd_audio, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if result_audio.returncode != 0:
                        self._window.evaluate_js(f'onProgress("第{part_num}段无音频或导出mp3失败。", {int((part_num/total_parts)*100)})')
                    else:
                        self._window.evaluate_js(f'onProgress("第{part_num}段音频导出完成。", {int((part_num/total_parts)*100)})')
                else:
                    self._window.evaluate_js(f'onProgress("第{part_num}段视频分割完成。", {int((part_num/total_parts)*100)})')
            self._window.evaluate_js('onFinished("所有文件处理完毕！", 100)')
        except Exception as e:
            error_message = f"处理失败: {e}\n{traceback.format_exc()}"
            safe_error_message = error_message.replace('"', "'").replace('\\', '/').replace('\n', ' ')
            self._window.evaluate_js(f'onError("{safe_error_message}")')

    def time_to_seconds(self, time_str):
        try:
            parts = list(map(int, time_str.split(':')))
            if len(parts) == 3:
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
            elif len(parts) == 2:
                return parts[0] * 60 + parts[1]
            else:
                return None
        except (ValueError, IndexError):
            return None

api = Api()
app = Flask(__name__)

@app.route('/')
def index():
    """渲染主页面。"""
    return render_template('video_split.html')

if __name__ == '__main__':
    window = webview.create_window(
        '视频分割器',
        app,
        js_api=api,
        width=550,
        height=700,
        resizable=False
    )
    api.set_window(window)
    webview.start(debug=True) 