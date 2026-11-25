"""
Perrito Widget para Windows 11
------------------------------
Un perrito que vive en tu escritorio:
  - Sus ojos siguen el cursor.
  - Una patita mueve el mouse cuando tú lo mueves (se pone verde al hacer clic).
  - La otra patita teclea: salen teclitas con la letra que presionas.
  - Mueve la cola más rápido cuando escribes.

Instalación:   pip install PySide6 pynput
Ejecutar:      pythonw perrito_widget.py      (o python perrito_widget.py)

Controles:  arrastra con clic izquierdo · rueda = tamaño · clic derecho = menú
Privacidad: solo se muestra la tecla en pantalla; no se guarda ni se envía nada.
"""
import math
import random
import sys

from pynput import keyboard, mouse
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (QBrush, QColor, QCursor, QFont, QGuiApplication,
                           QPainter, QPainterPath, QPen, QPolygonF)
from PySide6.QtWidgets import QApplication, QMenu, QWidget

W, H = 380, 340

TAN = QColor("#C98B4A")
TAN_DARK = QColor("#B07235")
WHITE = QColor("#FFF6E8")
PINK = QColor("#F2A6A6")
NOSE = QColor("#2A1B16")
KB_BASE = QColor("#2B2B33")
KEY = QColor("#F1E9DA")
KEY_ACCENT = QColor("#F0A93B")
MOUSE_GREEN = QColor("#9ADB3C")

KB_X, KB_Y, KB_COLS, KB_ROWS = 88, 276, 14, 3
KEY_W, KEY_H = 16, 11
MOUSE_BASE = QPointF(50, 296)


