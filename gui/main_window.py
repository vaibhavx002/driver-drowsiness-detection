# gui/main_window.py
import os
import cv2
import time
import logging

from PySide6.QtCore import (
    Qt, QTimer, QUrl, QEvent, QPoint, QPointF
)
from PySide6.QtGui import (
    QPixmap, QImage, QFont, QPainter, QColor, QPen
)
from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QSlider, QGroupBox, QGridLayout, QComboBox,
    QPushButton, QFrame, QStackedLayout
)
from PySide6.QtMultimedia import QSoundEffect

from core.camera_processor import CameraProcessor
from .glass_card import GlassCard


log = logging.getLogger(__name__)

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
ALERT_WAV = os.path.join(ASSETS_DIR, "alert.wav")
NOFACE_WAV = os.path.join(ASSETS_DIR, "noface.wav")


# =====================================================================
# FLASH OVERLAY
# =====================================================================
class FlashOverlay(QWidget):
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

        # alternate bright / off
        self._alpha = 200 if (self._current % 2 == 0) else 0
        self._current += 1
        self.update()

    def paintEvent(self, event):
        if self.isHidden():
            return

        p = QPainter(self)
        c = QColor(self.color)
        c.setAlpha(self._alpha)
        p.fillRect(self.rect(), c)
        p.end()


