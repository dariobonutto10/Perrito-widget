"""
Perrito Widget para Windows 11  (versión chiquita: dálmata)
-----------------------------------------------------------
Un dálmata chibi que vive en tu escritorio:
  - Sus ojos siguen el cursor.
  - Las patitas descansan quietas. Solo bajan al teclado cuando presionas una tecla.
  - Si mueves el mouse, una patita va al mouse y lo mueve (se pone verde al hacer clic).
  - Si el mouse está quieto, usa las dos patitas para teclear.
  - Salen teclitas voladoras con la letra que presionas.

Instalación:   pip install PySide6 pynput
Ejecutar:      pythonw perrito_widget.py      (o python perrito_widget.py)

Controles:  arrastra con clic izquierdo · rueda = tamaño · clic derecho = menú
Privacidad: solo se muestra la tecla en pantalla; no se guarda ni se envía nada.
"""
import math
import random
import sys
import time

from pynput import keyboard, mouse
from PySide6.QtCore import QPoint, QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import (QColor, QCursor, QFont, QGuiApplication, QPainter,
                           QPainterPath, QPen)
from PySide6.QtWidgets import QApplication, QMenu, QWidget

W, H = 240, 220

FUR = QColor("#FBFAF6")
SPOT = QColor("#2B2B2E")
LINE = QColor("#45454D")
PINK = QColor("#F6A9B1")
BLUSH = QColor(255, 140, 155, 120)
KB_BASE = QColor("#2B2B33")
KEY = QColor("#F1E9DA")
KEY_ACCENT = QColor("#F0A93B")
KEY_HIT = QColor("#FFD27A")
MOUSE_GREEN = QColor("#9ADB3C")

KB_X, KB_Y, KB_COLS, KB_ROWS = 50, 176, 14, 3
KEY_W, KEY_H = 10, 8
MOUSE_BASE = QPointF(26, 192)
SHOULDER = {"L": QPointF(94, 142), "R": QPointF(146, 142)}
REST = {"L": QPointF(99, 160), "R": QPointF(141, 160)}

MOUSE_ACTIVE_SECS = 0.6   # tiempo que la patita sigue en el mouse tras moverlo
KEY_HOLD_SECS = 0.2       # tiempo que la patita se queda en la tecla


class Paw:
    def __init__(self, rest):
        self.pos = QPointF(rest)
        self.key_target = None
        self.key_until = 0.0
        self.press = 0.0
        self.hit = (0, 0)


