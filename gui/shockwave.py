# gui/shockwave.py
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen
from PySide6.QtCore import Qt, QPropertyAnimation, Property

class Shockwave(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._radius = 0
        self._opacity = 0
        self.hide()
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)

    def start_wave(self):
        self.show()
        self.raise_()

        self._radius = 0
        self._opacity = 150

        anim = QPropertyAnimation(self, b"radius")
        anim.setDuration(900)
        anim.setStartValue(10)
        anim.setEndValue(int(min(self.width(), self.height()) * 0.6))
        anim.finished.connect(self.hide)
        anim.start()

        self._anim = anim

    def getRadius(self):
        return self._radius

    def setRadius(self, v):
        self._radius = v
        self._opacity = max(0, 150 - (v * 1.1))
        self.update()

    radius = Property(int, getRadius, setRadius)

    def paintEvent(self, ev):
        if self._opacity <= 0:
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        color = QColor(255, 50, 30, int(self._opacity))
        pen = QPen(color)
        pen.setWidth(6)
        p.setPen(pen)
        p.setBrush(Qt.NoBrush)

        cx, cy = self.width() / 2, self.height() / 2
        p.drawEllipse(int(cx - self._radius), int(cy - self._radius), self._radius*2, self._radius*2)
        p.end()
