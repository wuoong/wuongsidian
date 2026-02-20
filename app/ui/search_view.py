import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLabel
from PyQt6.QtCore import pyqtSignal, Qt


class SearchResultItem(QListWidgetItem):
    """自定义搜索项，存储文件路径"""

    def __init__(self, file_path, display_text):
        super().__init__(display_text)
        self.file_path = file_path


class SearchView(QWidget):
    # 当用户双击搜索结果时发出信号，传递文件路径
    result_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        self.title_label = QLabel("搜索结果")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #8b5cf6; margin-bottom: 5px;")

        self.results_list = QListWidget()
        self.results_list.setStyleSheet("""
            QListWidget { border: 1px solid #eee; border-radius: 6px; background: white; }
            QListWidget::item { padding: 10px; border-bottom: 1px solid #fafafa; }
            QListWidget::item:hover { background-color: #f4f4f4; }
        """)
        self.results_list.itemDoubleClicked.connect(self.on_item_double_clicked)

        layout.addWidget(self.title_label)
        layout.addWidget(self.results_list)

    def clear_results(self):
        self.results_list.clear()

    def add_result(self, file_path, snippet):
        filename = os.path.basename(file_path)
        # 组装显示文本：文件名 + 上下文片段
        display_text = f"📄 {filename}\n   ...{snippet}..."
        item = SearchResultItem(file_path, display_text)
        self.results_list.addItem(item)

    def on_item_double_clicked(self, item):
        if isinstance(item, SearchResultItem):
            self.result_selected.emit(item.file_path)