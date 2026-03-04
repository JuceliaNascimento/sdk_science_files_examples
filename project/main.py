import ctypes
import sys
from PySide6.QtWidgets import QApplication
from ui import MainWindow
from utils import MODERN_DARK_THEME


myappid = 'thermalviewer.v0' 
try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception as e:
    print(f"Erro ao configurar ID do Windows: {e}")

    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(MODERN_DARK_THEME)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())