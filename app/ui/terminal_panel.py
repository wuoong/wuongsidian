import os
import sys  # 引入 sys 模块获取绝对路径
import tempfile
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import QProcess

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
        self.process.readyReadStandardOutput.connect(self.handle_stdout)
        self.process.readyReadStandardError.connect(self.handle_stderr)

    def run_code(self, code_str):
        self.output_display.append("<br><b style='color:#8b5cf6;'>[执行代码] ▶</b>")

        self.temp_file = os.path.join(tempfile.gettempdir(), "smart_obsidian_run.py")
        with open(self.temp_file, "w", encoding="utf-8") as f:
            f.write(code_str)

        # 【核心修复 3】：绝对不要只写 "python"，使用 sys.executable 精准定位当前正在运行代码的虚拟环境 Python 解释器
        self.process.start(sys.executable, [self.temp_file])

    def handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='ignore')
        # 【核心修复 4】：将控制台的换行符替换为 HTML 的 <br>，防止输出全挤在一行
        data = data.replace('\n', '<br>')
        self.output_display.append(f"<span style='color:#d4d4d4;'>{data}</span>")

    def handle_stderr(self):
        data = self.process.readAllStandardError().data().decode('utf-8', errors='ignore')
        data = data.replace('\n', '<br>')
        self.output_display.append(f"<span style='color:#f43f5e;'>{data}</span>")

    def clear_output(self):
        self.output_display.clear()