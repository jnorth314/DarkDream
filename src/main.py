import sys

from PyQt6.QtWidgets import QApplication

from compare import CompareWidget

def main() -> None:
    """Create the GUI"""

    app = QApplication(sys.argv)

    window = CompareWidget()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
