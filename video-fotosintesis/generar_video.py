#!/usr/bin/env python3
"""
Vídeo explicativo: «¿Cómo funciona la fotosíntesis?»

Todo el vídeo se genera por código: cada fotograma se dibuja con Pillow,
la música se sintetiza con NumPy y FFmpeg une todo en un MP4.

Uso:
    python3 generar_video.py                 # genera fotosintesis.mp4
    python3 generar_video.py --preview 12.5  # guarda solo el fotograma del segundo 12.5

Requisitos: Python 3, Pillow, NumPy y FFmpeg.
"""
import argparse
import math
import os
import random
import subprocess
import sys
import wave
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- ajustes
W, H = 1920, 1080          # resolución final
FPS = 30
S = 2                      # sobremuestreo (se dibuja a 2x y se reduce: bordes suaves)
AQUI = os.path.dirname(os.path.abspath(__file__))

FONT_DIRS = ["/usr/share/fonts/opentype/inter/", "/usr/share/fonts/truetype/dejavu/"]
FONTS = {
    "xb": ["Inter-ExtraBold.otf", "DejaVuSans-Bold.ttf"],
    "bold": ["Inter-Bold.otf", "DejaVuSans-Bold.ttf"],
    "semi": ["Inter-SemiBold.otf", "DejaVuSans-Bold.ttf"],
    "reg": ["Inter-Regular.otf", "DejaVuSans.ttf"],
}

# ---------------------------------------------------------------- colores
SKY_TOP, SKY_BOT = (110, 185, 240), (205, 235, 252)
HILL1, HILL2 = (150, 205, 120), (125, 190, 100)
GRASS = (100, 175, 75)
SOIL_TOP, SOIL_BOT = (125, 88, 58), (90, 62, 40)
LEAF, LEAF_DARK = (70, 170, 75), (35, 115, 50)
STEM = (75, 145, 60)
ROOT = (225, 195, 145)
SUN, SUN_LIGHT = (255, 196, 40), (255, 228, 110)
WATER = (60, 155, 235)
CARBON = (80, 85, 95)
OXY = (232, 72, 72)
HYD = (245, 245, 250)
GLU, GLU_DARK = (248, 172, 40), (200, 120, 20)
DARK = (28, 40, 48)
GREY = (95, 105, 115)
WHITE = (255, 255, 255)
GREEN_TXT = (40, 125, 55)
ORANGE = (235, 130, 30)


# ---------------------------------------------------------------- utilidades
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, start, dur):
    return clamp((t - start) / dur) if dur > 0 else float(t >= start)


def eo(x):  # ease-out cúbico
    x = clamp(x)
    return 1 - (1 - x) ** 3


def eio(x):  # ease-in-out
    x = clamp(x)
    return x * x * (3 - 2 * x)


def back(x):  # ease-out con rebote
    x = clamp(x)
    c = 1.9
    return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2


def lerp(a, b, u):
    return a + (b - a) * u


def lerp2(p, q, u):
    return (lerp(p[0], q[0], u), lerp(p[1], q[1], u))


def fade(t, start, d=0.5, end=None, dout=0.5):
    a = eo(prog(t, start, d))
    if end is not None:
        a *= 1 - eio(prog(t, end, dout))
    return a


def along(pts, u):
    """Punto a la fracción u (0..1) de la longitud de una polilínea."""
    segs = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    total = sum(segs)
    d = clamp(u) * total
    for i, s in enumerate(segs):
        if d <= s or i == len(segs) - 1:
            return lerp2(pts[i], pts[i + 1], d / s if s else 0)
        d -= s
    return pts[-1]


def partial(pts, u):
    """Polilínea recortada hasta la fracción u de su longitud."""
    if u <= 0:
        return []
    segs = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    d = clamp(u) * sum(segs)
    out = [pts[0]]
    for i, s in enumerate(segs):
        if d >= s:
            out.append(pts[i + 1])
            d -= s
        else:
            out.append(lerp2(pts[i], pts[i + 1], d / s if s else 0))
            break
    return out


_fonts = {}


def font(size, w="bold"):
    key = (max(1, int(size * S)), w)
    if key not in _fonts:
        for name in FONTS[w]:
            for d in FONT_DIRS:
                if os.path.exists(d + name):
                    _fonts[key] = ImageFont.truetype(d + name, key[0])
                    break
            if key in _fonts:
                break
        else:
            _fonts[key] = ImageFont.load_default(key[0])
    return _fonts[key]


def tlen(txt, size, w="bold"):
    return font(size, w).getlength(txt) / S


def wrap(txt, size, w, maxw):
    lines, cur = [], ""
    for word in txt.split():
        test = (cur + " " + word).strip()
        if tlen(test, size, w) <= maxw or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


class Cv:
    """Lienzo: coordenadas lógicas 1920x1080, dibujado real a S x."""

    def __init__(self, bg):
        self.im = bg.copy()
        self.d = ImageDraw.Draw(self.im, "RGBA")

    @staticmethod
    def c(col, a=1.0):
        base = col[3] / 255 if len(col) > 3 else 1
        return (col[0], col[1], col[2], int(255 * clamp(a) * base))

    def _fo(self, fill, outline, a):
        return (self.c(fill, a) if fill else None, self.c(outline, a) if outline else None)

    def circle(self, x, y, r, fill=None, a=1, outline=None, width=0):
        if r <= 0 or a <= 0.003:
            return
        f, o = self._fo(fill, outline, a)
        self.d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S],
                       fill=f, outline=o, width=int(width * S))

    def ellipse(self, x, y, rx, ry, fill=None, a=1, outline=None, width=0):
        if rx <= 0 or ry <= 0 or a <= 0.003:
            return
        f, o = self._fo(fill, outline, a)
        self.d.ellipse([(x - rx) * S, (y - ry) * S, (x + rx) * S, (y + ry) * S],
                       fill=f, outline=o, width=int(width * S))

    def rrect(self, x0, y0, x1, y1, r, fill=None, a=1, outline=None, width=0):
        if a <= 0.003:
            return
        f, o = self._fo(fill, outline, a)
        self.d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], radius=r * S,
                                 fill=f, outline=o, width=int(width * S))

    def poly(self, pts, fill=None, a=1, outline=None, width=0):
        if a <= 0.003 or len(pts) < 3:
            return
        f, o = self._fo(fill, outline, a)
        self.d.polygon([(x * S, y * S) for x, y in pts], fill=f, outline=o, width=int(width * S))

    def line(self, pts, col, width, a=1, caps=True):
        if a <= 0.003 or len(pts) < 2:
            return
        self.d.line([(x * S, y * S) for x, y in pts], fill=self.c(col, a),
                    width=int(width * S), joint="curve")
        if caps:
            for p in (pts[0], pts[-1]):
                self.circle(p[0], p[1], width / 2 - 0.5, col, a)

    def text(self, x, y, txt, size, col, a=1, w="bold", anchor="mm"):
        if a <= 0.01:
            return
        self.d.text((x * S, y * S), txt, font=font(size, w), fill=self.c(col, a), anchor=anchor)

    def arrow(self, p0, p1, col, width, a=1, head=24):
        ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        base = (p1[0] - math.cos(ang) * head, p1[1] - math.sin(ang) * head)
        self.line([p0, base], col, width, a)
        n = (-math.sin(ang), math.cos(ang))
        self.poly([p1, (base[0] + n[0] * head * 0.6, base[1] + n[1] * head * 0.6),
                   (base[0] - n[0] * head * 0.6, base[1] - n[1] * head * 0.6)], col, a)

    def cover(self, col, a):
        if a > 0.003:
            self.d.rectangle([0, 0, W * S, H * S], fill=self.c(col, a))

    def final(self):
        return self.im.resize((W, H), Image.LANCZOS)


