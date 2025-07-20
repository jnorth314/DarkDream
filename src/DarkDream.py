from dataclasses import dataclass
import os
import sys
import time

import cv2
from pygrabber.dshow_graph import FilterGraph
from PyQt6.QtCore import pyqtSignal, QObject, Qt, QThread
from PyQt6.QtGui import QAction, QActionGroup, QCloseEvent, QIcon, QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QButtonGroup, QCheckBox, QDialog, QFrame, QGridLayout, QLabel, QMainWindow, QMenu, QMenuBar,
    QPushButton, QSpinBox, QWidget
)

from dungeon import (
    convert_string_to_dungeon, Dungeon, DungeonTile, get_dungeon_from_image, get_matching_dungeons, get_tile_image,
    USED_DUNGEON_TILES
)

ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../res/icon.ico")

@dataclass
class DeviceInfo:
    """Information regarding the Device in order to open the capture"""

    text: str
    idx: int
    resolution: tuple[int, int]

def get_all_capture_devices() -> list[DeviceInfo]:
    """Get all available capture devices"""

    #TODO: Find a solution that doesn't rely entirely on this library, preferably using cv2 exclusively

    def get_device_resolution(idx: int) -> tuple[int, int]:
        """Get resolution of the given index"""

        graph = FilterGraph()
        graph.add_video_input_device(idx)
        resolution = graph.get_input_device().get_current_format()
        graph.remove_filters()

        return resolution

    return [
        DeviceInfo(device, i, get_device_resolution(i)) for i, device in enumerate(FilterGraph().get_input_devices())
    ]

class VideoCapture(QThread):
    """Worker responsible for capturing the image"""

    captured = pyqtSignal(object)
    closed = pyqtSignal()

    def __init__(self, parent: QObject | None=None) -> None:
        super().__init__(parent=parent)

        self.video = cv2.VideoCapture()

    def run(self) -> None:
        """Thread where the capture image will be read"""

        while not self.isInterruptionRequested() and self.video.isOpened():
            is_success, img = self.video.read()

            if is_success:
                self.captured.emit(img)

            time.sleep(1/30)

        if self.video.isOpened():
            self.video.release()

        self.closed.emit()

    def open(self, idx: int, width: int, height: int) -> None:
        """Open the video with the corresponding parameters"""

        self.video.open(idx)
        self.video.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.video.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

class TileButton(QPushButton):
    """Button to hold tile information"""

    def __init__(self, parent: QWidget | None=None) -> None:
        super().__init__(parent=parent)

        self._tile = DungeonTile(0xFFFFFFFF, 0)
        self.setFixedSize(16, 16)
        self.setCheckable(True)

    @property
    def tile(self) -> DungeonTile:
        return self._tile

    @tile.setter
    def tile(self, tile: DungeonTile) -> None:
        self._tile = tile

        if self.tile != DungeonTile(0xFFFFFFFF, 0):
            self.setIcon(
                QIcon(QPixmap(QImage(get_tile_image(self.tile).tobytes(), 16, 16, 48, QImage.Format.Format_BGR888)))
            )
        else:
            self.setIcon(QIcon())

    def force(self) -> None:
        """Force the icon to be set for DungeonTile(0xFFFFFFFF, 0)"""

        self.setIcon(
            QIcon(QPixmap(QImage(get_tile_image(self.tile).tobytes(), 16, 16, 48, QImage.Format.Format_BGR888)))
        )

class DungeonFrame(QFrame):
    """Object to hold all of the TileButtons in a 15x15 grid"""

    def __init__(self, parent: QWidget | None=None) -> None:
        super().__init__(parent=parent)

        layout = QGridLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0 ,0)

        buttons = QButtonGroup(self)
        buttons.setExclusive(False)

        for y in range(15):
            for x in range(15):
                layout.addWidget(button := TileButton(self), y, x)
                buttons.addButton(button)

        self.setLayout(layout)

        label = QLabel(self)
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        label.setFixedSize(16*15, 16*15)
        label.hide()

    def get_dungeon(self) -> Dungeon:
        """Reassemble the tiles into a Dungeon and return the result"""

        layout: QGridLayout = self.layout()

        dungeon = [[DungeonTile(0xFFFFFFFF, 0) for _ in range(15)] for _ in range(15)]

        for y in range(15):
            for x in range(15):
                button: TileButton = layout.itemAtPosition(y, x).widget()

                dungeon[y][x] = button.tile

        return dungeon

    def set_overlay(self, img: cv2.typing.MatLike) -> None:
        """Apply a transparent image to overlay on top of the DungeonFrame"""

        img = cv2.resize(img, (16*15, 16*15))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGBA)
        img[..., 3] = 127

        height, width, channels = img.shape

        self.findChild(QLabel).setPixmap(
            QPixmap(QImage(img.tobytes(), width, height, width*channels, QImage.Format.Format_RGBA8888))
        )

