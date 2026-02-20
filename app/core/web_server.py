import os
import socket
import http.server
import socketserver
from PyQt6.QtCore import QThread, pyqtSignal

class LanServerThread(QThread):
    status_signal = pyqtSignal(str, bool)

    def __init__(self, directory, port=8000):
        super().__init__()
        self.directory = directory
        self.port = port
        self.httpd = None
        self.is_running = False

    def run(self):
        os.chdir(self.directory)
        handler = http.server.SimpleHTTPRequestHandler
        try:
            socketserver.TCPServer.allow_reuse_address = True
            self.httpd = socketserver.TCPServer(("", self.port), handler)
            self.is_running = True
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            self.status_signal.emit(f"http://{ip}:{self.port}", True)
            self.httpd.serve_forever() 
        except Exception as e:
            self.status_signal.emit(f"启动失败: {e}", False)
            self.is_running = False

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
        self.is_running = False
        self.status_signal.emit("局域网分享已停止", False)