def gradient(top, bot, w=W * S, h=H * S):
    ys = np.linspace(0, 1, h)[:, None]
    col = np.array(top) * (1 - ys) + np.array(bot) * ys
    arr = np.repeat(col[:, None, :], w, axis=1).astype(np.uint8)
    return Image.fromarray(arr, "RGB")


# ---------------------------------------------------------------- piezas de dibujo
def sun(c, x, y, r, t, a=1):
    for k, al in ((2.4, 0.07), (1.9, 0.10), (1.5, 0.16)):
        c.circle(x, y, r * k, SUN_LIGHT, al * a)
    for k in range(12):
        ang = math.radians(k * 30 + t * 18)
        tip = (x + math.cos(ang) * r * 1.6, y + math.sin(ang) * r * 1.6)
        b1 = (x + math.cos(ang - 0.13) * r * 1.12, y + math.sin(ang - 0.13) * r * 1.12)
        b2 = (x + math.cos(ang + 0.13) * r * 1.12, y + math.sin(ang + 0.13) * r * 1.12)
        c.poly([tip, b1, b2], SUN, a)
    c.circle(x, y, r, SUN, a)
    c.circle(x - r * 0.12, y - r * 0.12, r * 0.72, SUN_LIGHT, a)


def drop(c, x, y, r, a=1, col=WATER):
    c.poly([(x, y - r * 2.1), (x - r * 0.87, y - r * 0.5), (x + r * 0.87, y - r * 0.5)], col, a)
    c.circle(x, y, r, col, a)
    c.circle(x - r * 0.35, y - r * 0.3, r * 0.28, WHITE, a * 0.7)


def co2(c, x, y, sc=1, a=1, label=False):
    c.circle(x - 30 * sc, y, 15 * sc, OXY, a, outline=(170, 40, 40), width=2 * sc)
    c.circle(x + 30 * sc, y, 15 * sc, OXY, a, outline=(170, 40, 40), width=2 * sc)
    c.circle(x, y, 17 * sc, CARBON, a, outline=(40, 40, 50), width=2 * sc)
    if label:
        c.text(x, y + 34 * sc, "CO₂", 20 * sc, DARK, a)


def h2o(c, x, y, sc=1, a=1, label=False):
    for s in (-1, 1):
        c.circle(x + s * 24 * sc, y + 17 * sc, 13 * sc, HYD, a, outline=(150, 150, 165), width=2 * sc)
    c.circle(x, y, 22 * sc, OXY, a, outline=(170, 40, 40), width=2 * sc)
    if label:
        c.text(x, y + 50 * sc, "H₂O", 20 * sc, DARK, a)


def o2(c, x, y, sc=1, a=1, label=False):
    c.circle(x - 13 * sc, y, 16 * sc, OXY, a, outline=(170, 40, 40), width=2 * sc)
    c.circle(x + 13 * sc, y, 16 * sc, OXY, a, outline=(170, 40, 40), width=2 * sc)
    c.circle(x - 18 * sc, y - 6 * sc, 4 * sc, WHITE, a * 0.6)
    if label:
        c.text(x, y + 32 * sc, "O₂", 20 * sc, DARK, a)


def glucose(c, x, y, r, a=1, label=False):
    pts = [(x + r * math.cos(math.radians(60 * k + 30)), y + r * math.sin(math.radians(60 * k + 30)))
           for k in range(6)]
    c.poly(pts, GLU, a, outline=GLU_DARK, width=max(2, r * 0.08))
    c.circle(x, y, r * 0.32, (255, 215, 120), a)
    if label:
        c.text(x, y + r + 22, "Glucosa", 22, DARK, a)


def energy(c, x, y, name, a=1, sc=1):
    if sc < 0.05:
        return
    r = (34 if name == "NADPH" else 30) * sc
    col = (255, 205, 50) if name == "ATP" else (255, 150, 60)
    c.circle(x, y, r * 1.45, col, a * 0.25)
    c.circle(x, y, r, col, a, outline=(200, 110, 20), width=3)
    c.text(x, y + 1, name, (21 if name == "ATP" else 16) * sc, DARK, a)


def pill(c, x, y, txt, col, a=1, center=False, size=38):
    if a <= 0.01:
        return
    w = tlen(txt, size) + 64
    x0 = x - w / 2 if center else x
    off = (1 - eo(a)) * -30
    c.rrect(x0 + off, y - 38, x0 + w + off, y + 38, 38, col, a)
    c.text(x0 + w / 2 + off, y + 1, txt, size, WHITE, a)


def caption(c, t, items):
    """items: lista de (inicio, fin, texto). Barra inferior con subtítulos."""
    first, last = items[0][0], items[-1][1]
    bar_a = fade(t, first, 0.4, last - 0.4, 0.4)
    if bar_a <= 0.01:
        return
    act = [it for it in items if it[0] - 0.01 <= t <= it[1]]
    nlines = max([len(wrap(it[2], 36, "semi", 1560)) for it in act] or [1])
    h = 46 * nlines + 40
    c.rrect(120, 1012 - h / 2, 1800, 1012 + h / 2, 26, (18, 32, 30), bar_a * 0.82)
    for s, e, txt in act:
        a = fade(t, s, 0.35, e - 0.3, 0.3) * bar_a
        lines = wrap(txt, 36, "semi", 1560)
        y0 = 1012 - (len(lines) - 1) * 23
        for i, ln in enumerate(lines):
            c.text(960, y0 + i * 46, ln, 36, WHITE, a, "semi")


