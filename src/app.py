import os
import sys
import typing

from pygrabber.dshow_graph import FilterGraph
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QAction, QActionGroup, QIcon
from PyQt6.QtWidgets import QGridLayout, QMainWindow, QMenu, QMenuBar, QWidget

from capture import CaptureWidget
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

        menu = QMenuBar()

        file = menu.addMenu("File")
        captures: QMenu = file.addMenu("Select Capture") # type: ignore

        self.group = QActionGroup(captures)
        self.group.setExclusive(True)

        for device in FilterGraph().get_input_devices(): # type: ignore
            action = QAction(device)
            action.setCheckable(True)
            action.triggered.connect(self.on_select_capture)
            captures.addAction(action)
            self.group.addAction(action)

        view: QMenu = menu.addMenu("View") # type: ignore

        self.toggle_action = QAction("Capture Overlay")
        self.toggle_action.setCheckable(True)
        self.toggle_action.triggered.connect(self.on_toggle_capture)
        view.addAction(self.toggle_action)

        self.settings_action = QAction("Settings")
        self.settings_action.setCheckable(True)
        self.settings_action.triggered.connect(self.on_view_settings)
        view.addAction(self.settings_action)

        self.setMenuBar(menu)

        compare = CompareWidget()
        self.capture = CaptureWidget(compare.dungeon)

        widget = QWidget()

        layout = QGridLayout()
        layout.addWidget(compare, 0, 0)
        layout.addWidget(self.capture, 0, 1)

        widget.setLayout(layout)

        self.setCentralWidget(widget)

    @typing.no_type_check
    def on_select_capture(self) -> None:
        """Callback for when the select capture button in the menu is pressed"""

        action: QAction = self.sender()

        for i, device in enumerate(FilterGraph().get_input_devices()):
            if device == action.text():
                filter_graph = FilterGraph()
                filter_graph.add_video_input_device(i)
                width, height = filter_graph.get_input_device().get_current_format()
                self.capture.set_video_capture(i, width, height)
                break

    def on_toggle_capture(self) -> None:
        """Callback for when the capture is toggled for display"""

        if self.toggle_action.isChecked():
            self.capture.label.show()
        else:
            self.capture.label.hide()

    def on_view_settings(self) -> None:
        """Callback for when the settings view is toggled"""

        if self.settings_action.isChecked():
            self.capture.show()
        else:
            self.capture.hide()
            QTimer.singleShot(0, lambda : self.adjustSize())
