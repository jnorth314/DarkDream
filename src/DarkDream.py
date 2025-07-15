import os
import sys

import cv2
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QFrame, QGridLayout, QLabel, QMainWindow, QPushButton, QWidget

from dungeon import (
    convert_string_to_dungeon, Dungeon, DungeonTile, get_matching_dungeons, get_tile_image, USED_DUNGEON_TILES
)

ICON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../res/icon.ico")

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

        for y in range(15):
            for x in range(15):
                layout.addWidget(TileButton(self), y, x)

        self.setLayout(layout)

        label = QLabel(self)
        label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        label.setFixedSize(16*15, 16*15)

    def get_currently_checked_button(self) -> TileButton | None:
        """Go through the grid and return the currently checked button"""

        layout: QGridLayout = self.layout()

        for y in range(15):
            for x in range(15):
                button: TileButton = layout.itemAtPosition(y, x).widget()

                if button.isChecked():
                    return button

        return None

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

        for i, tile in enumerate(USED_DUNGEON_TILES[1:]):
            button = TileButton(self)
            button.tile = tile

            layout.addWidget(button, i//7, i%7) # Largest prime factor is a good choice here to form a rectangle

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

        label.setFrameShape(QFrame.Shape.HLine)

    def set_matches(self, matches: int) -> None:
        """Update the label according to the number of matches"""

        layout: QGridLayout = self.layout()
        label: QLabel = layout.itemAtPosition(0, 1).widget()
        label.setText(str(matches))

class DungeonCreatorWidget(QWidget):
    """Widget containing all of the elements to craft dungeons"""

    def __init__(self, parent: QWidget | None=None) -> None:
        super().__init__(parent=parent)

        layout = QGridLayout(self)
        layout.addWidget(DungeonFrame(self), 0, 0, 1, 2)
        layout.addWidget(TileSelectorFrame(self), 1, 0, 2, 1)
        layout.addWidget(MatchesFrame(self), 1, 1, 1, 1)
        layout.addWidget(QPushButton("Reset", self), 2, 1, 1, 1)
        self.setLayout(layout)

        tiles: QGridLayout = self.findChild(DungeonFrame).layout()

        for y in range(tiles.rowCount()):
            for x in range(tiles.columnCount()):
                button: TileButton = tiles.itemAtPosition(y, x).widget()
                button.clicked.connect(self.on_tile_select)

        selector: QGridLayout = self.findChild(TileSelectorFrame).layout()

        for y in range(selector.rowCount()):
            for x in range(selector.columnCount()):
                button: TileButton = selector.itemAtPosition(y, x).widget()
                button.clicked.connect(self.on_image_select)

        self.findChild(QPushButton).clicked.connect(self.on_reset)

    def on_tile_select(self) -> None:
        """Callback for when a tile is clicked in the DungeonFrame"""

        layout: QGridLayout = self.findChild(DungeonFrame).layout()
        sender: TileButton = self.sender()

        if not sender.isChecked() and sender.tile != DungeonTile(0xFFFFFFFF, 0): # A double clicked tile should be reset
            sender.tile = DungeonTile(0xFFFFFFFF, 0)
            self.check_dungeon()

        for y in range(15):
            for x in range(15):
                button: TileButton = layout.itemAtPosition(y, x).widget()
                button.setChecked(False)

        sender.setChecked(True)

    def on_image_select(self) -> None:
        """Callback for when a tile is clicked in the TileSelectorFrame"""

        sender: TileButton = self.sender()
        button = self.findChild(DungeonFrame).get_currently_checked_button()

        if button is not None and button.tile != sender.tile:
            button.tile = sender.tile
            self.check_dungeon()

    def on_reset(self) -> None:
        """Callback for when the reset button is clicked"""

        layout: QGridLayout = self.findChild(DungeonFrame).layout()

        for y in range(15):
            for x in range(15):
                button: TileButton = layout.itemAtPosition(y, x).widget()
                button.tile = DungeonTile(0xFFFFFFFF, 0)

        self.findChild(MatchesFrame).set_matches(21475)

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

class DarkDream(QMainWindow):
    """Application for predicting dungeons in Dark Cloud"""

    def __init__(self) -> None:
        super().__init__()

        self.setWindowTitle("DarkDream")
        self.setWindowIcon(QIcon(ICON_PATH))

        self.setCentralWidget(DungeonCreatorWidget(self))
        self.setFixedSize(self.minimumSize())

def main():
    """Create and run the GUI for DarkDream"""

    app = QApplication(sys.argv)

    window = DarkDream()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