def label_box(c, x, y, title, sub, px, py, a, col=DARK):
    """Etiqueta blanca anclada a la izquierda en (x, y) con línea hasta (px, py)."""
    if a <= 0.01:
        return
    w = max(tlen(title, 32), tlen(sub, 22, "reg") if sub else 0) + 40
    h = 76 if sub else 58
    c.line([(x, y), (px, py)], WHITE, 5, a)
    c.line([(x, y), (px, py)], col, 2.5, a)
    c.circle(px, py, 9, WHITE, a)
    c.circle(px, py, 6, col, a)
    c.rrect(x, y - h / 2, x + w, y + h / 2, 16, WHITE, a * 0.95, outline=col, width=3)
    if sub:
        c.text(x + 20, y - 13, title, 32, col, a, anchor="lm")
        c.text(x + 20, y + 20, sub, 22, GREY, a, "reg", anchor="lm")
    else:
        c.text(x + 20, y + 1, title, 32, col, a, anchor="lm")


def card(c, y0, icon, title, sub, a, active, accent):
    if a <= 0.01:
        return
    x0 = 1240 + (1 - eo(a)) * 80
    c.rrect(x0 + 6, y0 + 8, x0 + 606, y0 + 138, 24, (0, 0, 0), a * 0.12)
    c.rrect(x0, y0, x0 + 600, y0 + 130, 24, WHITE, a * 0.94,
            outline=accent if active else (215, 225, 220), width=6 if active else 3)
    c.circle(x0 + 70, y0 + 65, 46, accent, a * 0.18)
    icon(c, x0 + 70, y0 + 65, a)
    c.text(x0 + 138, y0 + 47, title, 34, DARK, a, anchor="lm")
    c.text(x0 + 138, y0 + 91, sub, 25, GREY, a, "reg", anchor="lm")


# ---------------------------------------------------------------- la planta
PX, GY = 560, 760
STEM_H = 400
#          (altura en tallo, lado, ángulo, largo)
LEAVES = [(0.28, -1, 22, 195), (0.44, 1, 26, 205), (0.60, -1, 32, 185),
          (0.75, 1, 38, 170), (0.88, -1, 48, 140), (0.95, 1, 58, 115)]
ROOTS = [[(0, 0), (5, 60), (-6, 120), (3, 175)],
         [(3, 35), (-45, 75), (-95, 125)],
         [(3, 50), (55, 95), (105, 140)],
         [(-5, 110), (-48, 150)],
         [(-3, 125), (42, 168)]]
ROOTS = [[(PX + x, GY + y) for x, y in r] for r in ROOTS]


def stem_pt(f, h=STEM_H):
    return (PX + 16 * math.sin(math.pi * f * 1.1), GY - h * f)


def leaf_geom(i, h=STEM_H):
    f, side, ang, L = LEAVES[i]
    b = stem_pt(f, h)
    a = math.radians(ang)
    return b, (side * math.cos(a), -math.sin(a)), L


def leaf_pt(i, u, h=STEM_H, sc=1):
    b, v, L = leaf_geom(i, h)
    return (b[0] + v[0] * L * sc * u, b[1] + v[1] * L * sc * u)


def draw_leaf(c, b, v, L, a=1):
    n = (-v[1], v[0])
    w = L * 0.3
    s1, s2 = [], []
    for k in range(25):
        u = k / 24
        s = math.sin(math.pi * u) ** 0.8 * w * (1 - 0.3 * u)
        bend = L * 0.06 * math.sin(math.pi * u * 0.9)  # ligera curvatura
        px, py = b[0] + v[0] * L * u + n[0] * bend, b[1] + v[1] * L * u + n[1] * bend
        s1.append((px + n[0] * s, py + n[1] * s))
        s2.append((px - n[0] * s, py - n[1] * s))
    c.poly(s1 + s2[::-1], LEAF, a, outline=LEAF_DARK, width=3)
    mid = [(b[0] + v[0] * L * u + n[0] * L * 0.06 * math.sin(math.pi * u * 0.9),
            b[1] + v[1] * L * u + n[1] * L * 0.06 * math.sin(math.pi * u * 0.9))
           for u in np.linspace(0, 0.9, 8)]
    c.line(mid, LEAF_DARK, 4, a)


def flower(c, x, y, r, a=1):
    for k in range(6):
        ang = math.radians(k * 60)
        c.circle(x + math.cos(ang) * r * 0.75, y + math.sin(ang) * r * 0.75, r * 0.55,
                 (245, 120, 160), a, outline=(210, 80, 120), width=2)
    c.circle(x, y, r * 0.45, (255, 210, 60), a, outline=(220, 160, 30), width=2)


def draw_plant(c, grow=1.0, roots=0.0, h=STEM_H, bloom=0.0, a=1):
    for k, r in enumerate(ROOTS):
        u = prog(roots, 0 if k == 0 else 0.3 + k * 0.08, 0.5 if k else 0.6)
        pts = partial(r, u)
        if len(pts) > 1:
            c.line(pts, ROOT, 9 if k == 0 else 6, a)
    stem = [stem_pt(f, h) for f in np.linspace(0, grow, 30)]
    if grow > 0.01:
        c.line(stem, STEM, 18, a)
        c.line(stem, (110, 180, 85), 6, a * 0.7)
    for i, (f, side, ang, L) in enumerate(LEAVES):
        g = back(prog(grow, f - 0.08, 0.28))
        if g > 0.01:
            b, v, _ = leaf_geom(i, h)
            draw_leaf(c, b, v, L * g, a)
    if grow > 0.98:
        top = stem_pt(1, h)
        if bloom > 0.01:
            flower(c, top[0], top[1] - 10, 38 * back(bloom), a)
        else:
            c.ellipse(top[0], top[1] - 6, 12, 18, (90, 165, 70), a, outline=LEAF_DARK, width=3)


def landscape():
    c = Cv(gradient(SKY_TOP, SKY_BOT))
    for col, base, amp, freq, ph in ((HILL1, 650, 60, 0.0028, 0.5), (HILL2, 700, 45, 0.004, 2.0)):
        pts = [(x, base - amp * math.sin(x * freq + ph) - amp * 0.4 * math.sin(x * freq * 2.7))
               for x in range(0, W + 41, 40)]
        c.poly(pts + [(W, H), (0, H)], col)
    soil = gradient(SOIL_TOP, SOIL_BOT, W * S, (H - GY) * S)
    c.im.paste(soil, (0, GY * S))
    c.rrect(-20, GY - 18, W + 20, GY + 14, 14, GRASS)
    rnd = random.Random(3)
    for _ in range(90):  # piedrecitas
        x, y = rnd.uniform(0, W), rnd.uniform(GY + 30, H)
        c.ellipse(x, y, rnd.uniform(4, 10), rnd.uniform(3, 7), (150, 112, 80), 0.6)
    for x in range(0, W, 14):  # hierba
        hh = 10 + 8 * math.sin(x * 0.37) ** 2
        c.line([(x, GY - 10), (x + 4, GY - 10 - hh)], (85, 160, 65), 4)
    return c.im


