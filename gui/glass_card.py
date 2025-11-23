# gui/glass_card.py
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect
from PySide6.QtGui import (
    QPainter, QColor, QBrush, QPen, QPainterPath, QLinearGradient, QRadialGradient, QPixmap
)
from PySide6.QtCore import (
    Qt, QRectF, QPropertyAnimation, QEasingCurve, Property, QTimer, QPointF
)
import random

class GlassCard(QFrame):
    def __init__(self, parent=None, radius=18):
        super().__init__(parent)
        self.radius = radius
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Colors
        self._glow_strength = 1.0
        self._hovered = False
        self._highlight_pos = 0.0

        self.fire_glow_color = QColor(255, 70, 30, 160)   # ← renamed
        self.fire_soft = QColor(255, 100, 50, 28)
        self.frost = QColor(255, 255, 255, 18)

        # Drop shadow
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(18)
        self.shadow.setOffset(0, 8)
        self.shadow.setColor(QColor(255, 80, 40, 90))
        self.setGraphicsEffect(self.shadow)

        # Animations
        self._setup_animations()

        # Noise texture
        self._noise = None
        self._noise_timer = QTimer(self)
        self._noise_timer.setInterval(1200)
        self._noise_timer.timeout.connect(self._regen_noise)
        self._noise_timer.start()
        self._regen_noise()

    # ---------------------------
    # Animations
    # ---------------------------
    def _setup_animations(self):
        self.glow_anim = QPropertyAnimation(self, b"glowStrength")
        self.glow_anim.setDuration(1800)
        self.glow_anim.setStartValue(0.8)
        self.glow_anim.setEndValue(1.4)
        self.glow_anim.setLoopCount(-1)
        self.glow_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.glow_anim.start()

        self.hlight_anim = QPropertyAnimation(self, b"highlightPos")
        self.hlight_anim.setDuration(2600)
        self.hlight_anim.setStartValue(0.0)
        self.hlight_anim.setEndValue(1.0)
        self.hlight_anim.setLoopCount(-1)
        self.hlight_anim.setEasingCurve(QEasingCurve.InOutCubic)
        self.hlight_anim.start()

        self.shadow_anim = QPropertyAnimation(self.shadow, b"blurRadius")
        self.shadow_anim.setDuration(2000)
        self.shadow_anim.setStartValue(12)
        self.shadow_anim.setEndValue(28)
        self.shadow_anim.setLoopCount(-1)
        self.shadow_anim.setEasingCurve(QEasingCurve.InOutSine)
        self.shadow_anim.start()

    def _regen_noise(self):
        w, h = 64, 64
        pix = QPixmap(w, h)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        for i in range(120):
            x = random.randrange(0, w)
            y = random.randrange(0, h)
            a = random.randrange(6, 18)
            p.setPen(Qt.NoPen)
            p.setBrush(QBrush(QColor(255, 255, 255, a)))
            p.drawRect(x, y, 1, 1)
        p.end()
        self._noise = pix

    # ---------------------------
    # Hover effect
    # ---------------------------
    def enterEvent(self, ev):
        self._hovered = True
        self._hover_burst(True)
        super().enterEvent(ev)

    def leaveEvent(self, ev):
        self._hovered = False
        self._hover_burst(False)
        super().leaveEvent(ev)

    def _hover_burst(self, on):
        anim = QPropertyAnimation(self, b"glowStrength")
        anim.setDuration(450)
        anim.setEndValue(1.8 if on else 1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()
        self._last_hover_anim = anim

    # ---------------------------
    # Properties
    # ---------------------------
    def getGlow(self):
        return self._glow_strength
    def setGlow(self, v):
        self._glow_strength = v
        self.update()
    glowStrength = Property(float, getGlow, setGlow)

    def getHighlightPos(self):
        return self._highlight_pos
    def setHighlightPos(self, v):
        self._highlight_pos = v
        self.update()
    highlightPos = Property(float, getHighlightPos, setHighlightPos)

    # ---------------------------
    # Painting
    # ---------------------------
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        path = QPainterPath()
        path.addRoundedRect(rect, self.radius, self.radius)

        # 1) Frost layer
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.frost)
        painter.drawPath(path)

        # 2) Warm linear gradient
        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        grad.setColorAt(0.0, QColor(255, 85, 40, int(20 * self._glow_strength)))
        grad.setColorAt(1.0, QColor(255, 120, 60, int(10 * self._glow_strength)))
        painter.setBrush(QBrush(grad))
        painter.drawPath(path)

        # 3) Radial bloom
        radial = QRadialGradient(rect.center(), rect.width() * 0.7)
        radial.setColorAt(0.0, QColor(255, 200, 180, int(18 * self._glow_strength)))
        radial.setColorAt(1.0, QColor(255, 90, 40, 6))
        painter.setBrush(QBrush(radial))
        painter.drawPath(path)

        # 4) Highlight sweep
        start_x = rect.left() + rect.width() * self._highlight_pos - rect.width() * 0.08
        end_x = start_x + rect.width() * 0.18
        hgrad = QLinearGradient(QPointF(start_x, rect.top()), QPointF(end_x, rect.bottom()))
        hgrad.setColorAt(0.0, QColor(255, 255, 255, 0))
        hgrad.setColorAt(0.5, QColor(255, 255, 255, int(40 * (1.0 if self._hovered else 0.6))))
        hgrad.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(hgrad))
        painter.drawPath(path)

        # 5) animated fire edge stroke (FIXED)
        base = self.fire_glow_color
        glow_color = QColor(
            base.red(),
            base.green(),
            base.blue(),
            min(220, int(120 * self._glow_strength))
        )
        pen = QPen(glow_color)
        pen.setWidth(4 + int(2 * (self._glow_strength - 1.0)))
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        # 6) noise texture
        if self._noise:
            painter.setOpacity(0.06)
            painter.drawPixmap(
                rect.toRect(),
                self._noise.scaled(rect.width(), rect.height(),
                                   Qt.IgnoreAspectRatio,
                                   Qt.SmoothTransformation)
            )
            painter.setOpacity(1.0)

        painter.end()