class TileSelectorFrame(QFrame):
    """Object to hold all of the TileButtons for editing the DungeonFrame"""

    def __init__(self, parent: QWidget | None=None) -> None:
        super().__init__(parent=parent)

        layout = QGridLayout(self)
        layout.setSpacing(1)
        layout.setContentsMargins(0, 0, 0 ,0)

        buttons = QButtonGroup(self)

        for i, tile in enumerate(USED_DUNGEON_TILES[1:]):
            # Largest prime factor is a good choice here to form a rectangle
            layout.addWidget(button := TileButton(self), i//7, i%7)
            buttons.addButton(button)

            button.tile = tile

        self.setLayout(layout)
        self.setFixedSize(16*layout.columnCount() + 15, 16*layout.rowCount() + 15)

class MatchesFrame(QFrame):
    """Object to hold the label for the matching statistics"""

    def __init__(self, parent: QWidget | None=None) -> None:
        super().__init__(parent=parent)

        layout = QGridLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel("Matches:", self), 0, 0, 3, 1)
        layout.addWidget(QLabel("21475", self), 0, 1, Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(label := QFrame(self), 1, 1)
        layout.addWidget(QLabel("21475", self), 2, 1, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        self.setLayout(layout)

        label.setFrameShape(QFrame.Shape.HLine)

    def set_matches(self, matches: int) -> None:
        """Update the label according to the number of matches"""

        layout: QGridLayout = self.layout()
        label: QLabel = layout.itemAtPosition(0, 1).widget()
        label.setText(str(matches))

class SettingsDialog(QDialog):
    """Settings dialog for cropping and resizing the captured image"""

    def __init__(self, parent: QWidget | None=None) -> None:
        super().__init__(parent=parent)

        self.setWindowTitle("Settings")

        layout = QGridLayout(self)
        layout.addWidget(QLabel("X", self), 0, 0, 1, 2, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(QLabel("Y", self), 0, 2, 1, 2, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(x := QSpinBox(self), 1, 0, 1, 2)
        layout.addWidget(y := QSpinBox(self), 1, 2, 1, 2)
        layout.addWidget(QLabel("Width", self), 2, 0, 1, 2, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(QLabel("Height", self), 2, 2, 1, 2, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(w := QSpinBox(self), 3, 0, 1, 2)
        layout.addWidget(h := QSpinBox(self), 3, 2, 1, 2)
        layout.addWidget(QCheckBox(self), 4, 0, 1, 1)
        layout.addWidget(QLabel("Image Recognition?", self), 4, 1, 1, 3)
        self.setLayout(layout)

        x.setMaximum(10000)
        y.setMaximum(10000)
        w.setMinimum(1), w.setMaximum(10000)
        h.setMinimum(1), h.setMaximum(10000)

    @property
    def bounds(self) -> tuple[int, int, int, int]:
        """Parameters that make up the bounding box of an image"""

        layout: QGridLayout = self.layout()

        x: QSpinBox = layout.itemAtPosition(1, 0).widget()
        y: QSpinBox = layout.itemAtPosition(1, 2).widget()
        w: QSpinBox = layout.itemAtPosition(3, 0).widget()
        h: QSpinBox = layout.itemAtPosition(3, 2).widget()

        return (x.value(), y.value(), w.value(), h.value())

class DungeonCreatorWidget(QWidget):
    """Widget containing all of the elements to craft dungeons"""

    def __init__(self, parent: QWidget | None=None) -> None:
        super().__init__(parent=parent)

        SettingsDialog(self)

        layout = QGridLayout(self)
        layout.addWidget(tiles := DungeonFrame(self), 0, 0, 1, 2)
        layout.addWidget(images := TileSelectorFrame(self), 1, 0, 2, 1)
        layout.addWidget(MatchesFrame(self), 1, 1, 1, 1)
        layout.addWidget(button := QPushButton("Reset", self), 2, 1, 1, 1)
        self.setLayout(layout)

        tiles.findChild(QButtonGroup).buttonClicked.connect(self.on_tile_select)
        images.findChild(QButtonGroup).buttonClicked.connect(self.on_image_select)
        button.clicked.connect(self.on_reset)

    def on_tile_select(self, button: TileButton) -> None:
        """Callback for when a tile is clicked in the DungeonFrame"""

        if not button.isChecked() and button.tile != DungeonTile(0xFFFFFFFF, 0): # A double clicked tile should be reset
            button.tile = DungeonTile(0xFFFFFFFF, 0)
            self.check_dungeon()

        layout: QGridLayout = self.findChild(DungeonFrame).layout()

        for y in range(layout.rowCount()):
            for x in range(layout.columnCount()):
                tile: TileButton = layout.itemAtPosition(y, x).widget()
                tile.setChecked(False)

        button.setChecked(True)

    def on_image_select(self, button: TileButton) -> None:
        """Callback for when a tile is clicked in the TileSelectorFrame"""

        checked: TileButton | None = self.findChild(DungeonFrame).findChild(QButtonGroup).checkedButton()

        if checked is not None and checked.tile != button.tile:
            checked.tile = button.tile
            self.check_dungeon()

    def on_reset(self) -> None:
        """Callback for when the reset button is clicked"""

        layout: QGridLayout = self.findChild(DungeonFrame).layout()

        for y in range(15):
            for x in range(15):
                button: TileButton = layout.itemAtPosition(y, x).widget()
                button.tile = DungeonTile(0xFFFFFFFF, 0)

        self.findChild(MatchesFrame).set_matches(21475)

    def on_image(self, img: cv2.typing.MatLike) -> None:
        """Callback for when the image is captured"""

        x, y, w, h = self.findChild(SettingsDialog).bounds
        height, width, _ = img.shape

        if (width - x) >= w and (height - y) >= h:
            img = img[y:y + h, x:x + w]

        self.findChild(DungeonFrame).set_overlay(img)

        if self.findChild(SettingsDialog).findChild(QCheckBox).isChecked():
            dungeon = get_dungeon_from_image(img)
            layout: QGridLayout = self.findChild(DungeonFrame).layout()

            has_updated = False

            for y in range(15):
                for x in range(15):
                    button: TileButton = layout.itemAtPosition(y, x).widget()

                    if button.tile == DungeonTile(0xFFFFFFFF, 0) and button.tile != dungeon[y][x]:
                        button.tile = dungeon[y][x]
                        has_updated = True

            if has_updated:
                self.check_dungeon()

    def check_dungeon(self) -> None:
        """Check if the dungeon was a match, if so fill out the rest of the minimap"""

        dungeon = self.findChild(DungeonFrame).get_dungeon()
        matches = get_matching_dungeons(dungeon)

        self.findChild(MatchesFrame).set_matches(len(matches))

        if len(matches) == 1:
            dungeon = convert_string_to_dungeon(matches[0])

            layout: QGridLayout = self.findChild(DungeonFrame).layout()

            for y in range(15):
                for x in range(15):
                    button: TileButton = layout.itemAtPosition(y, x).widget()
                    button.tile = dungeon[y][x]

                    if button.tile == DungeonTile(0xFFFFFFFF, 0):
                        button.force()

class CaptureAction(QAction):
    """Action for selecting a capture"""

    def __init__(self, device: DeviceInfo, parent: QWidget | None=None) -> None:
        super().__init__(device.text, parent=parent)

        self.device = device

        self.setCheckable(True)

class SettingsAction(QAction):
    """Action for opening the settings"""

class MenuBar(QMenuBar):
    """MenuBar for the application"""

    def __init__(self, parent: QWidget | None=None) -> None:
        super().__init__(parent=parent)

        self.addMenu(file := QMenu("File", self))

        file.addMenu(captures := QMenu("Select Capture", file))
        file.addAction(SettingsAction("Settings", file))

        actions = QActionGroup(captures)
        actions.setExclusive(False)

        for device in get_all_capture_devices():
            captures.addAction(action := CaptureAction(device, captures))
            actions.addAction(action)

class DarkDream(QMainWindow):
    """Application for predicting dungeons in Dark Cloud"""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("DarkDream")
        self.setWindowIcon(QIcon(ICON_PATH))

        self.setMenuBar(menu := MenuBar(self))
        self.setCentralWidget(widget := DungeonCreatorWidget(self))
        self.setFixedSize(self.minimumSize())

        menu.findChild(QActionGroup).triggered.connect(self.on_capture_select)
        menu.findChild(SettingsAction).triggered.connect(self.on_settings)

        worker = VideoCapture(self)
        worker.captured.connect(widget.on_image)
        worker.closed.connect(self.on_capture_closed)

    def on_capture_select(self, action: CaptureAction) -> None:
        """Callback for when a capture is selected"""

        is_checked = action.isChecked()

        for capture in self.findChild(MenuBar).findChildren(CaptureAction):
            capture.setChecked(False)

        action.setChecked(is_checked)

        worker = self.findChild(VideoCapture)
        worker.requestInterruption()
        worker.wait()

        if is_checked:
            device = action.device
            worker.open(device.idx, device.resolution[0], device.resolution[1])
            worker.start()
            self.findChild(DungeonCreatorWidget).findChild(DungeonFrame).findChild(QLabel).show()

    def on_settings(self) -> None:
        """Callback when the settings in the menu bar is selected"""

        self.findChild(DungeonCreatorWidget).findChild(SettingsDialog).show()

    def on_capture_closed(self) -> None:
        """Callback when the capture is closed"""

        self.findChild(DungeonCreatorWidget).findChild(DungeonFrame).findChild(QLabel).hide()

        action: CaptureAction | None = self.findChild(MenuBar).findChild(QActionGroup).checkedAction()

        if action is not None:
            action.setChecked(False)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Gracefully close the GUI by terminating and waiting for any threads"""

        worker = self.findChild(VideoCapture)
        worker.requestInterruption()
        worker.wait()

        event.accept()

def main():
    """Create and run the GUI for DarkDream"""

    app = QApplication(sys.argv)

    window = DarkDream()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