# ---------------------------------------------------------------- fondos (cacheados por proceso)
_bg = {}


def bg(name):
    if name not in _bg:
        if name == "land":
            _bg[name] = landscape()
        elif name == "chloro":
            _bg[name] = gradient((232, 244, 222), (200, 226, 190))
        elif name == "eq":
            _bg[name] = gradient((252, 249, 238), (232, 242, 222))
        elif name == "tissue":
            _bg[name] = make_tissue()
    return _bg[name]


def make_tissue():
    """Tejido de la hoja: células con cloroplastos (para el zoom)."""
    rnd = random.Random(7)
    c = Cv(Image.new("RGB", (W * S, H * S), (115, 172, 88)))
    cells, chloros = [], []
    for row in range(-1, 7):
        for col in range(-1, 9):
            x = col * 270 + (135 if row % 2 else 0) - 60 + rnd.uniform(-8, 8)
            y = row * 200 - 40 + rnd.uniform(-8, 8)
            box = (x + 8, y + 8, x + 262, y + 192)
            cells.append(box)
            c.rrect(*box, 46, (176, 222, 142), outline=(78, 138, 60), width=8)
            c.rrect(box[0] + 40, box[1] + 38, box[2] - 40, box[3] - 38, 34, (206, 238, 182))
            per = 2 * ((box[2] - box[0] - 60) + (box[3] - box[1] - 60))
            n = rnd.randint(7, 9)
            for k in range(n):
                d = (k + rnd.uniform(0, 0.6)) / n * per
                bw, bh = box[2] - box[0] - 60, box[3] - box[1] - 60
                x0, y0 = box[0] + 30, box[1] + 30
                if d < bw:
                    p, horiz = (x0 + d, y0), True
                elif d < bw + bh:
                    p, horiz = (x0 + bw, y0 + d - bw), False
                elif d < 2 * bw + bh:
                    p, horiz = (x0 + bw - (d - bw - bh), y0 + bh), True
                else:
                    p, horiz = (x0, y0 + bh - (d - 2 * bw - bh)), False
                rx, ry = (27, 15) if horiz else (15, 27)
                c.ellipse(p[0], p[1], rx, ry, (48, 140, 55), outline=(28, 92, 40), width=3)
                for j in (-1, 0, 1):
                    if horiz:
                        c.line([(p[0] + j * 10, p[1] - 6), (p[0] + j * 10, p[1] + 6)], (100, 190, 95), 3, caps=False)
                    else:
                        c.line([(p[0] - 6, p[1] + j * 10), (p[0] + 6, p[1] + j * 10)], (100, 190, 95), 3, caps=False)
                chloros.append(p)
    make_tissue.cells, make_tissue.chloros = cells, chloros
    return c.im


def hero():
    """Célula y cloroplasto protagonistas del zoom."""
    bg("tissue")
    cell = min(make_tissue.cells, key=lambda b: math.dist(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2), (900, 560)))
    inside = [p for p in make_tissue.chloros if cell[0] < p[0] < cell[2] and cell[1] < p[1] < cell[3]]
    chl = min(inside, key=lambda p: math.dist(p, (cell[2], cell[1])))
    return cell, chl


# ---------------------------------------------------------------- cloroplasto
CX, CY, RX, RY = 820, 540, 560, 290
GRANA = [(430, 500), (580, 625), (720, 455), (860, 600)]
CALVIN = (1130, 540)
SLOTS = [(975, 370), (975, 455), (985, 640), (975, 725)]


def chloroplast(c, t, a=1, grana_in=1.0, shimmer=0.0, glow=None):
    c.ellipse(CX + 10, CY + 16, RX, RY, (0, 0, 0), a * 0.10)
    c.ellipse(CX, CY, RX, RY, (105, 178, 78), a, outline=(55, 115, 42), width=10)
    c.ellipse(CX, CY, RX - 24, RY - 24, (186, 226, 142), a, outline=(88, 158, 68), width=4)
    rnd = random.Random(11)
    for _ in range(40):  # ribosomas y gránulos en el estroma
        ang, rr = rnd.uniform(0, 2 * math.pi), math.sqrt(rnd.uniform(0, 1)) * 0.85
        c.circle(CX + math.cos(ang) * (RX - 40) * rr, CY + math.sin(ang) * (RY - 40) * rr,
                 rnd.uniform(3, 6), (120, 170, 95), a)
    lam = [(330, 520)] + GRANA + [(990, 560)]
    c.line(partial(lam, grana_in), (62, 145, 62), 10, a)
    for i, (gx, gy) in enumerate(GRANA):
        g = eo(prog(grana_in, i * 0.18, 0.35))
        if g <= 0.01:
            continue
        if glow == i:
            c.circle(gx, gy, 115, (255, 235, 120), a * 0.35)
        for k in range(5):
            y = gy + (k - 2) * 26 + (1 - g) * 40
            c.rrect(gx - 65, y - 11, gx + 65, y + 11, 11, (45, 135, 60), a * g, outline=(25, 85, 40), width=3)
            c.line([(gx - 45, y - 5), (gx + 45, y - 5)], (95, 185, 95), 3, a * g)
            if shimmer > 0:
                s = 0.5 + 0.5 * math.sin(t * 6 + i * 1.3 + k * 0.7)
                c.rrect(gx - 65, y - 11, gx + 65, y + 11, 11, (255, 245, 130), a * g * shimmer * 0.45 * s)


def photon(c, p0, p1, t, a=1, n=3, speed=0.8):
    """Ondas de luz que viajan de p0 a p1."""
    D = math.dist(p0, p1)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    ux, uy, nx, ny = math.cos(ang), math.sin(ang), -math.sin(ang), math.cos(ang)
    c.line([p0, p1], (255, 225, 90), 3, a * 0.35)
    for k in range(n):
        s = ((t * speed + k / n) % 1) * D
        pts = []
        for d in np.linspace(s - 80, s + 80, 34):
            if 0 <= d <= D:
                w = 11 * math.sin(d / 14)
                pts.append((p0[0] + ux * d + nx * w, p0[1] + uy * d + ny * w))
        if len(pts) > 1:
            c.line(pts, (255, 200, 30), 6, a)


