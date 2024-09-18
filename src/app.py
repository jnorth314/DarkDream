import os
import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMainWindow

from compare import CompareWidget

class DarkDream(QMainWindow): # pragma: no cover
    """Main window of the DarkDream application"""

    def __init__(self)-> None:
        super().__init__()

        self.setWindowTitle("DarkDream")

        path_to_icon = (
            os.path.join(sys._MEIPASS, "res/icon.ico") if getattr(sys, "frozen", False) else # type: ignore # pylint: disable=protected-access
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "../res/icon.ico")
        )
        self.setWindowIcon(QIcon(path_to_icon))

        compare = CompareWidget()
        self.setCentralWidget(compare)
