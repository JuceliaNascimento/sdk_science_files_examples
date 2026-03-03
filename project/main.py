import sys
from PySide6.QtWidgets import QApplication
from ui import MainWindow
from utils import MODERN_DARK_THEME

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(MODERN_DARK_THEME)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())