def calvin(c, t, a=1):
    x, y, r = CALVIN[0], CALVIN[1], 130
    c.circle(x, y, r + 30, (255, 240, 200), a * 0.55)
    c.circle(x, y, r, None, a * 0.5, outline=WHITE, width=4)
    rot = t * 70
    for k in range(3):
        s = rot + k * 120
        e = s + 88
        c.d.arc([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], s, e,
                fill=c.c(ORANGE, a), width=14 * S)
        th = math.radians(e)
        p = (x + r * math.cos(th), y + r * math.sin(th))
        tg = (-math.sin(th), math.cos(th))
        nm = (math.cos(th), math.sin(th))
        c.poly([(p[0] + tg[0] * 28, p[1] + tg[1] * 28),
                (p[0] + nm[0] * 20, p[1] + nm[1] * 20),
                (p[0] - nm[0] * 20, p[1] - nm[1] * 20)], ORANGE, a)
    c.text(x, y - 18, "Ciclo de", 28, (170, 85, 15), a)
    c.text(x, y + 18, "Calvin", 34, (170, 85, 15), a)


# ---------------------------------------------------------------- escenas
# Cada escena recibe el lienzo, el tiempo local t y su duración d.

def sc_intro(c, t, d):
    sy = lerp(900, 190, eo(prog(t, 0.0, 2.6)))
    sun(c, 1700, sy, 80, t)
    draw_plant(c, grow=eio(prog(t, 0.6, 3.2)), roots=0)
    a = fade(t, 1.6, 0.8, d - 0.8, 0.6)
    oy = (1 - eo(prog(t, 1.6, 0.8))) * 40
    c.text(1310, 370 + oy, "¿Cómo funciona la", 64, DARK, a)
    a2 = fade(t, 2.1, 0.8, d - 0.8, 0.6)
    oy2 = (1 - eo(prog(t, 2.1, 0.8))) * 40
    c.text(1314, 476 + oy2, "FOTOSÍNTESIS?", 132, (20, 70, 30), a2 * 0.25, "xb")
    c.text(1310, 470 + oy2, "FOTOSÍNTESIS?", 132, (45, 150, 60), a2, "xb")
    c.text(1310, 580, "Así fabrican las plantas su propio alimento", 36, GREY,
           fade(t, 3.0, 0.8, d - 0.8, 0.6), "semi")


SUN_POS = (1000, 160)


def sc_ingredients(c, t, d):
    sun(c, SUN_POS[0], SUN_POS[1] + (1 - eo(prog(t, 0, 1.2))) * -0 + 0, 62, t,
        a=1)
    draw_plant(c, grow=1, roots=eo(prog(t, 7.0, 1.6)))
    pill(c, 80, 75, "Los 3 ingredientes", (45, 140, 60), fade(t, 0.3, 0.6, d - 0.6, 0.5))

    # 1. Luz
    la = fade(t, 1.3, 0.6) * (1 - 0.55 * prog(t, 7.0, 0.8))
    for i in (0, 1, 2, 3, 4):
        photon(c, (SUN_POS[0] - 40, SUN_POS[1] + 45), leaf_pt(i, 0.6), t + i * 0.37, la, n=2, speed=0.55)
    for i in (0, 1, 2, 3, 4):
        p = leaf_pt(i, 0.6)
        c.circle(p[0], p[1], 20 + 6 * math.sin(t * 5 + i), (255, 240, 120), la * 0.45)

    # 2. Agua: gotas de la tierra a las hojas
    if t > 6.5:
        ra = fade(t, 7.0, 0.6)
        rnd = random.Random(5)
        for _ in range(16):
            x, y = rnd.uniform(300, 820), rnd.uniform(GY + 40, 930)
            drop(c, x, y, 7, ra * (0.55 + 0.35 * math.sin(t * 2 + x)))
        for k in range(10):
            t0 = 8.4 + k * 0.6
            u = prog(t, t0, 2.6)
            if 0 < u < 1:
                rt = ROOTS[1 + k % 4]
                li = [0, 1, 2, 3, 4, 5][k % 6]
                fl = LEAVES[li][0]
                path = rt[::-1] + [(PX + 2, GY + 30), (PX, GY)] + \
                    [stem_pt(f) for f in np.linspace(0, fl, 8)] + \
                    [leaf_pt(li, uu) for uu in (0.2, 0.5, 0.75)]
                p = along(path, eio(u))
                drop(c, p[0], p[1], 10, (1 - prog(u, 0.85, 0.15)))

    # 3. CO2: entra por los estomas
    if t > 14.0:
        ia = fade(t, 14.6, 0.6, d - 0.7, 0.5)
        ins = (1010, 510)
        anchor = leaf_pt(3, 0.62)
        c.line([anchor, (ins[0] - 150, ins[1] + 20)], WHITE, 4, ia)
        c.circle(anchor[0], anchor[1], 10, WHITE, ia)
        c.circle(ins[0], ins[1], 156, WHITE, ia)
        c.circle(ins[0], ins[1], 148, (120, 192, 95), ia)
        for x in (-110, 110):  # células de la epidermis
            c.rrect(ins[0] + x - 50, ins[1] - 120, ins[0] + x + 50, ins[1] + 120, 30, (140, 205, 112), ia,
                    outline=(85, 150, 65), width=4)
        op = 14 + 6 * math.sin(t * 2)
        for s in (-1, 1):
            c.ellipse(ins[0] + s * (op + 30), ins[1], 32, 92, (70, 150, 58), ia, outline=(35, 100, 40), width=4)
        c.ellipse(ins[0], ins[1], op, 62, (35, 70, 40), ia)
        c.text(ins[0], ins[1] + 186, "Estoma (poro de la hoja)", 26, DARK, ia)
        for k in range(8):
            t0 = 15.0 + k * 0.75
            u = prog(t, t0, 2.2)
            if 0 < u < 1:
                st = (ins[0] + (110 if k % 2 else -110), ins[1] - 140)
                p = lerp2(st, ins, eio(u))
                sc = lerp(0.9, 0.35, eio(u))
                co2(c, p[0] + math.sin(u * 7 + k) * 12 * (1 - u), p[1], sc, ia * (1 - prog(u, 0.8, 0.2)))
        for k in range(7):  # moléculas en el aire hacia las hojas
            t0 = 14.6 + k * 0.85
            u = prog(t, t0, 3.0)
            if 0 < u < 1:
                st = (720 + (k * 97) % 260, 120 + (k * 53) % 140)
                tg = leaf_pt(k % 6, 0.55)
                p = lerp2(st, tg, eio(u))
                co2(c, p[0] + math.sin(u * 9 + k) * 18, p[1], 0.75, ia * (1 - prog(u, 0.85, 0.15)), label=True)

    card(c, 200, lambda c, x, y, a: sun(c, x, y, 22, t, a), "Luz solar", "Aporta la energía",
         fade(t, 1.0, 0.6, d - 0.6, 0.5), 1.0 <= t < 7.0, (240, 170, 20))
    card(c, 360, lambda c, x, y, a: drop(c, x, y + 10, 18, a), "Agua (H₂O)", "La absorben las raíces",
         fade(t, 7.0, 0.6, d - 0.6, 0.5), 7.0 <= t < 14.0, WATER)
    card(c, 520, lambda c, x, y, a: co2(c, x, y, 0.95, a), "Dióxido de carbono", "CO₂ del aire, entra por las hojas",
         fade(t, 14.0, 0.6, d - 0.6, 0.5), 14.0 <= t < d, (110, 115, 125))
    caption(c, t, [
        (1.0, 7.0, "Las hojas verdes capturan la energía de la luz del sol."),
        (7.0, 14.0, "Las raíces absorben agua del suelo y la suben por el tallo hasta las hojas."),
        (14.0, d - 0.2, "El dióxido de carbono (CO₂) del aire entra en las hojas por unos poros diminutos: los estomas."),
    ])


