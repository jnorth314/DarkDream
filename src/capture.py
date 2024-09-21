from functools import cache

import cv2
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QSpinBox, QFrame, QGridLayout, QLabel, QHBoxLayout, QWidget

from compare import CompareWidget, DungeonFrame, get_tiles

@cache
def get_hashes_of_tiles() -> list[cv2.typing.MatLike]:
    """Return precomputed hashes for all of the tiles of the tileset"""

    return [cv2.img_hash.pHash(cv2.resize(tile, (32, 32), interpolation=cv2.INTER_AREA)) for tile in get_tiles()]

def get_best_fit_tile(image: cv2.typing.MatLike) -> int:
    """Calculate the best fit tile"""

    image_hash = cv2.img_hash.pHash(cv2.resize(image, (32, 32), interpolation=cv2.INTER_AREA))

    module = cv2.img_hash.PHash.create()

    # Calculate the similarity for each tile (Except the 2 identical pillar tiles + blanks)
    similarities = [1.0 - module.compare(image_hash, phash)/64.0
                    for phash in get_hashes_of_tiles()[:40]]

    return -1 if max(similarities) < 0.9 else similarities.index(max(similarities))

def get_dungeon_from_image(image: cv2.typing.MatLike) -> list[list[int]]:
    """Calculate the dungeon based on the provided image"""

    return [[get_best_fit_tile(image[y:y + 16, x:x + 16]) for x in range(0, 16*15, 16)] for y in range(0, 16*15, 16)]

def crop_to_dungeon(image: cv2.typing.MatLike, x: int, y: int, dx: int, dy: int) -> cv2.typing.MatLike:
    """Crop the image to just the dungeon portion of the image"""

    return cv2.resize(image[y:y + dy, x: x + dx], (16*15, 16*15))

class SettingsFrame(QFrame):
    """Frame to hold the settings for capture"""

    def __init__(self) -> None:
        super().__init__()

        layout = QGridLayout()

        label = QLabel()
        label.setText("X")
        layout.addWidget(label, 0, 0)
        self.x_ = QSpinBox()
        self.x_.setRange(0, 0)
        layout.addWidget(self.x_, 1, 0)

        label = QLabel()
        label.setText("Y")
        layout.addWidget(label, 0, 1)
        self.y_ = QSpinBox()
        self.y_.setRange(0, 0)
        layout.addWidget(self.y_, 1, 1)

        label = QLabel()
        label.setText("Width")
        layout.addWidget(label, 2, 0)
        self.width_ = QSpinBox()
        self.width_.setRange(0, 0)
        layout.addWidget(self.width_, 3, 0)

        label = QLabel()
        label.setText("Height")
        layout.addWidget(label, 2, 1)
        self.height_ = QSpinBox()
        self.height_.setRange(0, 0)
        layout.addWidget(self.height_, 3, 1)

        layout.setSpacing(0)
        self.setLayout(layout)
        self.setFixedSize(16*8, 16*6)

class CaptureWidget(QWidget):
    """Widget responsible for capturing Dark Cloud and converting to tile ids"""

    def __init__(self, parent: QWidget) -> None:
        super().__init__()

        self.capture: cv2.VideoCapture | None = None

        self.label = QLabel(parent)
        self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.label.hide()

        layout = QHBoxLayout()
        self.settings = SettingsFrame()
        layout.addWidget(self.settings)
        self.setLayout(layout)

        self.hide()

        timer = QTimer(self)
        timer.timeout.connect(self.update_image)
        timer.start(1000//30)

    def update_image(self) -> None:
        """Update the image at regular intervals"""

        if self.capture is None or not self.capture.isOpened():
            return

        ret, frame = self.capture.read()

        if not ret:
            return

        x = self.settings.x_.value()
        y = self.settings.y_.value()
        dx = self.settings.width_.value()
        dy = self.settings.height_.value()

        height, width, channels = frame.shape

        if (dx > 0 and x + dx <= width and dy > 0 and y + dy <= height):
            frame = crop_to_dungeon(frame, x, y, dx, dy)
        else:
            frame = crop_to_dungeon(frame, 0, 0, min(height, width), min(height, width))

        dungeon = get_dungeon_from_image(frame)
        has_made_change = False
        dungeon_frame: DungeonFrame = self.label.parent() # type: ignore

        for x in range(15):
            for y in range(15):
                if dungeon_frame.buttons[y][x].id == -1 and dungeon[y][x] not in (-1, 23):
                    dungeon_frame.buttons[y][x].id = dungeon[y][x]
                    dungeon_frame.buttons[y][x].set_icon()
                    has_made_change = True

        if has_made_change:
            compare_widget: CompareWidget = dungeon_frame.parent() # type: ignore
            compare_widget.check_matching_dungeon()

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        frame[...,3] = 127

        height, width, channels = frame.shape

        pixmap = QPixmap(QImage(frame.tobytes(), width, height, width*channels, QImage.Format.Format_RGBA8888))
        self.label.resize(pixmap.size())
        self.label.setPixmap(pixmap)

    def set_video_capture(self, index: int, width: int, height: int) -> None:
        """Create a video capture"""

        if self.capture is not None:
            self.capture.release()

        self.capture = cv2.VideoCapture(index)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        self.settings.x_.setRange(0, width)
        self.settings.y_.setRange(0, height)
        self.settings.width_.setRange(0, width)
        self.settings.height_.setRange(0, height)
