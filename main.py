import sys
from PyQt6.QtWidgets import QApplication
from gui_app import MainWindow
from version import VERSION

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.setWindowTitle(f"SRT Ticket Hunter v{VERSION}")
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main() 