import os
import re
import markdown
import urllib.parse
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QTextEdit, QTextBrowser, QSplitter, QToolTip
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QEvent
from PyQt6.QtGui import QFont


class MarkdownEditor(QWidget):
    text_changed = pyqtSignal()
    link_clicked = pyqtSignal(str)
    run_code_requested = pyqtSignal(str)

    def __init__(self, file_path, vault_path=None):
        super().__init__()
        self.file_path = file_path
        self.vault_path = vault_path
        self.is_modified = False
        self.code_blocks = {}

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.editor = QTextEdit()
        self.editor.setFont(QFont("Consolas", 12))
        self.editor.setStyleSheet("border: none; padding: 20px; background: #ffffff;")
        self.editor.textChanged.connect(self.on_text_changed)

        self.preview = QTextBrowser()
        self.preview.setStyleSheet("border: none; border-left: 1px solid #eee; padding: 20px; background: #fafafa;")
        self.preview.setOpenLinks(False)
        self.preview.anchorClicked.connect(self.on_anchor_clicked)

        self.preview.viewport().installEventFilter(self)
        self.preview.setMouseTracking(True)
        self._last_hovered_link = None

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.editor)
        splitter.addWidget(self.preview)
        splitter.setSizes([500, 500])
        layout.addWidget(splitter)
        self.load_file()

    def eventFilter(self, obj, event):
        if obj == self.preview.viewport() and event.type() == QEvent.Type.MouseMove:
            anchor = self.preview.anchorAt(event.pos())
            if anchor.startswith("obsidian:"):
                clean_name = urllib.parse.unquote(anchor.split(":", 1)[1]).lstrip("/")
                if self._last_hovered_link != clean_name:
                    self._last_hovered_link = clean_name
                    if self.vault_path:
                        target_path = os.path.join(self.vault_path, clean_name + '.md')
                        if os.path.exists(target_path):
                            snippet = open(target_path, 'r', encoding='utf-8', errors='ignore').read(300)
                            QToolTip.showText(event.globalPosition().toPoint(), f"📄 {clean_name}\n\n{snippet}...",
                                              self.preview)
                        else:
                            QToolTip.hideText()
            else:
                self._last_hovered_link = None
                QToolTip.hideText()
        return super().eventFilter(obj, event)

    def on_anchor_clicked(self, url: QUrl):
        raw_url = url.toEncoded().data().decode('utf-8')

        # 捕捉代码运行请求
        if raw_url.startswith("runcode:"):
            block_id = raw_url.split(":", 1)[1]
            code = self.code_blocks.get(block_id, "")
            self.run_code_requested.emit(code)

        elif ":" in raw_url:
            clean_name = urllib.parse.unquote(raw_url.split(":", 1)[1].lstrip("/"))
            self.link_clicked.emit(clean_name)
        else:
            from PyQt6.QtGui import QDesktopServices
            QDesktopServices.openUrl(url)

    def load_file(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.editor.setPlainText(f.read())
                self.update_preview()
                self.is_modified = False
        except Exception:
            pass

    def save_file(self):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(self.editor.toPlainText())
            self.is_modified = False
            return True
        except Exception:
            return False

    def on_text_changed(self):
        self.is_modified = True
        self.update_preview()
        self.text_changed.emit()

    def update_preview(self):
        text = self.editor.toPlainText()
        self.code_blocks.clear()

        # 【核心修复 1】：提取代码，但不注入 HTML 按钮，而是注入“纯文本占位符”
        def code_replacer(match):
            code_content = match.group(1).strip()
            if not code_content:
                return match.group(0)  # 忽略空的代码块

            block_id = str(hash(code_content))
            self.code_blocks[block_id] = code_content

            # 使用一个绝对不会被 Markdown 破坏的文本占位符，包裹在换行符中
            return f"\n\nJUPYTER_BTN_{block_id}\n\n" + match.group(0) + "\n\n"

        # 更宽容的正则：兼容不写 python 的情况，只要是代码块就抓
        text = re.sub(r'```[ \t]*[a-zA-Z]*[\r\n]+(.*?)```', code_replacer, text, flags=re.DOTALL)

        # 此时 Markdown 引擎不会遇到复杂的 div 标签，能完美渲染代码高亮
        html = markdown.markdown(text, extensions=['extra', 'codehilite', 'sane_lists'])

        # 【核心修复 2】：在 Markdown 渲染成 HTML 之后，再把占位符替换成真实的运行按钮
        for block_id in self.code_blocks.keys():
            btn_html = f"<div style='text-align: right; margin-bottom: -15px; position: relative; z-index: 10;'><a href='runcode:{block_id}' style='background: #10b981; color: white; padding: 4px 10px; border-radius: 4px; text-decoration: none; font-size: 12px; font-weight: bold;'>▶ 运行代码</a></div>"
            # Markdown 可能会给独立一行的占位符加上 <p> 标签
            html = html.replace(f"<p>JUPYTER_BTN_{block_id}</p>", btn_html)
            html = html.replace(f"JUPYTER_BTN_{block_id}", btn_html)

        # 渲染双链逻辑
        def link_replacer(match):
            display_text = match.group(1)
            clean_filename = re.sub(r'<[^>]+>', '', display_text).strip().replace('*', '').replace('#', '')
            safe_href = urllib.parse.quote(clean_filename)
            return f'<a href="obsidian:{safe_href}" style="color: #8b5cf6; text-decoration: none; font-weight: bold;">{display_text}</a>'

        html = re.sub(r'\[\[(.*?)\]\]', link_replacer, html)
        self.preview.setHtml(html)