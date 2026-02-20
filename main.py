import sys
from PyQt6.QtWidgets import QApplication
from app.ui.main_window import ObsidianClone

def main():
    app = QApplication(sys.argv)
    with open("assets/styles.qss", "r", encoding="utf-8") as f:
        app.setStyleSheet(f.read())
    window = ObsidianClone()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
git --version