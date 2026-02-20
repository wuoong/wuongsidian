import os
import re
import shutil
import urllib.parse
from PyQt6.QtWidgets import (QMainWindow, QSplitter, QWidget, QVBoxLayout,
                             QHBoxLayout, QTabWidget, QPushButton, QLabel,
                             QFileDialog, QStackedWidget, QInputDialog, QMessageBox,
                             QTextBrowser, QLineEdit, QApplication)
from PyQt6.QtCore import Qt, QUrl, QTimer
from PyQt6.QtGui import QShortcut, QKeySequence, QDesktopServices

from app.ui.file_tree import FileTreeWidget
from app.ui.editor import MarkdownEditor
from app.ui.graph_view import GraphView
from app.core.ai_agent import VaultRAGAgent
from app.core.web_server import LanServerThread
from app.ui.search_view import SearchView

from app.ui.terminal_panel import TerminalPanel
from app.ui.kanban_view import KanbanView
from app.utils.config import ConfigManager


class EmptyStateWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_create = QLabel("创建新文件 (Ctrl + N)")
        lbl_create.setStyleSheet("color: #8b5cf6; font-size: 16px;")
        layout.addWidget(lbl_create)


class ObsidianClone(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("梧桐知网")
        self.resize(1300, 800)
        self.vault_path = ""
        self.open_editors = {}

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- 1. 活动栏 (Activity Bar) ---
        activity_bar = QWidget()
        activity_bar.setObjectName("activityBar")
        activity_bar.setFixedWidth(50)
        activity_layout = QVBoxLayout(activity_bar)
        activity_layout.setContentsMargins(0, 10, 0, 10)

        btn_files = QPushButton("🗂️")
        btn_files.setToolTip("编辑器视图")
        btn_files.clicked.connect(self.show_file_explorer)

        btn_open_vault = QPushButton("📂")
        btn_open_vault.setToolTip("打开/切换知识库")
        btn_open_vault.clicked.connect(self.open_vault)

        btn_search = QPushButton("🔍")
        btn_search.setToolTip("全局搜索")
        btn_search.clicked.connect(self.global_search)

        btn_graph = QPushButton("🌌")
        btn_graph.setToolTip("关系图谱")
        btn_graph.clicked.connect(self.show_graph_view)

        btn_kanban = QPushButton("📋")
        btn_kanban.setToolTip("项目看板 (YAML)")
        btn_kanban.clicked.connect(self.show_kanban_view)

        btn_ai = QPushButton("🤖")
        btn_ai.setToolTip("智能助手 (RAG)")
        btn_ai.clicked.connect(self.toggle_ai_panel)

        self.btn_server = QPushButton("🌐")
        self.btn_server.setToolTip("局域网分享")
        self.btn_server.clicked.connect(self.toggle_server)

        # 【新增】激活设置按钮
        self.btn_settings = QPushButton("⚙️")
        self.btn_settings.setToolTip("设置 (API Key配置)")
        self.btn_settings.clicked.connect(self.show_settings)

        activity_layout.addWidget(btn_files)
        activity_layout.addWidget(btn_open_vault)
        activity_layout.addWidget(btn_search)
        activity_layout.addWidget(btn_graph)
        activity_layout.addWidget(btn_kanban)
        activity_layout.addWidget(btn_ai)
        activity_layout.addWidget(self.btn_server)
        activity_layout.addStretch()
        activity_layout.addWidget(self.btn_settings)  # <--- 换成了绑定事件的设置按钮

        # --- 2. 核心分割器布局 ---
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        self.file_tree = FileTreeWidget()
        self.file_tree.file_double_clicked.connect(self.open_markdown_file)
        self.file_tree.new_note_requested.connect(self.create_new_note)
        self.file_tree.rename_requested.connect(self.rename_file)
        self.file_tree.delete_requested.connect(self.delete_file)
        self.file_tree.export_requested.connect(self.export_file)
        self.file_tree.open_local_requested.connect(self.open_local)
        self.file_tree.import_requested.connect(self.import_files)

        self.main_stack = QStackedWidget()
        self.empty_state = EmptyStateWidget()
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)

        self.graph_view = GraphView()
        self.search_view = SearchView()
        self.search_view.result_selected.connect(self.open_markdown_file)

        self.kanban_view = KanbanView()
        self.kanban_view.note_clicked.connect(self.open_markdown_file)

        self.main_stack.addWidget(self.empty_state)
        self.main_stack.addWidget(self.tabs)
        self.main_stack.addWidget(self.graph_view)
        self.main_stack.addWidget(self.search_view)
        self.main_stack.addWidget(self.kanban_view)

        self.terminal = TerminalPanel()

        self.center_splitter = QSplitter(Qt.Orientation.Vertical)
        self.center_splitter.addWidget(self.main_stack)
        self.center_splitter.addWidget(self.terminal)
        self.center_splitter.setSizes([750, 150])

        self.ai_panel = QWidget()
        self.ai_panel.setStyleSheet("background-color: #fafafa; border-left: 1px solid #ededed;")
        ai_layout = QVBoxLayout(self.ai_panel)
        ai_layout.setContentsMargins(10, 15, 10, 10)

        ai_title = QLabel("🤖 梧桐 AI 引擎 (RAG)")
        ai_title.setStyleSheet("font-weight: bold; color: #8b5cf6; border: none;")
        self.ai_chat_display = QTextBrowser()
        self.ai_chat_display.setStyleSheet(
            "background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 6px; padding: 5px;")
        self.ai_input = QLineEdit()
        self.ai_input.setPlaceholderText("提问...")
        self.ai_input.setStyleSheet("padding: 8px; border: 1px solid #e0e0e0; border-radius: 4px;")
        self.ai_input.returnPressed.connect(self.ask_ai)

        ai_layout.addWidget(ai_title)
        ai_layout.addWidget(self.ai_chat_display)
        ai_layout.addWidget(self.ai_input)
        self.ai_panel.hide()

        self.main_splitter.addWidget(self.file_tree)
        self.main_splitter.addWidget(self.center_splitter)
        self.main_splitter.addWidget(self.ai_panel)
        self.main_splitter.setSizes([220, 800, 280])

        main_layout.addWidget(activity_bar)
        main_layout.addWidget(self.main_splitter)

        # --- 3. 快捷键与初始化 ---
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self.create_new_note)
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self.save_current_note)

        self.server_thread = None
        self.config_manager = ConfigManager()
        last_vault = self.config_manager.get_last_vault()

        if last_vault and os.path.exists(last_vault):
            self.vault_path = last_vault
            self.file_tree.load_vault(last_vault)
        else:
            QTimer.singleShot(200, self.prompt_initial_vault)

    def prompt_initial_vault(self):
        QMessageBox.information(self, "欢迎使用梧桐知网",
                                "这是您首次运行或知识库已失效。\n请在下一步中选择或创建一个空文件夹作为您的【本地知识库】。")
        self.open_vault()

    # ================= 功能方法 =================

    def show_settings(self):
        """【新增】弹出设置框，让用户填写 API Key"""
        current_key = self.config_manager.get_api_key()
        new_key, ok = QInputDialog.getText(
            self,
            "设置大模型 API Key",
            "请输入您的 SiliconFlow API Key (以 sk- 开头):\n(如果您还没有，可前往 cloud.siliconflow.cn 免费申请)",
            QLineEdit.EchoMode.Normal,
            current_key
        )
        if ok:
            # 去除两端空格后保存到 config.json
            self.config_manager.set_api_key(new_key.strip())
            self.statusBar().showMessage("✅ API Key 已保存到本地配置", 3000)

    def show_kanban_view(self):
        self.save_current_note()
        if self.vault_path:
            self.kanban_view.load_vault_tasks(self.vault_path)
            self.main_stack.setCurrentIndex(4)
        else:
            QMessageBox.warning(self, "提示", "请先打开一个知识库！")

    def open_markdown_file(self, file_path):
        self.main_stack.setCurrentIndex(1)
        if file_path in self.open_editors:
            self.open_editors[file_path].load_file()
            self.tabs.setCurrentIndex(self.tabs.indexOf(self.open_editors[file_path]))
            return

        editor = MarkdownEditor(file_path, self.vault_path)
        editor.link_clicked.connect(self.handle_internal_link)
        editor.run_code_requested.connect(self.terminal.run_code)

        idx = self.tabs.addTab(editor, os.path.basename(file_path))
        self.tabs.setCurrentIndex(idx)
        self.open_editors[file_path] = editor

    def save_current_note(self):
        current_widget = self.tabs.currentWidget()
        if isinstance(current_widget, MarkdownEditor):
            current_widget.save_file()
            self.statusBar().showMessage(f"✅ 已保存: {os.path.basename(current_widget.file_path)}", 2000)

    def close_tab(self, index):
        editor = self.tabs.widget(index)
        if isinstance(editor, MarkdownEditor) and editor.is_modified:
            reply = QMessageBox.question(
                self, '保存确认',
                f"文档 '{os.path.basename(editor.file_path)}' 已修改，是否保存后关闭？",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Save:
                editor.save_file()
            elif reply == QMessageBox.StandardButton.Cancel:
                return

        for path, ed in list(self.open_editors.items()):
            if ed == editor:
                del self.open_editors[path]
                break
        self.tabs.removeTab(index)
        if self.tabs.count() == 0:
            self.main_stack.setCurrentIndex(0)

    def open_vault(self):
        folder = QFileDialog.getExistingDirectory(self, "选择知识库目录")
        if folder:
            self.vault_path = folder
            self.file_tree.load_vault(folder)
            self.tabs.clear()
            self.open_editors.clear()
            self.main_stack.setCurrentIndex(0)
            self.config_manager.set_last_vault(folder)
            self.statusBar().showMessage(f"✅ 已切换/创建知识库: {folder}", 3000)

    def show_graph_view(self):
        if not self.vault_path: return
        nodes_set, edges, node_weights = set(), [], {}
        for root, _, files in os.walk(self.vault_path):
            for f in files:
                if f.endswith('.md'):
                    source_name = f[:-3]
                    nodes_set.add(source_name)
                    node_weights[source_name] = node_weights.get(source_name, 0) + 1
                    try:
                        content = open(os.path.join(root, f), 'r', encoding='utf-8', errors='ignore').read()
                        for link in re.findall(r'\[\[(.*?)\]\]', content):
                            edges.append({"source": source_name, "target": link})
                            nodes_set.add(link)
                            node_weights[link] = node_weights.get(link, 0) + 1
                    except Exception:
                        pass

        echarts_nodes = [{"name": n, "symbolSize": min(15 + (node_weights.get(n, 1) - 1) * 5, 60)} for n in nodes_set]
        self.graph_view.render_graph(echarts_nodes, edges)
        self.main_stack.setCurrentIndex(2)

    def show_file_explorer(self):
        self.main_stack.setCurrentIndex(1 if self.tabs.count() > 0 else 0)

    def import_files(self, file_paths):
        if not self.vault_path: return
        for path in file_paths:
            try:
                target_path = os.path.join(self.vault_path, os.path.basename(path))
                if os.path.isdir(path):
                    shutil.copytree(path, target_path)
                else:
                    shutil.copy2(path, target_path)
            except Exception:
                pass

    def delete_file(self, file_path):
        if QMessageBox.question(self, "确认删除",
                                f"彻底删除 '{os.path.basename(file_path)}' 吗？") == QMessageBox.StandardButton.Yes:
            if file_path in self.open_editors:
                idx = self.tabs.indexOf(self.open_editors[file_path])
                if idx != -1: self.tabs.removeTab(idx)
                del self.open_editors[file_path]
            try:
                if os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                else:
                    os.remove(file_path)
            except Exception:
                pass

    def export_file(self, file_path):
        save_path, _ = QFileDialog.getSaveFileName(self, "导出", os.path.basename(file_path))
        if save_path:
            try:
                if os.path.isdir(file_path):
                    shutil.copytree(file_path, save_path)
                else:
                    shutil.copy2(file_path, save_path)
            except Exception:
                pass

    def open_local(self, file_path):
        QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))

    def create_new_note(self, default_name=""):
        if not self.vault_path: return
        name, ok = QInputDialog.getText(self, "新建笔记", "请输入名称:", text=default_name)
        if ok and name:
            if not name.endswith('.md'): name += '.md'
            file_path = os.path.join(self.vault_path, name)
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f: f.write(f"# {name[:-3]}\n\n")
            self.open_markdown_file(file_path)

    def rename_file(self, file_path):
        old_name = os.path.basename(file_path)
        new_name, ok = QInputDialog.getText(self, "重命名", "新名称:", text=old_name)
        if ok and new_name and new_name != old_name:
            if file_path.endswith('.md') and not new_name.endswith('.md'): new_name += '.md'
            new_path = os.path.join(os.path.dirname(file_path), new_name)
            if file_path in self.open_editors:
                idx = self.tabs.indexOf(self.open_editors[file_path])
                if idx != -1: self.tabs.removeTab(idx)
                del self.open_editors[file_path]
            os.rename(file_path, new_path)

    def global_search(self):
        if not self.vault_path:
            QMessageBox.warning(self, "提示", "请先打开一个知识库！")
            return
        query, ok = QInputDialog.getText(self, "全局搜索", "请输入笔记内容关键字:")
        if not (ok and query): return

        self.search_view.clear_results()
        found_count = 0

        for root, _, files in os.walk(self.vault_path):
            for f in files:
                if f.endswith('.md'):
                    file_path = os.path.join(root, f)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                            content = file.read()
                        if query.lower() in content.lower():
                            idx = content.lower().find(query.lower())
                            start = max(0, idx - 20)
                            end = min(len(content), idx + len(query) + 20)
                            snippet = content[start:end].replace('\n', ' ')
                            self.search_view.add_result(file_path, snippet)
                            found_count += 1
                    except Exception:
                        continue

        if found_count > 0:
            self.main_stack.setCurrentIndex(3)
            self.statusBar().showMessage(f"✅ 找到 {found_count} 处匹配内容", 3000)
        else:
            QMessageBox.information(self, "搜索结果", f"未在知识库中找到包含 '{query}' 的内容。")

    def handle_internal_link(self, target_name):
        if not self.vault_path: return
        target_name = urllib.parse.unquote(target_name)
        if not target_name.endswith('.md'): target_name += '.md'

        for root, _, files in os.walk(self.vault_path):
            if target_name in files:
                self.open_markdown_file(os.path.join(root, target_name))
                return

        if QMessageBox.question(self, "创建新笔记",
                                f"'{target_name}' 不存在，是否创建？") == QMessageBox.StandardButton.Yes:
            self.create_new_note(target_name)

    def toggle_ai_panel(self):
        self.ai_panel.setVisible(not self.ai_panel.isVisible())

    def ask_ai(self):
        if not self.vault_path: return
        query = self.ai_input.text().strip()
        if not query: return
        self.ai_input.clear()
        self.ai_chat_display.append(f"<b>我:</b> {query}")
        QApplication.processEvents()

        # 【关键修改】：调用 AI 引擎时，把用户设置的 API Key 传进去
        user_api_key = self.config_manager.get_api_key()
        agent = VaultRAGAgent(self.vault_path, user_api_key)
        response = agent.ask(query).replace('\n', '<br>')

        self.ai_chat_display.append(f"<b style='color:#8b5cf6;'>梧桐:</b> {response}<hr>")

    def toggle_server(self):
        if not self.vault_path: return
        if self.server_thread is None or not self.server_thread.is_running:
            self.server_thread = LanServerThread(self.vault_path)
            self.server_thread.status_signal.connect(self.on_server_status)
            self.server_thread.start()
        else:
            self.server_thread.stop()
            self.btn_server.setStyleSheet("")

    def on_server_status(self, msg, running):
        if running:
            self.btn_server.setStyleSheet("color: #8b5cf6;")
            QMessageBox.information(self, "局域网分享", f"服务已启动：\n{msg}")
        else:
            QMessageBox.information(self, "局域网分享", msg)