def sc_zoom(c, t, d):
    cell, chl = hero()
    sun(c, SUN_POS[0], SUN_POS[1], 62, t + 22)
    draw_plant(c, grow=1, roots=1)
    target = leaf_pt(2, 0.55)
    R = eio(prog(t, 0.2, 1.6)) * 2400
    tissue = bg("tissue")
    if R > 0:
        mask = Image.new("L", c.im.size, 0)
        ImageDraw.Draw(mask).ellipse([(target[0] - R) * S, (target[1] - R) * S,
                                      (target[0] + R) * S, (target[1] + R) * S], fill=255)
        c.im.paste(tissue, (0, 0), mask)
        if R < 2300:
            c.circle(target[0], target[1], R, None, 1, outline=WHITE, width=10)
    z = 1 + 7 * eio(prog(t, d - 1.6, 1.6)) ** 2
    if z > 1.001:  # zoom final hacia el cloroplasto
        cw, ch = W * S / z, H * S / z
        fx = lerp(W / 2, chl[0], eio(prog(t, d - 1.6, 0.6))) * S
        fy = lerp(H / 2, chl[1], eio(prog(t, d - 1.6, 0.6))) * S
        x0 = clamp(fx - cw / 2, 0, W * S - cw)
        y0 = clamp(fy - ch / 2, 0, H * S - ch)
        c.im.paste(tissue.resize(c.im.size, Image.BILINEAR, box=(x0, y0, x0 + cw, y0 + ch)))
    la = fade(t, 2.2, 0.5, d - 1.9, 0.4)
    pill(c, 960, 75, "Dentro de la hoja", (45, 140, 60), la, center=True)
    pa = fade(t, 2.8, 0.5, d - 1.9, 0.4)
    pulse = 0.5 + 0.5 * math.sin(t * 5)
    c.rrect(*cell, 46, None, pa * (0.6 + 0.4 * pulse), outline=(255, 225, 60), width=8)
    label_box(c, 250, 230, "Célula", "la unidad de la vida", cell[0] + 30, cell[1] + 20, pa)
    pb = fade(t, 4.0, 0.5, d - 1.9, 0.4)
    c.circle(chl[0], chl[1], 38 + 6 * pulse, None, pb, outline=(255, 225, 60), width=7)
    label_box(c, 1420, 230, "Cloroplasto", "aquí ocurre la fotosíntesis", chl[0] + 30, chl[1] - 26, pb)
    caption(c, t, [(2.2, d - 1.7, "Las hojas están formadas por células llenas de cloroplastos: "
                                   "las «fábricas» de la fotosíntesis.")])


def sc_chloro(c, t, d):
    chloroplast(c, t, a=fade(t, 0, 0.6), grana_in=prog(t, 0.6, 1.8), shimmer=prog(t, 2.5, 1.0) * (1 - prog(t, d - 1, 1)))
    pill(c, 960, 75, "El cloroplasto", (45, 140, 60), fade(t, 0.3, 0.6), center=True)
    la = lambda s: fade(t, s, 0.5, d - 0.7, 0.5)
    label_box(c, 1470, 330, "Membrana", "la envoltura", 1340, 432, la(2.4))
    label_box(c, 1470, 540, "Tilacoides", "contienen clorofila", 860, 600, la(3.2))
    label_box(c, 1470, 750, "Estroma", "el líquido interior", 1100, 700, la(4.0))
    caption(c, t, [
        (0.8, 5.0, "Los tilacoides tienen clorofila: el pigmento verde que captura la luz del sol."),
        (5.0, d, "La fotosíntesis ocurre en dos fases: la fase luminosa y el ciclo de Calvin."),
    ])


def water_split(c, t, t0, slot_ids):
    g = GRANA[0]
    u = prog(t, t0, 1.8)
    if 0 < u < 1 or (t0 + 1.8 <= t < t0 + 2.1):
        p = lerp2((40, 830), (g[0] - 20, g[1] + 40), eio(u))
        h2o(c, p[0], p[1], 1.3, 1, label=True)
    ts = t0 + 2.1
    f = prog(t, ts, 0.5)
    if 0 < f < 1:
        c.circle(g[0] - 20, g[1] + 40, 30 + 120 * eo(f), (255, 250, 180), 0.8 * (1 - f))
    ou = prog(t, ts, 2.4)
    if 0 < ou < 1:
        p = lerp2((g[0] - 20, g[1] + 20), (g[0] - 150, 150), eio(ou))
        oa = 1 - prog(ou, 0.85, 0.15)
        o2(c, p[0], p[1], 1.4, oa)
        c.text(p[0] + 60, p[1], "O₂", 30, OXY, oa, anchor="lm")
    for j, (name, sid) in enumerate(zip(("ATP", "NADPH"), slot_ids)):
        eu = prog(t, ts + 0.2 + j * 0.35, 2.0)
        if eu > 0:
            p = lerp2((g[0] + 10, g[1] + 30), SLOTS[sid], eio(eu))
            energy(c, p[0], p[1], name, 1, back(min(1, eu * 3)))


