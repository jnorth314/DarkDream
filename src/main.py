import sys

from PyQt6.QtWidgets import QApplication

from app import DarkDream

def main() -> None:
    """Create the GUI"""

    app = QApplication(sys.argv)

    window = DarkDream()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