# =====================================================================
# RING SHOCKWAVE
# =====================================================================
class OverlayRing(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._active = False
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.hide()

    def start(self, center, max_radius=300, duration_ms=700):
        self._center = center
        self._start = time.time()
        self._duration = duration_ms / 1000
        self._max_radius = max_radius

        self._active = True
        self.show()
        self.raise_()

    def paintEvent(self, event):
        if not self._active:
            return

        elapsed = time.time() - self._start
        t = elapsed / self._duration

        if t >= 1:
            self._active = False
            self.hide()
            return

        ease = 1 - (1 - t) ** 2
        radius = self._max_radius * ease
        alpha = int(255 * (1 - ease))

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        pen = QPen(QColor(255, 90, 40, alpha))
        pen.setWidth(6)
        p.setPen(pen)

        p.drawEllipse(QPointF(self._center.x(), self._center.y()), radius, radius)
        p.end()

        self.update()


# =====================================================================
# MAIN WINDOW
# =====================================================================
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("DrowsyGuard")
        self.resize(1100, 720)

        main = QHBoxLayout(self)

        # ==============================================================
        # LEFT SIDE — FIXED VIDEO AREA (NO BLUR)
        # ==============================================================
        self.left_card = GlassCard()
        left_layout = QVBoxLayout(self.left_card)
        left_layout.setContentsMargins(15, 15, 15, 15)

        # 720×480 FIXED CONTAINER
        self.video_container = QFrame()
        self.video_container.setFixedSize(720, 480)

        # Create a stacking layout for video + flash + ring
        self.video_stack = QStackedLayout(self.video_container)
        self.video_stack.setStackingMode(QStackedLayout.StackAll)

        # Video output
        self.video_label = QLabel()
        self.video_label.setFixedSize(720, 480)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background:#000; border-radius:10px;")

        # Flash overlay
        self.flash_overlay = FlashOverlay(self.video_container)
        self.flash_overlay.setFixedSize(720, 480)

        # Shockwave ring
        self.ring = OverlayRing(self.video_container)
        self.ring.setFixedSize(720, 480)

        # Add to stack
        self.video_stack.addWidget(self.video_label)
        self.video_stack.addWidget(self.flash_overlay)
        self.video_stack.addWidget(self.ring)

        left_layout.addWidget(self.video_container, alignment=Qt.AlignCenter)

        # Status text
        self.overlay_label = QLabel("Not Monitoring")
        self.overlay_label.setAlignment(Qt.AlignCenter)
        self.overlay_label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        left_layout.addWidget(self.overlay_label)

        main.addWidget(self.left_card, stretch=3)

        # ==============================================================
        # RIGHT PANEL
        # ==============================================================
        right_card = GlassCard()
        rc = QVBoxLayout(right_card)

        theme = QGroupBox("Theme")
        lay = QHBoxLayout()
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Auto", "Dark", "Light"])
        lay.addWidget(self.theme_combo)
        theme.setLayout(lay)
        rc.addWidget(theme)

        adj = QGroupBox("Image Adjustments")
        grid = QGridLayout()

        grid.addWidget(QLabel("Brightness"), 0, 0)
        self.brightness = QSlider(Qt.Horizontal)
        self.brightness.setRange(-100, 100)
        grid.addWidget(self.brightness, 0, 1)

        grid.addWidget(QLabel("Contrast"), 1, 0)
        self.contrast = QSlider(Qt.Horizontal)
        self.contrast.setRange(50, 300)
        self.contrast.setValue(100)
        grid.addWidget(self.contrast, 1, 1)

        grid.addWidget(QLabel("Sharpen"), 2, 0)
        self.sharpen = QSlider(Qt.Horizontal)
        self.sharpen.setRange(0, 20)
        grid.addWidget(self.sharpen, 2, 1)

        self.auto_mode = QComboBox()
        self.auto_mode.addItems(["Manual", "Auto-Adjust"])
        grid.addWidget(self.auto_mode, 3, 0, 1, 2)

        adj.setLayout(grid)
        rc.addWidget(adj)

        self.start_btn = QPushButton("Start Monitoring")
        self.stop_btn = QPushButton("Stop Monitoring")
        self.stop_btn.setEnabled(False)

        rc.addWidget(self.start_btn)
        rc.addWidget(self.stop_btn)

        self.status_label = QLabel("Status: Idle")
        rc.addWidget(self.status_label)

        rc.addStretch()

        main.addWidget(right_card, stretch=1)

        # ==============================================================
        # CAMERA + TIMER
        # ==============================================================
        self.cam = None
        self.timer = QTimer()
        self.timer.setInterval(33)
        self.timer.timeout.connect(self.update_frame)

        # Sounds
        self.sound_drowsy = QSoundEffect(self)
        self.sound_noface = QSoundEffect(self)

        if os.path.exists(ALERT_WAV):
            self.sound_drowsy.setSource(QUrl.fromLocalFile(ALERT_WAV))
        if os.path.exists(NOFACE_WAV):
            self.sound_noface.setSource(QUrl.fromLocalFile(NOFACE_WAV))

        # Buttons
        self.start_btn.clicked.connect(self.start)
        self.stop_btn.clicked.connect(self.stop)

        self.is_drowsy = False
        self.is_noface = False

    # =================================================================
    # START CAMERA
    # =================================================================
    def start(self):
        if self.cam:
            return

        self.cam = CameraProcessor()
        self.cam.on_drowsy = self.on_drowsy
        self.cam.on_clear_drowsy = self.on_drowsy_clear
        self.cam.on_noface = self.on_noface
        self.cam.on_clear_noface = self.on_noface_clear

        if not self.cam.start_processing():
            self.status_label.setText("Status: Camera Error")
            self.cam = None
            return

        self.timer.start()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        self.status_label.setText("Status: Monitoring")
        self.overlay_label.setText("Monitoring...")

    # =================================================================
    # STOP CAMERA
    # =================================================================
    def stop(self):
        if not self.cam:
            return

        self.cam.stop()
        self.cam = None

        self.video_label.clear()
        self.flash_overlay.hide()
        self.ring.hide()

        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        self.status_label.setText("Status: Idle")
        self.overlay_label.setText("Not Monitoring")

    # =================================================================
    # UPDATE FRAME
    # =================================================================
    def update_frame(self):
        if not self.cam or self.cam.latest_frame is None:
            return

        frame = self.cam.latest_frame
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]

        qimg = QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888)
        pix = QPixmap.fromImage(qimg).scaled(
            720, 480,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.video_label.setPixmap(pix)

    # =================================================================
    # ALERT EVENTS
    # =================================================================
    def on_drowsy(self):
        if not self.is_drowsy:
            try:
                self.sound_drowsy.play()
            except:
                pass

        self.is_drowsy = True

        # Flash only in the video region
        self.flash_overlay.start_flash(flashes=6, fade_ms=120)

        # Shockwave
        c = self.video_label.rect().center()
        self.ring.start(c, max_radius=250)

        self.overlay_label.setText("DROWSINESS ALERT!")
        self.overlay_label.setStyleSheet("color:#ff3a2a;font-weight:900;")

    def on_drowsy_clear(self):
        self.is_drowsy = False
        self.flash_overlay.hide()
        self.ring.hide()
        self.overlay_label.setText("Monitoring...")
        self.overlay_label.setStyleSheet("color:white;")

    def on_noface(self):
        if not self.is_noface:
            try:
                self.sound_noface.play()
            except:
                pass

        self.is_noface = True
        self.overlay_label.setText("FACE NOT VISIBLE")
        self.overlay_label.setStyleSheet("color:#ffd46a;font-weight:900;")

    def on_noface_clear(self):
        self.is_noface = False
        self.overlay_label.setText("Monitoring...")
        self.overlay_label.setStyleSheet("color:white;")