def sc_phase1(c, t, d):
    chloroplast(c, t, glow=0, shimmer=0.6)
    pill(c, 960, 75, "Fase 1 · Fase luminosa", (225, 150, 20), fade(t, 0.2, 0.6), center=True)
    sun(c, 110, 140, 52, t)
    la = fade(t, 0.6, 0.6)
    photon(c, (160, 190), (GRANA[0][0] - 30, GRANA[0][1] - 50), t, la)
    photon(c, (170, 160), (GRANA[2][0] - 40, GRANA[2][1] - 50), t + 0.3, la)
    water_split(c, t, 1.4, (0, 1))
    water_split(c, t, 5.4, (2, 3))
    caption(c, t, [
        (0.4, 5.6, "La luz llega a la clorofila y aporta la energía para romper las moléculas de agua (H₂O)."),
        (5.6, d, "Así se libera oxígeno (O₂) y se fabrican moléculas de energía: ATP y NADPH."),
    ])


def sc_phase2(c, t, d):
    chloroplast(c, t)
    sun(c, 110, 140, 52, t + 11, a=1 - prog(t, 0, 0.8))
    pill(c, 960, 75, "Fase 2 · Ciclo de Calvin", ORANGE, fade(t, 0.2, 0.6), center=True)
    calvin(c, t, fade(t, 0.3, 0.8))
    for k, (name, sid) in enumerate(zip(("ATP", "NADPH", "ATP", "NADPH"), range(4))):
        u = prog(t, 2.6 + k * 0.4, 1.4)
        if u < 1:
            p = lerp2(SLOTS[sid], CALVIN, eio(u))
            energy(c, p[0], p[1], name, 1 - prog(u, 0.7, 0.3), 1 - 0.5 * u)
    for k in range(3):
        u = prog(t, 0.9 + k * 0.6, 2.2)
        if 0 < u < 1:
            p = lerp2((1260 + k * 90, 110), (CALVIN[0] + (k - 1) * 50, CALVIN[1] - 60), eio(u))
            co2(c, p[0], p[1], 1.2, 1 - prog(u, 0.8, 0.2), label=True)
    gu = eo(prog(t, 5.6, 2.2))
    if gu > 0:
        p = lerp2(CALVIN, (1530, 830), gu)
        glucose(c, p[0], p[1], lerp(14, 52, gu), 1)
        ga = fade(t, 7.2, 0.5)
        c.text(1600, 808, "Glucosa", 40, DARK, ga, anchor="lm")
        c.text(1600, 852, "C₆H₁₂O₆", 30, GLU_DARK, ga, "semi", anchor="lm")
    caption(c, t, [
        (0.3, 5.6, "En el estroma, la energía (ATP y NADPH) se usa para atrapar el CO₂ que entró por las hojas."),
        (5.6, d, "Con él se fabrica glucosa: un azúcar que es el alimento de la planta."),
    ])


def rising_o2(c, t, a, n=14, seed=2):
    for k in range(n):
        per = 3.2
        ph = (t + k * per / n) % per / per
        li = k % 6
        st = leaf_pt(li, 0.7)
        x = st[0] + math.sin(ph * 6 + k) * 22 + (k % 3 - 1) * 30
        y = st[1] - ph * 380
        o2(c, x, y, 0.75, a * (1 - prog(ph, 0.7, 0.3)) * prog(ph, 0, 0.1))


def sc_products(c, t, d):
    sun(c, SUN_POS[0], SUN_POS[1], 62, t)
    hgt = STEM_H * (1 + 0.1 * eio(prog(t, 5.0, 2.0)))
    # durante el crecimiento las hojas acompañan al tallo
    draw_plant(c, grow=1, roots=1, h=hgt, bloom=prog(t, 6.2, 1.2))
    pill(c, 80, 75, "Los resultados", (45, 140, 60), fade(t, 0.2, 0.6, d - 0.6, 0.5))
    rising_o2(c, t, fade(t, 0.8, 0.8, d - 0.8, 0.6))
    if t > 4.6:  # la glucosa viaja por la planta
        for k in range(8):
            u = prog(t, 4.8 + k * 0.45, 2.0)
            if 0 < u < 1:
                li = k % 6
                path = [leaf_pt(li, 0.6, hgt), leaf_pt(li, 0.1, hgt)] + \
                    ([stem_pt(f, hgt) for f in np.linspace(LEAVES[li][0], 1, 5)] if k % 2 else
                     [stem_pt(f, hgt) for f in np.linspace(LEAVES[li][0], 0, 5)] + [ROOTS[0][2]])
                p = along(path, eio(u))
                glucose(c, p[0], p[1], 11, 1 - prog(u, 0.85, 0.15))
    card(c, 220, lambda c, x, y, a: o2(c, x, y, 1.1, a), "Oxígeno (O₂)", "Sale al aire: ¡lo respiramos!",
         fade(t, 0.8, 0.6, d - 0.6, 0.5), t < 4.8, OXY)
    card(c, 380, lambda c, x, y, a: glucose(c, x, y, 30, a), "Glucosa", "Alimento y energía para la planta",
         fade(t, 4.8, 0.6, d - 0.6, 0.5), t >= 4.8, GLU)
    caption(c, t, [
        (0.6, 4.8, "El oxígeno sale de las hojas al aire: es el que respiramos las personas y los animales."),
        (4.8, d, "La glucosa recorre la planta y le da energía para crecer, florecer y dar frutos."),
    ])


EQ = [("6 CO₂", CARBON, "Dióxido de carbono", "co2"), ("+", GREY, None, None),
      ("6 H₂O", WATER, "Agua", "h2o"), ("+", GREY, None, None),
      ("Luz", (225, 150, 20), "Energía solar", "sun"), ("→", GREEN_TXT, None, None),
      ("C₆H₁₂O₆", GLU_DARK, "Glucosa", "glu"), ("+", GREY, None, None),
      ("6 O₂", OXY, "Oxígeno", "o2")]


