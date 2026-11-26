"""
Perrito Widget para Windows 11  (labrador negro)
------------------------------------------------
Un labrador chiquito que vive en tu escritorio y teclea contigo:
  - Cuando presionas una tecla, levanta/baja la patita (izquierda o derecha según la tecla).
  - Si tecleas rápido, usa las dos patitas y mueve la cola.
  - Si mueves el mouse, levanta la patita izquierda y un mouse a su lado se mueve
    contigo (se pone verde al hacer clic).
  - En reposo mueve la cola, parpadea y a veces mira curioso.
  - Salen teclitas voladoras con la letra que presionas.

Instalación:   pip install PySide6 pynput
Ejecutar:      pythonw perrito_widget.py      (o python perrito_widget.py)

Controles:  arrastra con clic izquierdo · rueda = tamaño · clic derecho = menú
Privacidad: solo se muestra la tecla en pantalla; no se guarda ni se envía nada.
"""
import os
import random
import sys
import time
import traceback


def fatal(msg):
    """Muestra el error en una ventana (y lo guarda), porque con pythonw no hay consola."""
    try:
        log = os.path.join(os.path.expanduser("~"), "perrito_widget_error.log")
        with open(log, "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S") + "\n" + msg + "\n\n")
    except OSError:
        pass
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, msg[-1500:], "Perrito Widget - error", 0x10)
    except Exception:
        print(msg, file=sys.stderr)


try:
    from pynput import keyboard, mouse
    from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
    from PySide6.QtGui import (QColor, QCursor, QFont, QGuiApplication, QIcon,
                               QPainter, QPen, QPixmap)
    from PySide6.QtWidgets import (QApplication, QMenu, QSystemTrayIcon,
                                   QWidget)
except ImportError:
    fatal("Faltan dependencias. Abre una terminal y ejecuta:\n\n"
          "pip install PySide6 pynput\n\n" + traceback.format_exc())
    sys.exit(1)

SPR_W = 200      # ancho del perrito en pantalla (a escala 1.0)
ML, MR = 40, 6   # márgenes: a la izquierda va el mouse
KB_X0, KB_X1 = 0.0056, 0.8827   # extremos del teclado dentro del cuadro (0..1)

KEY = QColor("#F1E9DA")
KB_BASE = QColor("#2B2B33")
MOUSE_GREEN = QColor("#9ADB3C")

MOUSE_ACTIVE_SECS = 0.6


def resource(rel):
    """Resuelve recursos tanto en Python como en el EXE de PyInstaller."""
    candidates = []

    # En un ejecutable --onefile, PyInstaller extrae los datos en _MEIPASS.
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(os.path.join(meipass, rel))

    # Alternativa: recursos distribuidos junto al EXE.
    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
    candidates.append(os.path.join(exe_dir, rel))

    # Ejecución normal desde el código fuente.
    source_dir = os.path.dirname(os.path.abspath(__file__))
    candidates.append(os.path.join(source_dir, rel))

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    return candidates[0] if candidates else os.path.join(source_dir, rel)


