import os
import socket
import http.server
import socketserver
import logging
import tempfile
from PyQt6.QtCore import QThread, pyqtSignal

log_path = os.path.join(tempfile.gettempdir(), "wutong_server.log")
logging.basicConfig(filename=log_path, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


def get_real_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return socket.gethostbyname(socket.gethostname())


class UTF8RequestHandler(http.server.SimpleHTTPRequestHandler):
    def guess_type(self, path):
        mimetype = super().guess_type(path)
        if path.endswith('.md'):
            return 'text/plain; charset=utf-8'
        if mimetype and mimetype.startswith('text/'):
            return mimetype + '; charset=utf-8'
        return mimetype

    def log_message(self, format, *args):
        logging.info(f"[访客 IP: {self.client_address[0]}] 请求: {format % args}")


class LanServerThread(QThread):
    status_signal = pyqtSignal(str, bool)

    def __init__(self, directory, port=8888):
        super().__init__()
        self.directory = directory
        self.port = port
        self.httpd = None
        self.is_running = False

    def run(self):
        os.chdir(self.directory)
        try:
            # 【核心并发升级】：使用 ThreadingHTTPServer 替换 TCPServer
            # 现在它可以为每一个连进来的设备（手机、电脑、平板）开启一个独立的线程！
            http.server.ThreadingHTTPServer.allow_reuse_address = True
            self.httpd = http.server.ThreadingHTTPServer(("0.0.0.0", self.port), UTF8RequestHandler)
            self.is_running = True

            ip = get_real_ip()
            logging.info(f"=== 局域网服务已启动: http://{ip}:{self.port} ===")
            self.status_signal.emit(f"http://{ip}:{self.port}\n\n(运行日志:\n{log_path})", True)

            self.httpd.serve_forever()
        except Exception as e:
            logging.error(f"启动失败: {e}")
            self.status_signal.emit(f"启动失败: {e}", False)
            self.is_running = False

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
        self.is_running = False
        logging.info("=== 局域网服务已关闭 ===")
        self.status_signal.emit("局域网分享已停止", False)