def sc_equation(c, t, d):
    c.text(960, 150, "La ecuación de la fotosíntesis", 58, DARK, fade(t, 0.2, 0.6), "xb")
    size, gap = 84, 34
    widths = [tlen(s, size, "xb") for s, *_ in EQ]
    total = sum(widths) + gap * (len(EQ) - 1)
    x = (W - total) / 2
    centers = []
    for i, ((txt, col, desc, icon), w) in enumerate(zip(EQ, widths)):
        cx = x + w / 2
        centers.append((x, x + w))
        a = fade(t, 0.8 + i * 0.42, 0.5)
        oy = (1 - eo(a)) * 40
        c.text(cx, 470 + oy, txt, size, col, a, "xb")
        ia = fade(t, 1.0 + i * 0.42, 0.5)
        if icon == "co2":
            co2(c, cx, 335, 1.5, ia)
        elif icon == "h2o":
            h2o(c, cx, 325, 1.4, ia)
        elif icon == "sun":
            sun(c, cx, 330, 34, t, ia)
        elif icon == "glu":
            glucose(c, cx, 330, 46, ia)
        elif icon == "o2":
            o2(c, cx, 335, 1.6, ia)
        if desc:
            c.text(cx, 560, desc, 28, GREY, ia, "semi")
        if txt == "→":
            c.text(cx, 405, "clorofila", 24, GREEN_TXT, ia, "semi")
        x += w + gap
    for (i0, i1, txt, col, s) in ((0, 4, "Lo que entra", WATER, 5.2), (6, 8, "Lo que sale", GLU_DARK, 5.8)):
        a = fade(t, s, 0.5)
        u = eo(prog(t, s, 0.7))
        x0, x1 = centers[i0][0] - 10, centers[i1][1] + 10
        xm = (x0 + x1) / 2
        c.line([(xm - (xm - x0) * u, 640), (xm + (x1 - xm) * u, 640)], col, 6, a)
        c.line([(x0, 640), (x0, 620)], col, 6, a * u)
        c.line([(x1, 640), (x1, 620)], col, 6, a * u)
        c.text(xm, 690, txt, 34, col, a)
    caption(c, t, [(1.0, d, "Con la energía de la luz, 6 moléculas de CO₂ y 6 de agua se transforman "
                            "en 1 de glucosa y 6 de oxígeno.")])


def sc_outro(c, t, d):
    sun(c, 1700, 170, 75, t)
    draw_plant(c, grow=1, roots=1, h=STEM_H * 1.1, bloom=1)
    rising_o2(c, t, fade(t, 0, 0.8))
    a = fade(t, 0.5, 0.8)
    oy = (1 - eo(a)) * 40
    c.text(1240, 360 + oy, "¡Gracias a la fotosíntesis", 66, (25, 80, 35), a, "xb")
    a2 = fade(t, 0.9, 0.8)
    c.text(1240, 450 + (1 - eo(a2)) * 40, "hay vida en la Tierra!", 66, (45, 150, 60), a2, "xb")
    a3 = fade(t, 2.0, 0.6)
    txt = "Luz + Agua + CO₂  →  Glucosa + Oxígeno"
    w = tlen(txt, 36, "bold") + 70
    c.rrect(1240 - w / 2, 560, 1240 + w / 2, 636, 38, (45, 140, 60), a3)
    c.text(1240, 599, txt, 36, WHITE, a3)


# (duración, función, fondo, fundido de entrada, fundido de salida)
SCENES = [
    (7.0, sc_intro, "land", 0.8, 0.0),
    (22.0, sc_ingredients, "land", 0.0, 0.0),
    (8.5, sc_zoom, "land", 0.0, 0.5),
    (9.0, sc_chloro, "chloro", 0.5, 0.0),
    (11.0, sc_phase1, "chloro", 0.0, 0.0),
    (11.0, sc_phase2, "chloro", 0.0, 0.5),
    (11.0, sc_products, "land", 0.5, 0.5),
    (10.0, sc_equation, "eq", 0.5, 0.5),
    (8.0, sc_outro, "land", 0.5, 1.5),
]
TOTAL = sum(s[0] for s in SCENES)
NFRAMES = int(round(TOTAL * FPS))


def render(tg):
    acc = 0.0
    for dur, fn, bgname, fin, fout in SCENES:
        if tg < acc + dur or fn is SCENES[-1][1]:
            t = tg - acc
            c = Cv(bg(bgname))
            fn(c, t, dur)
            dark = 0.0
            if fin:
                dark = max(dark, 1 - prog(t, 0, fin))
            if fout:
                dark = max(dark, prog(t, dur - fout, fout))
            col = (0, 0, 0)
            c.cover(col, eio(dark))
            return c.final()
        acc += dur


def render_bytes(i):
    return render(i / FPS).tobytes()


# ---------------------------------------------------------------- música
def make_music(path, dur, sr=44100):
    n = int(dur * sr)
    t = np.arange(n) / sr
    out = np.zeros(n)
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    chords = [[48, 55, 60, 64], [43, 55, 59, 62], [45, 57, 60, 64], [41, 53, 57, 60]]  # Do, Sol, Lam, Fa
    beat = 4.0
    for k in range(int(dur / beat) + 1):
        ch = chords[k % 4]
        s0 = int(k * beat * sr)
        L = int((beat + 1.5) * sr)
        tt = np.arange(L) / sr
        env = np.minimum(1, tt / 1.2) * np.minimum(1, np.maximum(0, (beat + 1.5 - tt) / 1.5))
        seg = sum(np.sin(2 * np.pi * hz(m) * tt) + 0.3 * np.sin(4 * np.pi * hz(m) * tt) for m in ch)
        e = min(n, s0 + L)
        out[s0:e] += 0.05 * (seg * env)[: e - s0]
        for j in range(8):  # arpegio suave
            m = ch[[1, 2, 3, 2][j % 4]] + 12
            p0 = s0 + int(j * beat / 8 * sr)
            Lp = int(1.2 * sr)
            tp = np.arange(Lp) / sr
            note = np.sin(2 * np.pi * hz(m) * tp) * np.exp(-tp * 4) * np.minimum(1, tp / 0.01)
            e2 = min(n, p0 + Lp)
            if p0 < n:
                out[p0:e2] += 0.06 * note[: e2 - p0]
    out *= np.minimum(1, t / 2) * np.minimum(1, (dur - t) / 3)
    out = out / max(1e-9, np.abs(out).max()) * 0.5
    data = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(data.tobytes())


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", type=float, nargs="*", help="segundos a guardar como PNG")
    ap.add_argument("--out", default=os.path.join(AQUI, "fotosintesis.mp4"))
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    args = ap.parse_args()

    if args.preview is not None:
        for s in args.preview:
            name = f"preview_{s:05.1f}.png"
            render(s).save(name)
            print("guardado", name)
        return

    audio = args.out + ".wav"
    make_music(audio, TOTAL)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", audio,
           "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", args.out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(args.workers) as pool:
        for i, frame in enumerate(pool.imap(render_bytes, range(NFRAMES), chunksize=4)):
            ff.stdin.write(frame)
            if i % FPS == 0:
                print(f"\r{i / FPS:5.1f}s / {TOTAL:.1f}s", end="", flush=True)
    ff.stdin.close()
    ff.wait()
    os.remove(audio)
    print(f"\nListo: {args.out}")


if __name__ == "__main__":
    sys.exit(main())
