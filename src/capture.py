import cv2

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QSpinBox, QFrame, QGridLayout, QLabel, QHBoxLayout, QWidget

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

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        frame[...,3] = 127

        height, width, channels = frame.shape

        image = QImage(frame.tobytes(), width, height, width*channels, QImage.Format.Format_RGBA8888)
        pixmap = QPixmap(image)
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
