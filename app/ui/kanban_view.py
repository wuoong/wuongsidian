import os
import re
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QListWidget,
                             QLabel, QListWidgetItem, QAbstractItemView)
from PyQt6.QtCore import pyqtSignal, Qt


class KanbanListWidget(QListWidget):
    """自定义支持拖拽的列表组件"""
    item_moved = pyqtSignal(str, str)  # 传递：文件路径, 新的状态

    def __init__(self, status_val):
        super().__init__()
        self.status_val = status_val
        # 开启拖拽权限
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)

        self.setStyleSheet("""
            QListWidget { background-color: #f4f4f5; border: 1px solid #e4e4e7; border-radius: 8px; padding: 5px; min-height: 400px; }
            QListWidget::item { background-color: white; border-radius: 6px; padding: 15px; margin-bottom: 5px; border: 1px solid #ddd; }
            QListWidget::item:hover { border: 1px solid #8b5cf6; }
        """)

    def dropEvent(self, event):
        source_widget = event.source()

        # 确保是从别的列表拖过来的卡片
        if source_widget and isinstance(source_widget, KanbanListWidget) and source_widget != self:
            items = source_widget.selectedItems()
            if items:
                # 拿到绑定在卡片上的隐藏文件路径
                file_path = items[0].data(100)

                # 让 Qt 完成界面上的卡片移动动画
                super().dropEvent(event)

                # 发送精准的信号，告诉总管去修改 .md 文件里的 status
                self.item_moved.emit(file_path, self.status_val)
                return

        # 如果是在同一个列表里上下拖动排序，只执行 UI 移动即可
        super().dropEvent(event)


class KanbanView(QWidget):
    note_clicked = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.vault_path = ""
        layout = QHBoxLayout(self)

        # 实例化三个可拖拽的独立看板列
        self.list_todo = KanbanListWidget("todo")
        self.list_doing = KanbanListWidget("doing")
        self.list_done = KanbanListWidget("done")

        # 绑定双击打开笔记的事件
        self.list_todo.itemDoubleClicked.connect(self.on_item_clicked)
        self.list_doing.itemDoubleClicked.connect(self.on_item_clicked)
        self.list_done.itemDoubleClicked.connect(self.on_item_clicked)

        # 绑定拖拽后的底层文件修改事件
        self.list_todo.item_moved.connect(self.update_note_status)
        self.list_doing.item_moved.connect(self.update_note_status)
        self.list_done.item_moved.connect(self.update_note_status)

        layout.addLayout(self.create_column("📋 To Do (待办)", self.list_todo))
        layout.addLayout(self.create_column("⏳ Doing (进行中)", self.list_doing))
        layout.addLayout(self.create_column("✅ Done (已完成)", self.list_done))

    def create_column(self, title, list_widget):
        col_layout = QVBoxLayout()
        lbl = QLabel(title)
        lbl.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px; color: #555;")
        col_layout.addWidget(lbl)
        col_layout.addWidget(list_widget)
        return col_layout

    def load_vault_tasks(self, vault_path):
        """扫描本地库中的 YAML 元数据生成卡片"""
        self.vault_path = vault_path
        if not vault_path: return

        self.list_todo.clear()
        self.list_doing.clear()
        self.list_done.clear()

        for root, _, files in os.walk(vault_path):
            for f in files:
                if f.endswith('.md'):
                    path = os.path.join(root, f)
                    try:
                        content = open(path, 'r', encoding='utf-8', errors='ignore').read()

                        # 【核心修复 2】：去掉 ^ 的强限制，允许 YAML 块上方有 # 标题或空行
                        yaml_match = re.search(r'(?:^|\n)---[\r\n]+(.*?)[\r\n]+---', content, re.DOTALL)

                        if yaml_match:
                            yaml_text = yaml_match.group(1).lower()
                            item = QListWidgetItem(f"📄 {f.replace('.md', '')}")
                            item.setData(100, path)  # 绑定隐藏文件路径

                            if 'status: todo' in yaml_text or 'status:todo' in yaml_text:
                                self.list_todo.addItem(item)
                            elif 'status: doing' in yaml_text or 'status:doing' in yaml_text:
                                self.list_doing.addItem(item)
                            elif 'status: done' in yaml_text or 'status:done' in yaml_text:
                                self.list_done.addItem(item)
                    except Exception:
                        pass

    def on_item_clicked(self, item):
        file_path = item.data(100)
        self.note_clicked.emit(file_path)

    def update_note_status(self, file_path, new_status):
        """核心：当卡片被拖入新列时，用正则直接重写源文件的 YAML"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 使用正则把文件开头的 status 替换成拖拽后所在的列的状态
            new_content = re.sub(r'(status:\s*)\w+', rf'\g<1>{new_status}', content, count=1, flags=re.IGNORECASE)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        except Exception as e:
            print(f"看板文件状态同步失败: {e}")