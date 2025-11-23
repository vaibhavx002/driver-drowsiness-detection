# gui/flash_overlay.py

from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import QTimer, Qt
class FlashOverlay(QWidget):
    """Flash a semi-transparent overlay color."""
    def __init__(self, parent=None, color=QColor(255, 60, 40, 160)):
        super().__init__(parent)
        self.color = color
        self._alpha = 0
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.hide()

    def start_flash(self, flashes=4, fade_ms=150):
        self._flashes = flashes
        self._current = 0
        self._fade_ms = fade_ms
        self.show()
        self.raise_()

        self._timer = QTimer(self)
        self._timer.setInterval(fade_ms)
        self._timer.timeout.connect(self._step)
        self._step()
        self._timer.start()

    def _step(self):
        if self._current >= self._flashes:
            self._timer.stop()
            self.hide()
            return

        # Alternate opacity
        self._alpha = 200 if (self._current % 2 == 0) else 0
        self._current += 1
        self.update()

    def paintEvent(self, event):
        if self.isHidden():
            return

        painter = QPainter(self)
        c = QColor(self.color)
        c.setAlpha(self._alpha)
        painter.fillRect(self.rect(), c)
        painter.end()

