import cv2

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QLabel, QWidget

def crop_to_dungeon(image: cv2.typing.MatLike, x: int, y: int, dx: int, dy: int) -> cv2.typing.MatLike:
    """Crop the image to just the dungeon portion of the image"""

    image = cv2.cvtColor(cv2.resize(image[y:y + dy, x: x + dx], (16*15, 16*15)), cv2.COLOR_BGR2RGBA)
    image[...,3] = 127

    return image

class CaptureWidget(QWidget):
    """Widget responsible for capturing Dark Cloud and converting to tile ids"""

    def __init__(self, parent: QWidget) -> None:
        super().__init__()

        self.capture: cv2.VideoCapture | None = None

        self.label = QLabel(parent)
        self.label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.label.hide()

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

        frame = crop_to_dungeon(frame, 1108, 155, 39*15, 39*15) #TODO: Pull from User's Settings

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