class Dog(QWidget):
    key_pressed = Signal(str)
    clicked = Signal(bool)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Cuadros 1..9 del sprite. Validamos todos los archivos para detectar
        # paquetes incompletos y mostrar una ruta útil para diagnosticarlo.
        frame_paths = {n: resource(f"assets/frame_{n}.png") for n in range(1, 10)}
        missing = [path for path in frame_paths.values() if not os.path.isfile(path)]
        if missing:
            raise FileNotFoundError(
                "No se encontraron todos los cuadros de la mascota.\\n\\n"
                "Archivos faltantes:\\n" + "\\n".join(missing) +
                "\\n\\nVuelve a descargar el ejecutable generado por la última "
                "compilación de GitHub Actions. El workflow debe incluir la carpeta "
                "'assets' mediante PyInstaller."
            )
        self.frames = {n: QPixmap(frame_paths[n]) for n in range(1, 10)}
        invalid = [n for n, pm in self.frames.items() if pm.isNull()]
        if invalid:
            raise RuntimeError(
                "Hay imágenes PNG dañadas o ilegibles en assets: " +
                ", ".join(str(n) for n in invalid)
            )
        pm = self.frames[1]
        self.spr_h = SPR_W * pm.height() / pm.width()
        self.base_w = ML + SPR_W + MR
        self.base_h = int(self.spr_h) + 6

        self.scale = 1.0
        self.on_top = True
        self.resize(self.base_w, self.base_h)

        # estado
        self.cur = 1
        self.key_frame = 1
        self.key_until = 0.0
        self.blink_until = 0.0
        self.curious_until = 0.0
        self.recent = []
        self.flip = False
        self.lcount = 0
        self.bounce = 0.0
        self.mouse_off = QPointF(0, 0)
        self.last_cursor = QCursor.pos()
        self.last_mouse_act = -10.0
        self.mouse_down = False
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
        self.move(geo.right() - self.base_w - 20, geo.bottom() - self.base_h - 10)

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
        self.recent = [t for t in self.recent if now - t < 0.4] + [now]
        h = ord(ch[0]) if ch else random.randint(0, 99)
        left = (h % 14) < 7

        if len(self.recent) >= 3:        # tecleo rápido: las dos patitas
            self.flip = not self.flip
            self.key_frame = 4 if self.flip else 6
            hold = 0.22
        elif left:                       # patita izquierda
            self.lcount += 1
            self.key_frame = 2 if self.lcount % 2 else 8
            hold = 0.16
        else:                            # patita derecha
            self.key_frame = 3
            hold = 0.16
        self.key_until = now + hold
        self.bounce = 1.0

        if ch.strip() or ch == "␣":
            frac = (h % 14) / 13
            x = ML + SPR_W * (KB_X0 + (KB_X1 - KB_X0) * frac)
            self.caps.append({
                "ch": ch.upper(), "x": x, "y": self.spr_h * 0.80,
                "vx": random.uniform(-1.0, 1.0), "vy": random.uniform(-2.2, -1.5),
                "rot": random.uniform(-15, 15), "vr": random.uniform(-4, 4), "life": 1.0,
            })

    def on_click(self, pressed):
        self.mouse_down = pressed
        self.last_mouse_act = time.monotonic()

    def pick_frame(self, now):
        if self.mouse_active(now):
            # mientras mueves el mouse: izquierda en el mouse, derecha puede teclear
            return 3 if now < self.key_until else 8
        if now < self.key_until:
            return self.key_frame
        if now < self.blink_until:
            return 5
        if now < self.curious_until:
            return 7
        return 1 if int(now / 0.7) % 2 == 0 else 9   # cola en reposo

    def tick(self):
        now = time.monotonic()
        self.bounce = max(0.0, self.bounce - 0.12)

        cur = QCursor.pos()
        d = cur - self.last_cursor
        self.last_cursor = cur
        if d.x() or d.y():
            self.last_mouse_act = now
            self.mouse_off += QPointF(d.x(), d.y()) * 0.10
            self.mouse_off.setX(max(-7, min(7, self.mouse_off.x())))
            self.mouse_off.setY(max(-7, min(7, self.mouse_off.y())))
        self.mouse_off *= 0.93

        if now > self.blink_until and random.random() < 0.004:
            self.blink_until = now + 0.15
        if now > self.curious_until and random.random() < 0.0015:
            self.curious_until = now + 1.2

        self.cur = self.pick_frame(now)

        for c in self.caps:
            c["x"] += c["vx"]; c["y"] += c["vy"]; c["vy"] += 0.03
            c["rot"] += c["vr"]; c["life"] -= 0.022
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
        self.resize(int(self.base_w * self.scale), int(self.base_h * self.scale))

    # ---- dibujo ----
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        p.scale(self.scale, self.scale)

        pm = self.frames[self.cur]
        p.drawPixmap(QRectF(ML, 2 + 2.5 * self.bounce, SPR_W, self.spr_h), pm, QRectF(pm.rect()))
        self.draw_mouse(p)
        self.draw_caps(p)

    def draw_mouse(self, p):
        pos = QPointF(20, self.base_h - 30) + self.mouse_off
        p.setBrush(MOUSE_GREEN if self.mouse_down else KEY)
        p.setPen(QPen(KB_BASE, 1.5))
        p.drawEllipse(QRectF(pos.x() - 8, pos.y() - 11, 16, 22))
        p.drawLine(QPointF(pos.x(), pos.y() - 11), QPointF(pos.x(), pos.y() - 3))

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


def main():
    app = QApplication(sys.argv)

    def hook(exc_type, exc, tb):
        fatal("".join(traceback.format_exception(exc_type, exc, tb)))
        app.quit()
    sys.excepthook = hook

    try:
        dog = Dog()
        dog.show()
        dog.raise_()

        # ícono en la bandeja del sistema (junto al reloj) para poder cerrarlo siempre
        tray = QSystemTrayIcon(QIcon(dog.frames[1]), dog)
        menu = QMenu()
        menu.addAction("Salir").triggered.connect(app.quit)
        tray.setContextMenu(menu)
        tray.setToolTip("Perrito Widget")
        tray.show()
        dog.tray, dog.tray_menu = tray, menu
    except Exception:
        fatal(traceback.format_exc())
        sys.exit(1)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
