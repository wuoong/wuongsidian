import os
import sys
import tempfile
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import QProcess, QProcessEnvironment


class TerminalPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: Consolas;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        top_layout = QHBoxLayout()
        title = QLabel("💻 内嵌控制台 (Jupyter Sandbox)")
        title.setStyleSheet("font-weight: bold; color: #8b5cf6;")
        self.btn_clear = QPushButton("🗑️ 清空")
        self.btn_clear.setStyleSheet("background: transparent; border: none; color: #aaa;")
        self.btn_clear.clicked.connect(self.clear_output)

        top_layout.addWidget(title)
        top_layout.addStretch()
        top_layout.addWidget(self.btn_clear)

        self.output_display = QTextBrowser()
        self.output_display.setStyleSheet("border: none; background-color: #1e1e1e;")

        layout.addLayout(top_layout)
        layout.addWidget(self.output_display)

        self.process = QProcess(self)

        # 【修复乱码 1】：强制给子进程注入环境变量，要求 Python 必须用 UTF-8 输出
        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONIOENCODING", "utf-8")
        self.process.setProcessEnvironment(env)

        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)

    def run_code(self, code_str):
        self.output_display.append("<br><b style='color:#8b5cf6;'>[执行代码] ▶</b>")
        self.temp_file = os.path.join(tempfile.gettempdir(), "smart_obsidian_run.py")
        with open(self.temp_file, "w", encoding="utf-8") as f:
            f.write(code_str)

        if getattr(sys, 'frozen', False):
            python_cmd = "python"
        else:
            python_cmd = sys.executable

        self.process.start(python_cmd, [self.temp_file])

    # 【修复乱码 2】：加入双重解码保险机制
    def handle_stdout(self):
        raw_data = self.process.readAllStandardOutput().data()
        try:
            data = raw_data.decode('utf-8')
        except UnicodeDecodeError:
            data = raw_data.decode('gbk', errors='ignore')

        data = data.replace('\n', '<br>')
        self.output_display.append(f"<span style='color:#d4d4d4;'>{data}</span>")

    def handle_stderr(self):
        raw_data = self.process.readAllStandardError().data()
        try:
            data = raw_data.decode('utf-8')
        except UnicodeDecodeError:
            data = raw_data.decode('gbk', errors='ignore')

        data = data.replace('\n', '<br>')
        self.output_display.append(f"<span style='color:#f43f5e;'>{data}</span>")

    def clear_output(self):
        self.output_display.clear()