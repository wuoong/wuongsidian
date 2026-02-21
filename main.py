import sys
import os
from PyQt6.QtWidgets import QApplication
from app.ui.main_window import ObsidianClone


def resource_path(relative_path):
    """ 获取程序运行时的绝对路径 (兼容开发环境和打包后的临时环境) """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def main():
    app = QApplication(sys.argv)

    # 使用 resource_path 精准定位样式表
    style_path = resource_path("assets/styles.qss")
    if os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    window = ObsidianClone()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()