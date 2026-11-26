"""
Corta el sprite sheet 3x3 en 9 cuadros alineados (por el teclado) y guarda
assets/frame_1.png ... frame_9.png + assets/meta.json.
Uso:  python tools/make_assets.py
"""
import json
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "assets", "source", "labrador-sprite.png")
OUT = os.path.join(HERE, "..", "assets")
TARGET_W = 400  # ancho final (px) de cada cuadro

im = Image.open(SRC).convert("RGBA")
a = np.array(im)[..., 3] > 20


def runs(v):
    out, s = [], None
    for i, x in enumerate(v):
        if x and s is None:
            s = i
        if not x and s is not None:
            out.append((s, i - 1)); s = None
    if s is not None:
        out.append((s, len(v) - 1))
    return out


cols, rows = runs(a.any(0)), runs(a.any(1))
assert len(cols) == 3 and len(rows) == 3, "No se detectó una cuadrícula 3x3"
cx = [0, (cols[0][1] + cols[1][0]) // 2, (cols[1][1] + cols[2][0]) // 2, im.width]
cy = [0, (rows[0][1] + rows[1][0]) // 2, (rows[1][1] + rows[2][0]) // 2, im.height]

frames = []
for r in range(3):
    for c in range(3):
        crop = im.crop((cx[c], cy[r], cx[c + 1], cy[r + 1]))
        m = np.array(crop)[..., 3] > 20
        ys, xs = np.where(m)
        bottom = ys.max()
        base = np.where(m[max(0, bottom - 10):bottom + 1].any(0))[0]
        anchor_x = (base.min() + base.max()) // 2
        frames.append(dict(img=crop, ax=anchor_x, ay=bottom,
                           x0=xs.min(), x1=xs.max(), y0=ys.min(),
                           kx0=base.min(), kx1=base.max()))

L = max(f["ax"] - f["x0"] for f in frames)
R = max(f["x1"] - f["ax"] for f in frames)
U = max(f["ay"] - f["y0"] for f in frames)
CW, CH = L + R + 1, U + 1
k = TARGET_W / CW

for i, f in enumerate(frames, 1):
    canvas = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
    canvas.alpha_composite(f["img"], (L - f["ax"], U - f["ay"]))
    canvas = canvas.resize((TARGET_W, round(CH * k)), Image.LANCZOS)
    canvas.save(os.path.join(OUT, f"frame_{i}.png"))

f0 = frames[0]
meta = dict(width=TARGET_W, height=round(CH * k),
            kb_x0=(L - f0["ax"] + f0["kx0"]) / CW, kb_x1=(L - f0["ax"] + f0["kx1"]) / CW)
json.dump(meta, open(os.path.join(OUT, "meta.json"), "w"))
print("OK", meta)
