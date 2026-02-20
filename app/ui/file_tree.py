import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeView, QMenu, QFileDialog)
from PyQt6.QtCore import QDir, pyqtSignal, Qt, QUrl
from PyQt6.QtGui import QFileSystemModel, QAction, QDesktopServices

class FileTreeWidget(QWidget):
    file_double_clicked = pyqtSignal(str) 
    new_note_requested = pyqtSignal()
    rename_requested = pyqtSignal(str) 
    delete_requested = pyqtSignal(str)
    export_requested = pyqtSignal(str)
    open_local_requested = pyqtSignal(str)
    import_requested = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setObjectName("sidebar")
        self.sort_ascending = True 
        self.setAcceptDrops(True)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        top_bar = QWidget()
        top_bar.setObjectName("sidebarTopBar")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(0, 0, 0, 0)

        self.btn_add = QPushButton("➕")
        self.btn_add.clicked.connect(self.new_note_requested.emit)
        self.btn_upload = QPushButton("📥")
        self.btn_upload.clicked.connect(self.request_upload)
        self.btn_sort = QPushButton("⬇️")
        self.btn_sort.clicked.connect(self.toggle_sort)

        top_layout.addWidget(self.btn_add)
        top_layout.addWidget(self.btn_upload)
        top_layout.addWidget(self.btn_sort)
        top_layout.addStretch()

        self.tree_view = QTreeView()
        self.file_model = QFileSystemModel()
        self.file_model.setFilter(QDir.Filter.NoDotAndDotDot | QDir.Filter.AllEntries)
        self.tree_view.setModel(self.file_model)
        self.tree_view.setHeaderHidden(True) 
        self.tree_view.setSortingEnabled(True)
        self.tree_view.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        for i in range(1, 4): self.tree_view.setColumnHidden(i, True)

        self.tree_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(top_bar)
        layout.addWidget(self.tree_view)
        self.tree_view.doubleClicked.connect(self.on_double_click)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.acceptProposedAction()
        else: event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        paths = [url.toLocalFile() for url in urls if url.isLocalFile()]
        if paths: self.import_requested.emit(paths) 
        event.acceptProposedAction()

    def request_upload(self):
        file_paths, _ = QFileDialog.getOpenFileNames(self, "选择文件", "", "所有文件 (*.*)")
        if file_paths: self.import_requested.emit(file_paths)

    def load_vault(self, folder_path):
        self.file_model.setRootPath(folder_path)
        self.tree_view.setRootIndex(self.file_model.index(folder_path))

    def on_double_click(self, index):
        file_path = self.file_model.filePath(index)
        if os.path.isfile(file_path):
            if file_path.endswith('.md') or file_path.endswith('.txt'): self.file_double_clicked.emit(file_path)
            else: QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    def show_context_menu(self, pos):
        index = self.tree_view.indexAt(pos)
        if not index.isValid(): return
        file_path = self.file_model.filePath(index)
        menu = QMenu(self)
        a_open = QAction("🖥️ 本地打开", self)
        a_rename = QAction("📝 重命名", self)
        a_export = QAction("📤 导出...", self)
        a_delete = QAction("🗑️ 删除", self)

        a_open.triggered.connect(lambda: self.open_local_requested.emit(file_path))
        a_rename.triggered.connect(lambda: self.rename_requested.emit(file_path))
        a_export.triggered.connect(lambda: self.export_requested.emit(file_path))
        a_delete.triggered.connect(lambda: self.delete_requested.emit(file_path))

        menu.addAction(a_open)
        menu.addAction(a_rename)
        menu.addAction(a_export)
        menu.addSeparator() 
        menu.addAction(a_delete)
        menu.exec(self.tree_view.viewport().mapToGlobal(pos))

    def toggle_sort(self):
        self.sort_ascending = not self.sort_ascending
        order = Qt.SortOrder.AscendingOrder if self.sort_ascending else Qt.SortOrder.DescendingOrder
        self.tree_view.sortByColumn(0, order)
        self.btn_sort.setText("⬇️" if self.sort_ascending else "⬆️")