class Dog(QWidget):
    key_pressed = Signal(str)
    clicked = Signal(bool)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.scale = 1.0
        self.resize(W, H)

        # Estado de animación
        self.t = 0.0
        self.typing = 0.0          # 0..1, decae con el tiempo
        self.press = 0.0           # hundimiento de la pata que teclea
        self.paw = QPointF(230, 270)
        self.paw_target = QPointF(230, 270)
        self.hit_key = (0, 0)
        self.mouse_off = QPointF(0, 0)
        self.last_cursor = QCursor.pos()
        self.mouse_down = False
        self.blink = 0
        self.caps = []
        self.drag = None

        self.key_pressed.connect(self.on_key)
        self.clicked.connect(self.on_click)

        # Escucha global de teclado y clics
        self.kl = keyboard.Listener(on_press=self._kp)
        self.ml = mouse.Listener(on_click=self._mc)
        self.kl.daemon = self.ml.daemon = True
        self.kl.start()
        self.ml.start()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)

        geo = QGuiApplication.primaryScreen().availableGeometry()
        self.move(geo.right() - W - 20, geo.bottom() - H - 10)

    # ---- hilos de pynput -> señales Qt ----
    def _kp(self, key):
        try:
            ch = key.char if key.char else "?"
        except AttributeError:
            ch = {"space": "␣", "enter": "⏎", "backspace": "⌫", "tab": "⇥"}.get(key.name, "")
        self.key_pressed.emit(ch)

    def _mc(self, x, y, button, pressed):
        self.clicked.emit(pressed)

    # ---- eventos ----
    def on_key(self, ch):
        self.typing = 1.0
        self.press = 1.0
        h = ord(ch[0]) if ch else random.randint(0, 99)
        col, row = h % KB_COLS, (h // KB_COLS) % KB_ROWS
        self.hit_key = (col, row)
        self.paw_target = QPointF(KB_X + col * KEY_W + KEY_W / 2 + 4,
                                  KB_Y + row * KEY_H + KEY_H / 2 + 4)
        if ch.strip() or ch == "␣":
            self.caps.append({
                "ch": ch.upper(), "x": self.paw_target.x(), "y": self.paw_target.y() - 16,
                "vx": random.uniform(-1.6, 1.6), "vy": random.uniform(-3.2, -2.2),
                "rot": random.uniform(-15, 15), "vr": random.uniform(-4, 4), "life": 1.0,
            })

    def on_click(self, pressed):
        self.mouse_down = pressed

    def tick(self):
        self.t += 0.016
        self.typing = max(0.0, self.typing - 0.012)
        self.press = max(0.0, self.press - 0.09)

        # Pata que teclea persigue su tecla
        self.paw += (self.paw_target - self.paw) * 0.35

        # Mouse: se desplaza con el movimiento real del cursor
        cur = QCursor.pos()
        d = cur - self.last_cursor
        self.last_cursor = cur
        self.mouse_off += QPointF(d.x(), d.y()) * 0.15
        self.mouse_off.setX(max(-16, min(16, self.mouse_off.x())))
        self.mouse_off.setY(max(-12, min(12, self.mouse_off.y())))
        self.mouse_off *= 0.94

        # Parpadeo
        if self.blink > 0:
            self.blink -= 1
        elif random.random() < 0.006:
            self.blink = 8

        # Teclitas voladoras
        for c in self.caps:
            c["x"] += c["vx"]; c["y"] += c["vy"]; c["vy"] += 0.04
            c["rot"] += c["vr"]; c["life"] -= 0.02
        self.caps = [c for c in self.caps if c["life"] > 0]
        self.update()

    # ---- interacción de ventana ----
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
        elif e.button() == Qt.RightButton:
            m = QMenu(self)
            top = m.addAction("Siempre visible")
            top.setCheckable(True); top.setChecked(True)
            quit_ = m.addAction("Salir")
            act = m.exec(e.globalPosition().toPoint())
            if act == quit_:
                QApplication.quit()
            elif act == top:
                f = self.windowFlags() ^ Qt.WindowStaysOnTopHint
                self.setWindowFlags(f); self.show()

    def mouseMoveEvent(self, e):
        if self.drag is not None and e.buttons() & Qt.LeftButton:
            self.move(e.globalPosition().toPoint() - self.drag)

    def mouseReleaseEvent(self, e):
        self.drag = None

    def wheelEvent(self, e):
        self.scale = max(0.5, min(2.0, self.scale + (0.1 if e.angleDelta().y() > 0 else -0.1)))
        self.resize(int(W * self.scale), int(H * self.scale))

    # ---- dibujo ----
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.scale(self.scale, self.scale)
        p.setPen(Qt.NoPen)

        self.draw_tail(p)
        self.draw_body(p)
        self.draw_head(p)
        self.draw_keyboard(p)
        mouse_pos = self.draw_mouse(p)
        self.draw_arm(p, QPointF(152, 232), QPointF(mouse_pos.x(), mouse_pos.y() - 6))
        typing_paw = QPointF(self.paw.x(), self.paw.y() + 5 * self.press)
        self.draw_arm(p, QPointF(228, 232), typing_paw)
        self.draw_caps(p)

    def ell(self, p, color, cx, cy, w, h):
        p.setBrush(QBrush(color))
        p.drawEllipse(QRectF(cx - w / 2, cy - h / 2, w, h))

    def draw_tail(self, p):
        speed = 6 + 14 * self.typing
        ang = math.sin(self.t * speed) * (18 + 14 * self.typing)
        p.save()
        p.translate(255, 270)
        p.rotate(ang - 25)
        p.setPen(QPen(TAN, 16, Qt.SolidLine, Qt.RoundCap))
        path = QPainterPath(QPointF(0, 0))
        path.cubicTo(30, -5, 45, -25, 42, -55)
        p.drawPath(path)
        p.setPen(Qt.NoPen)
        self.ell(p, WHITE, 42, -55, 14, 14)
        p.restore()

    def draw_body(self, p):
        self.ell(p, TAN, 190, 235, 140, 150)         # cuerpo
        self.ell(p, WHITE, 190, 242, 70, 100)         # pecho
        self.ell(p, TAN_DARK, 138, 275, 50, 40)       # patas traseras
        self.ell(p, TAN_DARK, 242, 275, 50, 40)

    def draw_head(self, p):
        cx, cy = 190, 135
        wob = math.sin(self.t * 25) * 3 * self.typing  # orejas se mueven al teclear
        # orejas
        for side in (-1, 1):
            ear = QPolygonF([QPointF(cx + side * 48, cy - 28),
                             QPointF(cx + side * (62 + wob), cy - 88),
                             QPointF(cx + side * 12, cy - 48)])
            p.setBrush(TAN_DARK); p.drawPolygon(ear)
            inner = QPolygonF([QPointF(cx + side * 44, cy - 34),
                               QPointF(cx + side * (54 + wob), cy - 74),
                               QPointF(cx + side * 22, cy - 46)])
            p.setBrush(PINK); p.drawPolygon(inner)
        self.ell(p, TAN, cx, cy, 124, 108)            # cabeza
        self.ell(p, WHITE, cx, cy + 24, 70, 52)       # hocico
        self.ell(p, WHITE, cx, cy - 18, 14, 40)       # franja

        # ojos que siguen el cursor
        gc = self.mapToGlobal(QPointF(cx * self.scale, (cy - 8) * self.scale).toPoint())
        cur = QCursor.pos()
        dx, dy = cur.x() - gc.x(), cur.y() - gc.y()
        dist = math.hypot(dx, dy) or 1
        k = min(dist / 150, 1) * 5
        ox, oy = dx / dist * k, dy / dist * k
        for ex in (cx - 26, cx + 26):
            if self.blink:
                p.setPen(QPen(NOSE, 3, Qt.SolidLine, Qt.RoundCap))
                p.drawLine(QPointF(ex - 9, cy - 8), QPointF(ex + 9, cy - 8))
                p.setPen(Qt.NoPen)
            else:
                self.ell(p, QColor("white"), ex, cy - 8, 28, 28)
                self.ell(p, NOSE, ex + ox, cy - 8 + oy, 15, 15)
                self.ell(p, QColor("white"), ex + ox + 3, cy - 12 + oy, 5, 5)

        # nariz y boca
        self.ell(p, NOSE, cx, cy + 14, 22, 15)
        p.setPen(QPen(NOSE, 2.5, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(cx, cy + 21), QPointF(cx, cy + 30))
        path = QPainterPath(QPointF(cx - 16, cy + 30))
        path.quadTo(cx - 8, cy + 38, cx, cy + 30)
        path.quadTo(cx + 8, cy + 38, cx + 16, cy + 30)
        p.drawPath(path)
        p.setPen(Qt.NoPen)
        if self.typing > 0.3:                          # lengüita feliz
            self.ell(p, PINK, cx, cy + 40, 14, 16)

    def draw_keyboard(self, p):
        p.setBrush(KB_BASE)
        p.drawRoundedRect(QRectF(KB_X - 8, KB_Y - 6, KB_COLS * KEY_W + 16, KB_ROWS * KEY_H + 12), 7, 7)
        for r in range(KB_ROWS):
            for c in range(KB_COLS):
                hit = (c, r) == self.hit_key and self.press > 0.2
                if hit:
                    col = QColor("#FFD27A")
                elif r == 0 and c == KB_COLS - 1:
                    col = KEY_ACCENT
                else:
                    col = KEY
                p.setBrush(col)
                p.drawRoundedRect(QRectF(KB_X + c * KEY_W + 1, KB_Y + r * KEY_H + 1 + (1 if hit else 0),
                                         KEY_W - 2, KEY_H - 2), 2, 2)

    def draw_mouse(self, p):
        pos = MOUSE_BASE + self.mouse_off
        p.setBrush(MOUSE_GREEN if self.mouse_down else KEY)
        p.setPen(QPen(KB_BASE, 2))
        p.drawEllipse(QRectF(pos.x() - 14, pos.y() - 18, 28, 36))
        p.drawLine(QPointF(pos.x(), pos.y() - 18), QPointF(pos.x(), pos.y() - 4))
        p.setPen(Qt.NoPen)
        return pos

    def draw_arm(self, p, shoulder, paw):
        p.setPen(QPen(TAN, 28, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(shoulder, paw)
        p.setPen(Qt.NoPen)
        self.ell(p, WHITE, paw.x(), paw.y(), 30, 26)
        p.setBrush(TAN_DARK)
        for dx in (-7, 0, 7):                           # deditos
            p.drawEllipse(QRectF(paw.x() + dx - 1.5, paw.y() + 2, 3, 6))

    def draw_caps(self, p):
        p.setFont(QFont("Segoe UI", 9, QFont.Bold))
        for c in self.caps:
            p.save()
            p.setOpacity(max(0.0, min(1.0, c["life"] * 1.6)))
            p.translate(c["x"], c["y"])
            p.rotate(c["rot"])
            p.setBrush(QColor("white"))
            p.setPen(QPen(QColor("#B9B2A5"), 1.5))
            p.drawRoundedRect(QRectF(-11, -11, 22, 22), 4, 4)
            p.setPen(QColor("#333"))
            p.drawText(QRectF(-11, -11, 22, 22), Qt.AlignCenter, c["ch"])
            p.restore()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dog = Dog()
    dog.show()
    sys.exit(app.exec())