class Dog(QWidget):
    key_pressed = Signal(str)
    clicked = Signal(bool)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.scale = 1.0
        self.on_top = True
        self.resize(W, H)

        self.t = 0.0
        self.typing = 0.0
        self.paws = {"L": Paw(REST["L"]), "R": Paw(REST["R"])}
        self.mouse_off = QPointF(0, 0)
        self.last_cursor = QCursor.pos()
        self.last_mouse_act = -10.0
        self.mouse_down = False
        self.blink = 0
        self.caps = []
        self.drag = None

        self.key_pressed.connect(self.on_key)
        self.clicked.connect(self.on_click)

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
    def mouse_active(self, now):
        return now - self.last_mouse_act < MOUSE_ACTIVE_SECS

    def on_key(self, ch):
        now = time.monotonic()
        self.typing = 1.0
        h = ord(ch[0]) if ch else random.randint(0, 99)
        col, row = h % KB_COLS, (h // KB_COLS) % KB_ROWS
        side = "L" if col < KB_COLS // 2 else "R"
        if side == "L" and self.mouse_active(now):
            side = "R"  # la izquierda está ocupada con el mouse
        paw = self.paws[side]
        paw.key_target = QPointF(KB_X + col * KEY_W + KEY_W / 2,
                                 KB_Y + row * KEY_H + KEY_H / 2)
        paw.key_until = now + KEY_HOLD_SECS
        paw.press = 1.0
        paw.hit = (col, row)
        if ch.strip() or ch == "␣":
            self.caps.append({
                "ch": ch.upper(), "x": paw.key_target.x(), "y": paw.key_target.y() - 10,
                "vx": random.uniform(-1.0, 1.0), "vy": random.uniform(-2.0, -1.4),
                "rot": random.uniform(-15, 15), "vr": random.uniform(-4, 4), "life": 1.0,
            })

    def on_click(self, pressed):
        self.mouse_down = pressed
        self.last_mouse_act = time.monotonic()

    def mouse_pos(self):
        return MOUSE_BASE + self.mouse_off

    def tick(self):
        now = time.monotonic()
        self.t += 0.016
        self.typing = max(0.0, self.typing - 0.012)

        # Movimiento real del cursor
        cur = QCursor.pos()
        d = cur - self.last_cursor
        self.last_cursor = cur
        if d.x() or d.y():
            self.last_mouse_act = now
            self.mouse_off += QPointF(d.x(), d.y()) * 0.12
            self.mouse_off.setX(max(-10, min(10, self.mouse_off.x())))
            self.mouse_off.setY(max(-8, min(8, self.mouse_off.y())))
        self.mouse_off *= 0.93

        mouse_busy = self.mouse_active(now)
        for name, paw in self.paws.items():
            if name == "L" and mouse_busy:
                mp = self.mouse_pos()
                target = QPointF(mp.x(), mp.y() - 4)
            elif now < paw.key_until and paw.key_target is not None:
                target = paw.key_target
            else:
                target = REST[name]
            paw.pos += (target - paw.pos) * 0.35
            paw.press = max(0.0, paw.press - 0.09)

        if self.blink > 0:
            self.blink -= 1
        elif random.random() < 0.006:
            self.blink = 8

        for c in self.caps:
            c["x"] += c["vx"]; c["y"] += c["vy"]; c["vy"] += 0.03
            c["rot"] += c["vr"]; c["life"] -= 0.025
        self.caps = [c for c in self.caps if c["life"] > 0]
        self.update()

    # ---- interacción de ventana ----
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
        elif e.button() == Qt.RightButton:
            m = QMenu(self)
            top = m.addAction("Siempre visible")
            top.setCheckable(True)
            top.setChecked(self.on_top)
            quit_ = m.addAction("Salir")
            act = m.exec(e.globalPosition().toPoint())
            if act == quit_:
                QApplication.quit()
            elif act == top:
                self.on_top = not self.on_top
                self.setWindowFlag(Qt.WindowStaysOnTopHint, self.on_top)
                self.show()

    def mouseMoveEvent(self, e):
        if self.drag is not None and e.buttons() & Qt.LeftButton:
            self.move(e.globalPosition().toPoint() - self.drag)

    def mouseReleaseEvent(self, e):
        self.drag = None

    def wheelEvent(self, e):
        self.scale = max(0.5, min(2.5, self.scale + (0.1 if e.angleDelta().y() > 0 else -0.1)))
        self.resize(int(W * self.scale), int(H * self.scale))

    # ---- dibujo ----
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.scale(self.scale, self.scale)

        now = time.monotonic()
        self.draw_tail(p)
        self.draw_body(p)
        self.draw_head(p)
        self.draw_keyboard(p)
        mp = self.draw_mouse(p)
        for name, paw in self.paws.items():
            pos = QPointF(paw.pos)
            if now < paw.key_until:
                pos.setY(pos.y() + 2.5 * paw.press)
            self.draw_arm(p, SHOULDER[name], pos)
        self.draw_caps(p)

    def ell(self, p, color, cx, cy, w, h, outline=True):
        p.setBrush(color)
        p.setPen(QPen(LINE, 1.6) if outline else Qt.NoPen)
        p.drawEllipse(QRectF(cx - w / 2, cy - h / 2, w, h))

    def stroke(self, p, path, width):
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(LINE, width + 3, Qt.SolidLine, Qt.RoundCap))
        p.drawPath(path)
        p.setPen(QPen(FUR, width, Qt.SolidLine, Qt.RoundCap))
        p.drawPath(path)

    def draw_tail(self, p):
        speed = 6 + 14 * self.typing
        ang = math.sin(self.t * speed) * (16 + 12 * self.typing)
        p.save()
        p.translate(152, 152)
        p.rotate(ang - 20)
        path = QPainterPath(QPointF(0, 0))
        path.cubicTo(16, -2, 26, -14, 24, -30)
        self.stroke(p, path, 8)
        p.restore()

    def draw_body(self, p):
        self.ell(p, FUR, 120, 140, 70, 62)
        self.ell(p, SPOT, 104, 136, 14, 12, False)
        self.ell(p, SPOT, 139, 147, 16, 12, False)
        self.ell(p, SPOT, 127, 127, 9, 8, False)

    def draw_head(self, p):
        cx, cy = 120, 78
        wob = math.sin(self.t * 25) * 4 * self.typing
        for side in (-1, 1):  # orejas caídas
            p.save()
            p.translate(cx + side * 44, cy - 4)
            p.rotate(-side * 12 + side * wob)
            self.ell(p, SPOT, 0, 0, 24, 42)
            p.restore()
        self.ell(p, FUR, cx, cy, 108, 92)
        self.ell(p, SPOT, cx + 24, cy - 30, 18, 14, False)
        self.ell(p, SPOT, cx - 38, cy + 14, 12, 10, False)

        # ojos que siguen el cursor
        gc = self.mapToGlobal(QPoint(int(cx * self.scale), int((cy - 2) * self.scale)))
        cur = QCursor.pos()
        dx, dy = cur.x() - gc.x(), cur.y() - gc.y()
        dist = math.hypot(dx, dy) or 1
        k = min(dist / 150, 1) * 2.5
        ox, oy = dx / dist * k, dy / dist * k
        for ex in (cx - 22, cx + 22):
            if self.blink:
                p.setBrush(Qt.NoBrush)
                p.setPen(QPen(SPOT, 2.5, Qt.SolidLine, Qt.RoundCap))
                p.drawLine(QPointF(ex - 6, cy - 2), QPointF(ex + 6, cy - 2))
            else:
                self.ell(p, SPOT, ex + ox, cy - 2 + oy, 14, 17, False)
                self.ell(p, QColor("white"), ex + ox + 2.5, cy - 6 + oy, 5, 5, False)
                self.ell(p, QColor("white"), ex + ox - 2, cy + 2 + oy, 2.5, 2.5, False)

        for bx in (cx - 36, cx + 36):  # cachetes
            self.ell(p, BLUSH, bx, cy + 14, 14, 8, False)

        if self.typing > 0.3:  # lengüita feliz
            self.ell(p, PINK, cx, cy + 24, 9, 10)
        self.ell(p, SPOT, cx, cy + 10, 14, 10, False)  # nariz
        self.ell(p, QColor(255, 255, 255, 170), cx - 2.5, cy + 8, 4, 2.5, False)
        p.setPen(QPen(SPOT, 1.8, Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        p.drawLine(QPointF(cx, cy + 15), QPointF(cx, cy + 19))
        path = QPainterPath(QPointF(cx - 8, cy + 19))
        path.quadTo(cx - 4, cy + 25, cx, cy + 19)
        path.quadTo(cx + 4, cy + 25, cx + 8, cy + 19)
        p.drawPath(path)

    def draw_keyboard(self, p):
        p.setPen(Qt.NoPen)
        p.setBrush(KB_BASE)
        p.drawRoundedRect(QRectF(KB_X - 5, KB_Y - 4, KB_COLS * KEY_W + 10, KB_ROWS * KEY_H + 8), 5, 5)
        hits = {pw.hit for pw in self.paws.values() if pw.press > 0.2}
        for r in range(KB_ROWS):
            for c in range(KB_COLS):
                if (c, r) in hits:
                    col = KEY_HIT
                elif r == 0 and c == KB_COLS - 1:
                    col = KEY_ACCENT
                else:
                    col = KEY
                p.setBrush(col)
                p.drawRoundedRect(QRectF(KB_X + c * KEY_W + 0.8, KB_Y + r * KEY_H + 0.8,
                                         KEY_W - 1.6, KEY_H - 1.6), 1.5, 1.5)

    def draw_mouse(self, p):
        pos = self.mouse_pos()
        p.setBrush(MOUSE_GREEN if self.mouse_down else KEY)
        p.setPen(QPen(KB_BASE, 1.5))
        p.drawEllipse(QRectF(pos.x() - 8, pos.y() - 11, 16, 22))
        p.drawLine(QPointF(pos.x(), pos.y() - 11), QPointF(pos.x(), pos.y() - 3))
        return pos

    def draw_arm(self, p, shoulder, paw):
        path = QPainterPath(shoulder)
        path.lineTo(paw)
        self.stroke(p, path, 12)
        self.ell(p, FUR, paw.x(), paw.y(), 17, 15)
        p.setPen(QPen(LINE, 1.2, Qt.SolidLine, Qt.RoundCap))
        for dx in (-3, 3):  # deditos
            p.drawLine(QPointF(paw.x() + dx, paw.y() + 2), QPointF(paw.x() + dx, paw.y() + 6))

    def draw_caps(self, p):
        p.setFont(QFont("Segoe UI", 7, QFont.Bold))
        for c in self.caps:
            p.save()
            p.setOpacity(max(0.0, min(1.0, c["life"] * 1.6)))
            p.translate(c["x"], c["y"])
            p.rotate(c["rot"])
            p.setBrush(QColor("white"))
            p.setPen(QPen(QColor("#B9B2A5"), 1.2))
            p.drawRoundedRect(QRectF(-8, -8, 16, 16), 3, 3)
            p.setPen(QColor("#333"))
            p.drawText(QRectF(-8, -8, 16, 16), Qt.AlignCenter, c["ch"])
            p.restore()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dog = Dog()
    dog.show()
    sys.exit(app.exec())
