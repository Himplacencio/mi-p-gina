#!/usr/bin/env python3
"""
«Imagina que eres una planta»: vídeo vertical (9:16) sobre la fotosíntesis,
con estilo de historia cinematográfica: personaje maniquí con sombreado 3D,
cortes rápidos, subtítulos grandes palabra a palabra, música y efectos.

Todo se genera por código (Pillow + NumPy + FFmpeg).

Uso:
    python3 generar_video_vertical.py                 # crea fotosintesis_vertical.mp4
    python3 generar_video_vertical.py --preview 3 20  # guarda esos segundos como PNG
"""
import argparse
import math
import os
import random
import re
import subprocess
import sys
import wave
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
S = 1.5                       # sobremuestreo interno
IW, IH = int(W * S), int(H * S)
AQUI = os.path.dirname(os.path.abspath(__file__))

FONT_DIRS = ["/usr/share/fonts/opentype/inter/", "/usr/share/fonts/truetype/dejavu/"]
FONTS = {"xb": ["Inter-ExtraBold.otf", "DejaVuSans-Bold.ttf"],
         "bold": ["Inter-Bold.otf", "DejaVuSans-Bold.ttf"],
         "semi": ["Inter-SemiBold.otf", "DejaVuSans-Bold.ttf"],
         "reg": ["Inter-Regular.otf", "DejaVuSans.ttf"],
         "mono": ["DejaVuSans-Bold.ttf", "DejaVuSans-Bold.ttf"]}

MAN = (232, 232, 236)        # maniquí protagonista
DARKMAN = (38, 40, 48)
FRIEND = (150, 170, 205)
LEAFC, LEAFD = (95, 190, 80), (45, 125, 50)
OXY, CARB, HYDC, WATERC = (225, 60, 60), (70, 72, 80), (240, 240, 245), (70, 160, 255)
GOLD = (255, 205, 60)


# ------------------------------------------------------------------ utilidades
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def prog(t, s, d):
    return clamp((t - s) / d) if d > 0 else float(t >= s)


def eo(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def eio(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def back(x):
    x = clamp(x)
    return 1 + 2.7 * (x - 1) ** 3 + 1.7 * (x - 1) ** 2


def lerp(a, b, u):
    return a + (b - a) * u


def lerp2(p, q, u):
    return (lerp(p[0], q[0], u), lerp(p[1], q[1], u))


def lerpc(a, b, u):
    return tuple(int(lerp(a[i], b[i], u)) for i in range(3))


def anim(v, u):
    """Valor fijo o tupla (inicio, fin) interpolada con u."""
    if isinstance(v, tuple) and len(v) == 2 and isinstance(v[0], (tuple, list)):
        return lerp2(v[0], v[1], eio(u))
    if isinstance(v, tuple) and len(v) == 2:
        return lerp(v[0], v[1], eio(u))
    return v


def animp(v, u):
    """Punto fijo (x, y) o par de puntos ((x0, y0), (x1, y1)) interpolado."""
    if v is not None and isinstance(v[0], (tuple, list)):
        return lerp2(v[0], v[1], eio(u))
    return v


_fonts = {}


def font(size, w="bold"):
    key = (max(1, int(size)), w)
    if key not in _fonts:
        for name in FONTS[w]:
            for d in FONT_DIRS:
                if os.path.exists(d + name) and key not in _fonts:
                    _fonts[key] = ImageFont.truetype(d + name, key[0])
        if key not in _fonts:
            _fonts[key] = ImageFont.load_default(key[0])
    return _fonts[key]


LIGHT = np.array([-0.45, -0.62, 0.64])
LIGHT /= np.linalg.norm(LIGHT)


def vgrad(cols, h=IH):
    """Degradado vertical a partir de [(pos 0..1, color), ...]."""
    ys = np.linspace(0, 1, h)
    out = np.zeros((h, 3))
    for ch in range(3):
        out[:, ch] = np.interp(ys, [p for p, _ in cols], [c[ch] for _, c in cols])
    return Image.fromarray(out[:, None, :].astype(np.uint8), "RGB").resize((IW, h))


class Cv:
    def __init__(self, col=(0, 0, 0)):
        self.im = Image.new("RGB", (IW, IH), col)
        self.d = ImageDraw.Draw(self.im, "RGBA")
        self.cam(1, W / 2, H / 2)
        self.light, self.amb, self.tint, self.rim = LIGHT, 0.33, (1, 1, 1), None

    def cam(self, z, cx, cy):
        self.z, self.cx, self.cy = z, cx, cy

    def P(self, p):
        return (((p[0] - self.cx) * self.z + W / 2) * S, ((p[1] - self.cy) * self.z + H / 2) * S)

    def L(self, r):
        return r * self.z * S

    @staticmethod
    def c(col, a=1.0):
        return (int(col[0]), int(col[1]), int(col[2]), int(255 * clamp(a)))

    # ---- primitivas planas
    def circle(self, p, r, fill=None, a=1, outline=None, width=0):
        x, y = self.P(p)
        R = self.L(r)
        if R <= 0.3 or a <= 0.003:
            return
        self.d.ellipse([x - R, y - R, x + R, y + R], fill=self.c(fill, a) if fill else None,
                       outline=self.c(outline, a) if outline else None, width=max(1, int(self.L(width))) if outline else 0)

    def ellipse(self, p, rx, ry, fill=None, a=1, outline=None, width=0):
        x, y = self.P(p)
        Rx, Ry = self.L(rx), self.L(ry)
        if Rx <= 0.3 or Ry <= 0.3 or a <= 0.003:
            return
        self.d.ellipse([x - Rx, y - Ry, x + Rx, y + Ry], fill=self.c(fill, a) if fill else None,
                       outline=self.c(outline, a) if outline else None, width=max(1, int(self.L(width))) if outline else 0)

    def poly(self, pts, fill, a=1):
        if a > 0.003 and len(pts) > 2:
            self.d.polygon([self.P(p) for p in pts], fill=self.c(fill, a))

    def rrect(self, p0, p1, r, fill=None, a=1, outline=None, width=0):
        if a <= 0.003:
            return
        x0, y0 = self.P(p0)
        x1, y1 = self.P(p1)
        self.d.rounded_rectangle([x0, y0, x1, y1], radius=self.L(r), fill=self.c(fill, a) if fill else None,
                                 outline=self.c(outline, a) if outline else None,
                                 width=max(1, int(self.L(width))) if outline else 0)

    def line(self, pts, col, width, a=1, caps=True):
        if a <= 0.003 or len(pts) < 2:
            return
        self.d.line([self.P(p) for p in pts], fill=self.c(col, a), width=max(1, int(self.L(width))), joint="curve")
        if caps:
            for p in (pts[0], pts[-1]):
                self.circle(p, width / 2 - 0.3, col, a)

    def text(self, p, txt, size, col, a=1, w="bold", anchor="mm", stroke=0, scol=(0, 0, 0)):
        if a <= 0.01:
            return
        self.d.text(self.P(p), txt, font=font(self.L(size), w), fill=self.c(col, a), anchor=anchor,
                    stroke_width=int(self.L(stroke)), stroke_fill=self.c(scol, a))

    def glow(self, p, r, col, a=1, n=4):
        for k in range(n):
            self.circle(p, r * (1 + k * 0.6), col, a * 0.22 / (k + 1))

    def cover(self, col, a):
        if a > 0.003:
            self.d.rectangle([0, 0, IW, IH], fill=self.c(col, a))

    def blur(self, r):
        if r < 0.4:
            return
        f = 4
        sm = self.im.resize((IW // f, IH // f), Image.BILINEAR).filter(ImageFilter.GaussianBlur(r * S / f))
        self.im.paste(sm.resize((IW, IH), Image.BILINEAR))

    # ---- primitivas con sombreado 3D
    def _box(self, x0, y0, x1, y1):
        b = (int(max(0, x0)), int(max(0, y0)), int(min(IW, x1 + 1)), int(min(IH, y1 + 1)))
        return b if b[2] > b[0] and b[3] > b[1] else None

    def _blit(self, box, nx, ny, edge, col, a, spec, em):
        cov = np.clip(edge, 0, 1) * a
        if cov.max() <= 0.003:
            return
        rr = nx * nx + ny * ny
        nz = np.sqrt(np.clip(1 - rr, 0, 1))
        lx, ly, lz = self.light
        lam = np.clip(nx * lx + ny * ly + nz * lz, 0, 1)
        hv = np.array([lx, ly, lz + 1])
        hv /= np.linalg.norm(hv)
        sp = np.clip(nx * hv[0] + ny * hv[1] + nz * hv[2], 0, 1) ** 30 * spec
        tint = np.array(self.tint, np.float32)
        base = np.array(col, np.float32) / 255 * tint
        shade = self.amb + (1 - self.amb) * lam
        shade = shade * (1 - em) + em
        rgb = base * shade[..., None] + sp[..., None] * tint
        if self.rim is not None:
            rgb += np.array(self.rim, np.float32) / 255 * ((1 - nz) ** 2.5 * 0.6)[..., None]
        reg = np.asarray(self.im.crop(box), np.float32) / 255
        out = reg * (1 - cov[..., None]) + rgb * cov[..., None]
        self.im.paste(Image.fromarray((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)), box[:2])

    def capsule(self, p0, p1, r, col, a=1, spec=0.45, em=0.0):
        x0, y0 = self.P(p0)
        x1, y1 = self.P(p1)
        R = self.L(r)
        if R < 0.7 or a <= 0.003:
            return
        box = self._box(min(x0, x1) - R - 2, min(y0, y1) - R - 2, max(x0, x1) + R + 2, max(y0, y1) + R + 2)
        if not box:
            return
        ys, xs = np.mgrid[box[1]:box[3], box[0]:box[2]].astype(np.float32) + 0.5
        dx, dy = x1 - x0, y1 - y0
        l2 = dx * dx + dy * dy
        if l2 > 1e-6:
            u = np.clip(((xs - x0) * dx + (ys - y0) * dy) / l2, 0, 1)
            cx, cy = x0 + u * dx, y0 + u * dy
        else:
            cx, cy = x0, y0
        nx, ny = (xs - cx) / R, (ys - cy) / R
        edge = R - np.sqrt(nx * nx + ny * ny) * R + 0.5
        self._blit(box, nx, ny, edge, col, a, spec, em)

    def ball(self, p, r, col, a=1, spec=0.45, em=0.0):
        self.capsule(p, p, r, col, a, spec, em)

    def ellipsoid(self, p, rx, ry, col, a=1, spec=0.4, em=0.0):
        x, y = self.P(p)
        Rx, Ry = self.L(rx), self.L(ry)
        if min(Rx, Ry) < 0.7 or a <= 0.003:
            return
        box = self._box(x - Rx - 2, y - Ry - 2, x + Rx + 2, y + Ry + 2)
        if not box:
            return
        ys, xs = np.mgrid[box[1]:box[3], box[0]:box[2]].astype(np.float32) + 0.5
        nx, ny = (xs - x) / Rx, (ys - y) / Ry
        edge = (1 - np.sqrt(nx * nx + ny * ny)) * min(Rx, Ry) + 0.5
        self._blit(box, nx, ny, edge, col, a, spec, em)


# ------------------------------------------------------------------ personaje
POSES = {"down": ((10, 5), (10, 5)), "open": ((32, 75), (32, 75)), "up": ((150, 172), (150, 172)),
         "chest": ((16, -150), (16, -150)), "wave": ((10, 5), (140, 165)), "hips": ((40, -40), (40, -40))}


def leaf(c, base, ang, L, a=1, glow=0):
    v = (math.cos(math.radians(ang)), -math.sin(math.radians(ang)))
    n = (-v[1], v[0])
    s1, s2 = [], []
    for k in range(17):
        u = k / 16
        w = math.sin(math.pi * u) ** 0.8 * L * 0.3
        p = (base[0] + v[0] * L * u, base[1] + v[1] * L * u)
        s1.append((p[0] + n[0] * w, p[1] + n[1] * w))
        s2.append((p[0] - n[0] * w, p[1] - n[1] * w))
    if glow:
        c.glow((base[0] + v[0] * L * 0.5, base[1] + v[1] * L * 0.5), L * 0.5, (255, 240, 120), glow)
    tint = c.tint
    col = tuple(min(255, int(LEAFC[i] * tint[i] + glow * 60)) for i in range(3))
    dk = tuple(int(LEAFD[i] * tint[i]) for i in range(3))
    c.poly(s1 + s2[::-1], col, a)
    c.poly(s2 + [base], dk, a * 0.45)
    c.line([base, (base[0] + v[0] * L * 0.85, base[1] + v[1] * L * 0.85)], dk, max(1.5, L * 0.04), a)


def face(c, hc, R, expr, look=0, t=0, a=1, glow_eyes=False):
    ink = (12, 12, 16)
    ey = hc[1] - 0.02 * R
    blink = expr not in ("scared", "happy") and (t % 3.7) < 0.12
    brows = {"neutral": (0, 0), "angry": (0.11, -0.03), "worried": (-0.11, 0.05), "scared": (-0.15, -0.1),
             "happy": (-0.07, -0.03), "smile": (-0.04, 0), "sad": (-0.1, 0.06)}
    for sg in (-1, 1):
        ex = hc[0] + sg * 0.34 * R + look * 0.3 * R
        if glow_eyes:
            c.glow((ex, ey), 0.07 * R, (255, 255, 255), a)
            c.ellipse((ex, ey), 0.065 * R, 0.08 * R, (255, 255, 255), a)
            continue
        bi, bo = brows.get(expr, (0, 0))
        c.line([(ex - sg * 0.13 * R, ey - 0.3 * R + bi * R), (ex + sg * 0.15 * R, ey - 0.3 * R + bo * R)],
               ink, 0.075 * R, a)
        if blink:
            c.line([(ex - 0.09 * R, ey), (ex + 0.09 * R, ey)], ink, 0.045 * R, a)
        elif expr == "scared":
            c.circle((ex, ey), 0.17 * R, None, a, outline=ink, width=0.05 * R)
            c.circle((ex, ey), 0.055 * R, ink, a)
        elif expr == "happy":
            pts = [(ex + 0.1 * R * math.cos(th), ey + 0.02 * R - 0.1 * R * math.sin(th)) for th in np.linspace(0.2, math.pi - 0.2, 9)]
            c.line(pts, ink, 0.05 * R, a)
        else:
            c.ellipse((ex, ey), 0.095 * R, 0.13 * R, ink, a)
            c.circle((ex - 0.03 * R, ey - 0.05 * R), 0.03 * R, (255, 255, 255), a)
    if glow_eyes:
        return
    mx, my = hc[0] + look * 0.3 * R, hc[1] + 0.42 * R
    if expr in ("smile", "happy"):
        pts = [(mx + 0.17 * R * math.cos(th), my - 0.04 * R + 0.1 * R * math.sin(th)) for th in np.linspace(0.3, math.pi - 0.3, 11)]
        c.line(pts, ink, 0.045 * R, a)
    elif expr == "scared":
        c.ellipse((mx, my + 0.03 * R), 0.07 * R, 0.1 * R, ink, a)
    elif expr == "worried":
        pts = [(mx + (k / 8 - 0.5) * 0.3 * R, my + 0.025 * R * math.sin(k * 1.6)) for k in range(9)]
        c.line(pts, ink, 0.04 * R, a)
    elif expr in ("angry", "sad"):
        pts = [(mx + 0.13 * R * math.cos(th), my + 0.06 * R - 0.06 * R * math.sin(th)) for th in np.linspace(0.3, math.pi - 0.3, 9)]
        c.line(pts, ink, 0.045 * R, a)
    else:
        c.line([(mx - 0.08 * R, my), (mx + 0.08 * R, my)], ink, 0.04 * R, a)


def mannequin(c, x, y, s=1.0, col=MAN, expr="neutral", arms="down", look=0, t=0, sprout=True,
              wig=0.0, glow_eyes=False, leafglow=0.0, a=1.0, breathe=True):
    by = 3 * math.sin(t * 2.2) if breathe else 0

    def J(px, py):
        k = -py / 700
        return (x + px * s + wig * k * s, y + (py - by * k) * s)

    r = lambda v: v * s
    for sg in (-1, 1):  # piernas
        hip, knee, ank = J(sg * 30, -290), J(sg * 32, -155), J(sg * 32, -28)
        c.capsule(hip, knee, r(24), col, a)
        c.capsule(knee, ank, r(20), col, a)
        c.ball(knee, r(23), col, a)
        c.capsule(J(sg * 26, -14), J(sg * 44, -12), r(17), col, a)
    c.capsule(J(-24, -300), J(24, -300), r(46), col, a)
    c.capsule(J(0, -330), J(0, -385), r(30), col, a)
    c.capsule(J(0, -400), J(0, -452), r(54), col, a)
    c.capsule(J(-34, -440), J(34, -440), r(52), col, a)
    pose = POSES[arms]
    for i, sg in enumerate((-1, 1)):
        a1, a2 = (math.radians(v) for v in pose[i])
        sh = (sg * 74, -450)
        el = (sh[0] + sg * 118 * math.sin(a1), sh[1] + 118 * math.cos(a1))
        wr = (el[0] + sg * 108 * math.sin(a2), el[1] + 108 * math.cos(a2))
        if arms == "wave" and i == 1:
            wr = (wr[0] + 18 * math.sin(t * 9), wr[1])
        c.ball(J(*sh), r(27), col, a)
        c.capsule(J(*sh), J(*el), r(19), col, a)
        c.ball(J(*el), r(18), col, a)
        c.capsule(J(*el), J(*wr), r(16), col, a)
        c.ball(J(*wr), r(22), col, a)
    c.capsule(J(0, -480), J(0, -515), r(17), col, a)
    hc, R = J(0, -600), r(96)
    c.ball(hc, R, col, a, spec=0.5)
    face(c, hc, R, expr, look, t, a, glow_eyes)
    if sprout:
        top = J(3, -742)
        c.capsule(J(0, -690), top, r(6), (80, 160, 60), a)
        sw = 4 * math.sin(t * 1.7)
        leaf(c, top, 150 + sw, r(75), a, leafglow)
        leaf(c, top, 28 - sw, r(80), a, leafglow)
    return hc, R


# ------------------------------------------------------------------ moléculas 3D
def co2_3d(c, p, s=1, a=1):
    c.ball((p[0] - 34 * s, p[1]), 20 * s, OXY, a)
    c.ball((p[0] + 34 * s, p[1]), 20 * s, OXY, a)
    c.ball(p, 23 * s, CARB, a, spec=0.6)


def h2o_3d(c, p, s=1, a=1, spread=0.0):
    for sg in (-1, 1):
        q = (p[0] + sg * (30 + spread) * s, p[1] + (24 + spread * 0.5) * s)
        c.ball(q, 17 * s, HYDC, a)
    c.ball(p, 28 * s, OXY, a, spec=0.6)


def o2_3d(c, p, s=1, a=1):
    c.ball((p[0] - 15 * s, p[1]), 20 * s, OXY, a)
    c.ball((p[0] + 15 * s, p[1]), 20 * s, OXY, a)


def orb(c, p, r, label, a=1):
    c.glow(p, r, GOLD, a)
    c.ball(p, r, GOLD, a, spec=0.7, em=0.35)
    if label:
        c.text(p, label, r * 0.48, (60, 35, 0), a, "xb")


# ------------------------------------------------------------------ escenarios
def day_params(day):
    keys = [(0.0, (6, 9, 24), (24, 32, 62), (0.42, 0.48, 0.70), 0.22, (50, 70, 140), 0.32),
            (1.0, (55, 70, 135), (255, 165, 105), (1.0, 0.82, 0.70), 0.30, (255, 150, 70), 0.62),
            (2.0, (70, 145, 225), (200, 228, 248), (1.0, 1.0, 1.0), 0.36, (110, 110, 120), 1.0)]
    i = 0 if day <= 1 else 1
    u = clamp(day - keys[i][0])
    k0, k1 = keys[i], keys[i + 1]
    return dict(top=lerpc(k0[1], k1[1], u), bot=lerpc(k0[2], k1[2], u),
                tint=tuple(lerp(k0[3][j], k1[3][j], u) for j in range(3)), amb=lerp(k0[4], k1[4], u),
                rim=lerpc(k0[5], k1[5], u), land=lerp(k0[6], k1[6], u))


def field_bg(c, t, day, sun=None, blur=3):
    dp = day_params(day)
    c.im.paste(vgrad([(0, dp["top"]), (0.62, dp["bot"]), (1, dp["bot"])]))
    if day < 1:
        rnd = random.Random(4)
        for _ in range(140):
            p = (rnd.uniform(-300, 1400), rnd.uniform(-400, 1150))
            tw = 0.6 + 0.4 * math.sin(t * 3 + p[0])
            c.circle(p, rnd.uniform(1.2, 3), (255, 255, 255), (1 - day) * tw)
    if sun is not None:
        c.glow(sun, 90, (255, 210, 120), 1.0, 6)
        c.circle(sun, 80, (255, 236, 170))
    f = dp["land"]
    tint = dp["tint"]
    layers = [((70, 120, 90), 1150, 70, 0.004, 0.3), ((55, 110, 65), 1220, 55, 0.006, 2.0),
              ((48, 100, 55), 1290, 35, 0.009, 4.0)]
    for col, base, amp, fr, ph in layers:
        cc = tuple(int(col[i] * f * tint[i]) for i in range(3))
        pts = [(x, base - amp * math.sin(x * fr + ph) - amp * 0.4 * math.sin(x * fr * 2.3)) for x in range(-1500, 2600, 60)]
        c.poly(pts + [(2600, 5000), (-1500, 5000)], cc)
    gc = tuple(int(c_ * f * tint[i]) for i, c_ in enumerate((62, 125, 58)))
    c.poly([(-1500, 1320), (2600, 1320), (2600, 5000), (-1500, 5000)], gc)
    rnd = random.Random(9)
    dk = tuple(int(v * 0.75) for v in gc)
    for _ in range(160):
        x, y = rnd.uniform(-600, 1700), rnd.uniform(1330, 2600)
        hh = rnd.uniform(14, 30) * (0.6 + (y - 1320) / 900)
        c.line([(x, y), (x + rnd.uniform(-5, 5), y - hh)], dk, 4, 0.8)
    c.blur(blur)
    c.tint, c.amb, c.rim = dp["tint"], dp["amb"], dp["rim"]
    return dp


def sc_field(c, t, d, day=2.0, z=1.0, f=(540, 960), sun=None, blur=None, expr="neutral", arms="down",
             look=0, wig=0, rays=0, figure=None, fig_in=0.0, o2=False, tags=False, shake=0.0, cut_fig=False,
             walk=0):
    u = t / d
    day = anim(day, u)
    z = anim(z, u)
    fx, fy = animp(f, u)
    if shake:
        fx += shake * (math.sin(t * 37) + math.sin(t * 23)) * 3
        fy += shake * math.sin(t * 29) * 3
    c.cam(z, fx, fy)
    sp = animp(sun, u)
    field_bg(c, t, day, sp, blur if blur is not None else 2 + 2.5 * z)
    c.ellipse((540, 1505), 115, 20, (0, 0, 0), 0.28)
    if figure:
        fa = eo(prog(t, fig_in, 0.8)) if fig_in > 0 else 1
        col = DARKMAN if figure == "dark" else FRIEND
        ex = "smile" if figure == "friend" else "neutral"
        fx2 = 830 if not cut_fig else 760
        mannequin(c, fx2, 1470, 0.93, col, ex, "wave" if figure == "friend" else "down", look=-0.6, t=t + 1,
                  sprout=False, glow_eyes=figure == "dark", a=fa)
    hc, R = mannequin(c, 540, 1500, 1.0, MAN, expr, arms, look, t, True, wig * math.sin(t * 11) * 22,
                      leafglow=rays * (0.6 + 0.4 * math.sin(t * 6)))
    if rays and sp is not None:
        for k, tgt in enumerate([(470, 760), (612, 752)]):
            c.poly([(sp[0] - 30, sp[1]), (sp[0] + 30, sp[1]), (tgt[0] + 20, tgt[1]), (tgt[0] - 20, tgt[1])],
                   (255, 235, 140), 0.18 * rays)
            for j in range(4):
                q = ((t * 0.9 + j / 4 + k * 0.13) % 1)
                p = lerp2(sp, tgt, q)
                c.glow(p, 8, (255, 230, 120), rays * 0.9, 3)
                c.circle(p, 6, (255, 250, 210), rays)
    if o2:
        for k in range(9):
            q = ((t * 0.45 + k / 9) % 1)
            st = (520 + (k % 3 - 1) * 60, 760)
            en = (830 + 25, 1470 - 600 * 0.93 + 45)
            p = lerp2(st, en, q)
            p = (p[0], p[1] - math.sin(q * math.pi) * 160 + math.sin(t * 3 + k) * 10)
            o2_3d(c, p, 0.55, min(1, q * 5) * (1 - prog(q, 0.85, 0.15)))
    if tags:
        tag(c, (90, 430), 1, "LUZ, AGUA Y CO₂", (60, 120, 230), fade_a=eo(prog(t, 0.3, 0.4)), anchor=(470, 755))
        tag(c, (580, 600), 2, "SOLO TIERRA", (220, 60, 60), fade_a=eo(prog(t, 1.0, 0.4)), anchor=(650, 1420))
    return hc, R


def tag(c, p, n, txt, col, fade_a=1, anchor=None):
    if fade_a <= 0.01:
        return
    w = font(34 * S, "xb").getlength(txt) / S + 110
    if anchor:
        c.line([(p[0] + w / 2, p[1] + 34), anchor], (255, 255, 255), 4, fade_a)
        c.circle(anchor, 9, col, fade_a)
    c.rrect((p[0] + 4, p[1] + 6), (p[0] + w + 4, p[1] + 74), 34, (0, 0, 0), 0.3 * fade_a)
    c.rrect(p, (p[0] + w, p[1] + 68), 34, (255, 255, 255), fade_a)
    c.circle((p[0] + 36, p[1] + 34), 24, col, fade_a)
    c.text((p[0] + 36, p[1] + 35), str(n), 30, (255, 255, 255), fade_a, "xb")
    c.text((p[0] + 72, p[1] + 35), txt, 34, (25, 25, 30), fade_a, "xb", anchor="lm")


def closeup(day=2.0, expr="neutral", z=(3.0, 3.25), look=0, arms="down", shake=0, sun=None, **kw):
    return dict(day=day, expr=expr, z=z, f=(540, 930), look=look, arms=arms, shake=shake, sun=sun, blur=16, **kw)


# ---- panel LED
_bitmaps = {}


def led_bitmap(txt):
    if txt not in _bitmaps:
        f = ImageFont.truetype(FONT_DIRS[1] + "DejaVuSans-Bold.ttf", 15)
        w = int(f.getlength(txt)) + 2
        im = Image.new("L", (w, 18), 0)
        ImageDraw.Draw(im).text((1, 0), txt, font=f, fill=255)
        _bitmaps[txt] = np.asarray(im) > 110
    return _bitmaps[txt]


def sc_led(c, t, d, lines=("",), swap=None, z=(1.0, 1.07), sub=None):
    u = t / d
    c.cam(anim(z, u), 540 + 4 * math.sin(t * 1.3), 900 + 3 * math.sin(t * 1.7))
    c.im.paste(vgrad([(0, (16, 18, 18)), (1, (34, 38, 36))]))
    for row in range(-10, 40):
        y = row * 70
        c.line([(-400, y), (1500, y)], (55, 62, 58), 3, 0.8, caps=False)
        for col in range(-6, 16):
            x = col * 140 + (70 if row % 2 else 0)
            c.line([(x, y), (x, y + 70)], (55, 62, 58), 3, 0.8, caps=False)
    c.blur(5)
    if swap and t >= swap[0]:
        lines = swap[1]
    bms = [led_bitmap(s) for s in lines]
    cols = max(b.shape[1] for b in bms)
    rows = sum(b.shape[0] for b in bms) + 4 * (len(bms) - 1)
    pitch = min(13.0, 880 / cols)
    bw, bh = cols * pitch + 60, rows * pitch + 60
    x0, y0 = 540 - bw / 2, 860 - bh / 2
    c.rrect((x0 - 14, y0 - 14), (x0 + bw + 14, y0 + bh + 14), 18, (70, 72, 76))
    c.rrect((x0 - 6, y0 - 6), (x0 + bw + 6, y0 + bh + 6), 14, (30, 30, 32))
    c.rrect((x0, y0), (x0 + bw, y0 + bh), 10, (10, 8, 6))
    c.line([(x0 + 200, y0 - 14), (x0 + 200, -300)], (60, 60, 64), 10, caps=False)
    c.line([(x0 + bw - 200, y0 - 14), (x0 + bw - 200, -300)], (60, 60, 64), 10, caps=False)
    flick = 0.92 + 0.08 * math.sin(t * 40)
    yy = y0 + 30
    for b in bms:
        xx = 540 - b.shape[1] * pitch / 2
        for r_ in range(b.shape[0]):
            for q in range(b.shape[1]):
                p = (xx + q * pitch + pitch / 2, yy + r_ * pitch + pitch / 2)
                if b[r_, q]:
                    c.circle(p, pitch * 0.62, (255, 120, 30), 0.25 * flick)
                    c.circle(p, pitch * 0.36, (255, 160, 60), flick)
                else:
                    c.circle(p, pitch * 0.3, (50, 26, 14), 1)
        yy += (b.shape[0] + 4) * pitch
    c.glow((540, 860), bw * 0.35, (255, 120, 40), 0.25, 3)
    if sub:
        c.text((540, y0 + bh + 70), sub, 30, (170, 175, 170), 0.9, "semi")


# ---- título
def sc_title(c, t, d):
    c.im.paste(vgrad([(0, (4, 20, 10)), (0.5, (14, 60, 30)), (1, (4, 18, 10))]))
    rnd = random.Random(2)
    for k in range(70):
        x = rnd.uniform(0, W)
        sp = rnd.uniform(40, 120)
        y = (rnd.uniform(0, H) - t * sp) % H
        col = (180, 255, 140) if k % 3 else (255, 230, 120)
        c.glow((x, y), rnd.uniform(3, 7), col, 0.8, 3)
    z = lerp(1.25, 1.0, eo(prog(t, 0, 0.6)))
    c.cam(z, 540, 960)
    mask = Image.new("L", (IW, IH), 0)
    md = ImageDraw.Draw(mask)
    fnt = font(c.L(132), "xb")
    md.text(c.P((540, 900)), "FOTOSÍNTESIS", font=fnt, fill=255, anchor="mm")
    a = eo(prog(t, 0, 0.35))
    glow = mask.filter(ImageFilter.GaussianBlur(28 * S))
    col = Image.new("RGB", (IW, IH), (120, 255, 110))
    c.im.paste(col, (0, 0), glow.point(lambda v: int(min(255, v * 1.6 * a))))
    c.text((540, 900), "FOTOSÍNTESIS", 132, (235, 255, 225), a, "xb")
    c.cam(1, 540, 960)
    c.text((540, 790), "TU SUPERPODER", 40, (190, 240, 170), eo(prog(t, 0.4, 0.4)), "bold")


# ---- nota de papel
RECIPE_Y = {1: 700, 2: 860, 3: 1040, 4: 1210}


def sc_paper(c, t, d, z=(1.0, 1.08), f=(540, 960), circle=None):
    u = t / d
    c.cam(anim(z, u), *animp(f, u))
    c.im.paste(vgrad([(0, (18, 50, 26)), (1, (8, 30, 16))]))
    rnd = random.Random(5)
    for row in range(-4, 16):
        for col in range(-3, 9):
            x = col * 200 + (100 if row % 2 else 0) + rnd.uniform(-15, 15)
            y = row * 170 + rnd.uniform(-15, 15)
            c.rrect((x, y), (x + 186, y + 156), 50, (40, 110, 50), 0.9)
            c.ellipse((x + 50, y + 40), 20, 12, (30, 90, 40), 0.9)
    c.blur(9)
    top, bot, x0, x1 = 420, 1330, 150, 930
    torn = [(x, bot + 18 * math.sin(x * 0.11) + 12 * math.sin(x * 0.37)) for x in range(int(x1), int(x0) - 1, -20)]
    c.poly([(x0 + 16, top + 22), (x1 + 16, top + 22)] + [(p[0] + 16, p[1] + 22) for p in torn], (0, 0, 0), 0.45)
    c.poly([(x0, top), (x1, top)] + torn, (238, 232, 215))
    for k in range(6):
        c.ellipse((rnd.uniform(200, 880), rnd.uniform(500, 1250)), rnd.uniform(40, 110), rnd.uniform(30, 70), (205, 190, 160), 0.18)
    ink, red = (45, 45, 50), (200, 50, 45)
    c.text((540, 500), "RECETA SECRETA", 62, ink, 1, "xb")
    c.line([(250, 545), (830, 545)], red, 4, 0.9)
    c.text((540, 580), "SOLO PARA PLANTAS", 26, red, 1, "bold")
    items = [("INGREDIENTE Nº 1:", "LUZ DEL SOL"), ("INGREDIENTE Nº 2:", "AGUA (H₂O)"),
             ("INGREDIENTE Nº 3:", "DIÓXIDO DE CARBONO (CO₂)"), ("RESULTADO:", "GLUCOSA + OXÍGENO")]
    for i, (a_, b_) in enumerate(items, 1):
        y = RECIPE_Y[i]
        c.text((200, y - 30), a_, 34, ink, 1, "bold", anchor="lm")
        c.text((200, y + 22), b_, 40 if i != 3 else 34, (20, 20, 25), 1, "xb", anchor="lm")
    if circle:
        y = RECIPE_Y[circle]
        pr = eo(prog(t, 0.25, 0.7))
        x, yy = c.P((520, y))
        rx, ry = c.L(370), c.L(78)
        c.d.arc([x - rx, yy - ry, x + rx, yy + ry], -200, -200 + 370 * pr, fill=c.c(red, 0.95), width=int(c.L(7)))


# ---- raíces
def root_paths():
    rnd = random.Random(12)
    paths = []

    def grow(p, ang, length, depth, path):
        pts = path + [p]
        if depth == 0:
            paths.append(pts)
            return
        n = 2 if depth > 1 else 1
        for k in range(n + (depth == 3)):
            a2 = ang + rnd.uniform(-35, 35)
            q = (p[0] + math.cos(math.radians(a2)) * length, p[1] + math.sin(math.radians(a2)) * length)
            grow(q, a2, length * 0.75, depth - 1, pts)

    for sg in (-1, 1):
        foot = (540 + sg * 52, 760)
        grow(foot, 90 + sg * 20, 230, 3, [])
    return paths


ROOTPATHS = root_paths()


def sc_roots(c, t, d):
    c.cam(lerp(1.0, 1.07, t / d), 540, 980)
    c.im.paste(vgrad([(0, (110, 170, 230)), (0.3, (190, 220, 240)), (1, (190, 220, 240))]))
    c.poly([(-500, 700), (1600, 700), (1600, 770), (-500, 770)], (60, 130, 55))
    c.blur(4)
    c.poly([(-500, 760), (1600, 760), (1600, 3000), (-500, 3000)], (62, 42, 28))
    rnd = random.Random(3)
    for k in range(5):
        y = 900 + k * 260
        pts = [(x, y + 30 * math.sin(x * 0.006 + k)) for x in range(-500, 1650, 80)]
        c.poly(pts + [(1600, 3000), (-500, 3000)], (52 - k * 6, 35 - k * 4, 24 - k * 3), 0.6)
    c.light = np.array([-0.3, -0.85, 0.43])
    c.amb = 0.25
    for _ in range(22):
        c.ball((rnd.uniform(0, 1080), rnd.uniform(820, 2000)), rnd.uniform(12, 34), (110, 95, 80))
    drops = random.Random(8)
    for k, path in enumerate(ROOTPATHS):
        for i in range(len(path) - 1):
            r0 = 16 * (0.62 ** i)
            c.capsule(path[i], path[i + 1], r0, (215, 185, 135), 1, 0.3)
    mannequin(c, 540, 760, 1.5, MAN, "neutral", "down", 0, t, sprout=False)
    vein = eo(prog(t, 1.2, 1.5))
    for sg in (-1, 1):
        seg = [(540 + sg * 48, 730), (540 + sg * 48, 540), (540 + sg * 45, 330)]
        y_top = lerp(730, 330, vein)
        c.line([(540 + sg * 48, 730), (540 + sg * 47, y_top)], (90, 190, 255), 10, 0.55 * vein)
    for k in range(18):
        path = ROOTPATHS[k % len(ROOTPATHS)][::-1]
        t0 = (k * 0.31) % 2.4
        q = prog(t, t0, 1.6)
        if 0 < q < 1:
            st = (path[0][0] + drops.uniform(-120, 120), path[0][1] + drops.uniform(40, 160))
            p = lerp2(st, path[0], eio(q * 2)) if q < 0.5 else along(path, (q - 0.5) * 2)
            c.glow(p, 12, WATERC, 1, 3)
            c.ball(p, 11, WATERC, 1, 0.9, 0.15)
        else:
            drops.uniform(0, 1), drops.uniform(0, 1)


def along(pts, u):
    seg = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
    dd = clamp(u) * sum(seg)
    for i, s in enumerate(seg):
        if dd <= s or i == len(seg) - 1:
            return lerp2(pts[i], pts[i + 1], dd / s if s else 0)
        dd -= s
    return pts[-1]


# ---- estoma
def sc_stoma(c, t, d, opening=(0.08, 0.08), co2=False, z=(1.0, 1.1)):
    u = t / d
    c.cam(anim(z, u), 540, 960)
    c.im.paste(vgrad([(0, (40, 110, 45)), (1, (25, 80, 35))]))
    rnd = random.Random(6)
    for row in range(-3, 14):
        for col in range(-2, 8):
            x = col * 210 + (105 if row % 2 else 0) + rnd.uniform(-20, 20)
            y = row * 180 + rnd.uniform(-20, 20)
            c.rrect((x, y), (x + 196, y + 166), 60, (95, 175, 80))
            c.rrect((x + 8, y + 8), (x + 188, y + 158), 56, (120, 195, 100))
    c.blur(4)
    op = lerp(opening[0], opening[1], eo(prog(t, 0.1, 0.9))) if opening[0] != opening[1] else opening[0]
    op += 0.03 * math.sin(t * 2)
    gap = 18 + op * 70
    c.ellipse((540, 960), gap + 30, 300, (50, 110, 45))
    c.ellipse((540, 960), gap, 250, (8, 20, 10))
    c.light = np.array([-0.4, -0.55, 0.73])
    rnd2 = random.Random(1)
    for sg in (-1, 1):
        cx = 540 + sg * (gap + 105)
        c.ellipsoid((cx, 960), 125, 330, (115, 200, 95), 1, 0.35)
        for k in range(9):
            ang = rnd2.uniform(0, 2 * math.pi)
            rr = math.sqrt(rnd2.uniform(0.05, 0.6))
            c.ellipsoid((cx + math.cos(ang) * 80 * rr, 960 + math.sin(ang) * 260 * rr), 22, 14, (45, 140, 50), 1, 0.3)
    if co2:
        for k in range(8):
            q = prog(t, 0.9 + k * 0.32, 1.6)
            if 0 < q < 1:
                st = (540 + (k % 2 * 2 - 1) * (260 + 40 * (k % 3)), 350 + (k * 137) % 300)
                p = lerp2(st, (540, 960), eio(q))
                s = lerp(1.5, 0.25, eio(q))
                co2_3d(c, p, s, 1 - prog(q, 0.8, 0.2))


# ---- túnel del cloroplasto
def sc_tunnel(c, t, d, speed=1.0, tint=None, still=False):
    c.im.paste(vgrad([(0, (3, 20, 8)), (0.5, (10, 45, 18)), (1, (3, 18, 8))]))
    vp = (540, 900)
    c.cam(1, 540, 960)
    bgc = np.array([10, 45, 18])
    c.light = np.array([0.0, -0.75, 0.66])
    off = 0 if still else (t * speed * 0.9) % 0.7
    for i in range(16, -1, -1):
        zz = 0.55 + i * 0.7 - off
        if zz < 0.5:
            continue
        sc = 1 / zz
        fog = 1 - math.exp(-(zz - 0.5) * 0.35)
        c.ellipse(vp, 600 * sc, 820 * sc, None, 0.35 * (1 - fog), outline=(120, 200, 110), width=6 * sc)
        for sg in (-1, 1):
            gx = vp[0] + sg * 380 * sc
            for k in range(4):
                gy = vp[1] + (k - 1.5) * 52 * sc + (120 if (i % 2) else -80) * sc
                col = tuple(int(v) for v in np.array((60, 170, 70)) * (1 - fog) + bgc * fog)
                if 150 * sc * c.z * S < 5:
                    continue
                c.ellipsoid((gx, gy), 150 * sc, 22 * sc, col, 1, 0.35 * (1 - fog))
    for k in range(3):
        x = 300 + k * 260 + 40 * math.sin(t * 0.7 + k)
        c.poly([(x - 40, -100), (x + 40, -100), (vp[0] + (x - 540) * 0.2 + 30, vp[1]), (vp[0] + (x - 540) * 0.2 - 30, vp[1])],
               (220, 255, 170), 0.06)
    rnd = random.Random(4)
    for k in range(40):
        ang = rnd.uniform(0, 2 * math.pi)
        dist = ((rnd.uniform(0, 1) + t * 0.25 * speed) % 1)
        rr = 40 + dist ** 2 * 900
        p = (vp[0] + math.cos(ang) * rr, vp[1] + math.sin(ang) * rr * 1.3)
        c.circle(p, 2 + dist * 6, (200, 255, 160), 0.6 * dist)
    if tint:
        c.cover(tint[0], tint[1])


def sc_split(c, t, d, split=False):
    sc_tunnel(c, 3.0, 10, still=True)
    c.blur(12)
    c.cover((0, 0, 0), 0.25)
    c.light = LIGHT
    c.amb = 0.3
    ctr = (540, 900)
    if not split:
        ba = eo(prog(t, 0.15, 0.4))
        c.poly([(-100, -100), (120, -200), (ctr[0] + 30, ctr[1]), (ctr[0] - 30, ctr[1])], (255, 240, 150), 0.22 * ba)
        for j in range(6):
            q = (t * 1.1 + j / 6) % 1
            p = lerp2((10, -150), ctr, q)
            c.glow(p, 12, GOLD, ba, 3)
        sh = 6 * prog(t, 0.6, 1.0) * math.sin(t * 60)
        c.glow(ctr, 140, (255, 230, 140), 0.6 * prog(t, 0.5, 1.2), 3)
        h2o_3d(c, (ctr[0] + sh, ctr[1]), 3.0, 1, 0)
    else:
        fl = 1 - prog(t, 0, 0.35)
        q = eo(prog(t, 0.05, 1.2))
        o2_3d(c, (ctr[0], lerp(ctr[1], 380, eio(prog(t, 0.3, 2.0)))), 2.6, 1)
        for sg in (-1, 1):
            p = (ctr[0] + sg * lerp(90, 380, q), ctr[1] + lerp(70, 300, q))
            c.ball(p, 50, HYDC, 1)
            c.text((p[0], p[1] + 85), "H⁺", 34, (230, 230, 230), q, "xb")
        if t > 1.6:
            for k, (lbl, p) in enumerate((("ATP", (300, 1560)), ("NADPH", (780, 1560)))):
                a = eo(prog(t, 1.6 + k * 0.3, 0.4))
                orb(c, p, 70 * back(prog(t, 1.6 + k * 0.3, 0.4)), lbl, a)
        c.cover((255, 255, 240), 0.85 * fl)


def sc_calvin(c, t, d, glucose=False):
    sc_tunnel(c, 6.0, 10, still=True)
    c.blur(14)
    c.cover((20, 10, 0), 0.35)
    c.light = LIGHT
    c.amb = 0.3
    ctr = (540, 900)
    rot = t * 1.4
    tilt = lerp(0.42, 1.0, eio(prog(t, 0.6, 1.0))) if glucose else 0.42
    rad = lerp(270, 210, eio(prog(t, 0.6, 1.0))) if glucose else 270
    c.ellipse(ctr, rad, rad * tilt, None, 0.6, outline=(255, 190, 90), width=5)
    atoms = []
    for k in range(6):
        ang = rot * (0 if glucose and t > 1.6 else 1) + k * math.pi / 3 + (math.pi / 6 if glucose else 0)
        depth = math.sin(ang)
        p = (ctr[0] + math.cos(ang) * rad, ctr[1] + math.sin(ang) * rad * tilt)
        atoms.append((depth, p))
    atoms.sort()
    gl = prog(t, 1.0, 1.0) if glucose else 0
    if glucose:
        pts = [p for _, p in sorted(atoms, key=lambda a: math.atan2(a[1][1] - ctr[1], a[1][0] - ctr[0]))]
        c.line(pts + [pts[0]], (255, 200, 110), 14, gl, caps=False)
        c.glow(ctr, 260, (255, 170, 60), gl * 0.7, 3)
    for depth, p in atoms:
        sc = 1 + 0.25 * depth * (1 - tilt)
        col = lerpc(CARB, (255, 170, 50), gl)
        c.ball(p, 52 * sc, col, 1, 0.6, 0.25 * gl)
    if not glucose:
        for k in range(4):
            q = prog(t, 0.3 + k * 0.45, 1.2)
            if 0 < q < 1:
                st = (900 - k * 90, -50)
                co2_3d(c, lerp2(st, ctr, eio(q)), lerp(1.6, 0.6, q), 1 - prog(q, 0.8, 0.2))
        for k in range(3):
            q = prog(t, 0.6 + k * 0.5, 1.2)
            if 0 < q < 1:
                orb(c, lerp2((-60, 1300 - k * 120), ctr, eio(q)), lerp(45, 15, q), "ATP" if k != 1 else "", 1 - prog(q, 0.85, 0.15))
    else:
        a = eo(prog(t, 1.6, 0.5))
        c.text((540, 1250), "C₆H₁₂O₆", 70, (255, 220, 150), a, "xb", stroke=2)
        rnd = random.Random(1)
        for k in range(24):
            ang = rnd.uniform(0, 2 * math.pi)
            q = (t * 0.6 + rnd.uniform(0, 1)) % 1
            p = (ctr[0] + math.cos(ang) * (150 + 380 * q), ctr[1] + math.sin(ang) * (150 + 380 * q))
            c.glow(p, 5, GOLD, gl * (1 - q), 2)


# ------------------------------------------------------------------ guion
# Cada plano: (función, parámetros, subtítulos [(texto, duración)], efectos, ambiente)
F = sc_field
SHOTS = [
    (F, dict(day=0.15, z=(1.0, 1.1), f=(540, 1000)), [("IMAGINA", 1.0), ("QUE ERES", 0.6), ("UNA PLANTA.", 1.1)], ["whoosh"], "dark"),
    (F, dict(day=0.15, z=(1.45, 1.55), f=(540, 1150), wig=1, expr="worried"), [("NO PUEDES", 0.6), ("MOVERTE.", 1.0)], [], "dark"),
    (F, closeup(day=0.15, expr="worried", look=-0.3), [("NO PUEDES", 0.6), ("IR A COMPRAR", 0.8), ("COMIDA.", 0.9)], [], "dark"),
    (F, closeup(day=0.15, expr="angry", z=(3.4, 3.7), shake=1), [("Y TIENES", 0.6), ("HAMBRE.", 1.1)], ["boom"], "dark"),
    (sc_led, dict(lines=("05:59",)), [("PERO ENTONCES,", 1.3)], ["beep"], "dark"),
    (sc_led, dict(lines=("05:59",), swap=(0.4, ("06:00",))), [("A LAS SEIS", 0.8), ("EN PUNTO,", 0.9)], ["beep2"], "dark"),
    (F, dict(day=(0.2, 1.25), z=(1.0, 1.05), f=(540, 1000), sun=((780, 1330), (780, 1010)), expr="neutral", look=0.3),
     [("SALE", 0.7), ("EL SOL.", 1.4)], ["rise"], "bright"),
    (F, closeup(day=1.3, expr="happy", sun=(780, 980)), [("SONRÍES.", 1.0), ("PORQUE TIENES", 0.8), ("UN SUPERPODER:", 1.1)], [], "bright"),
    (sc_title, {}, [("~LA FOTOSÍNTESIS.", 2.0)], ["boom", "chime"], "bright"),
    (sc_paper, dict(z=(0.9, 1.0)), [("EN TUS HOJAS", 0.8), ("HAY UNA NOTA.", 1.0)], ["whoosh"], "bright"),
    (sc_paper, dict(z=(1.15, 1.22), f=((530, 700), (530, 740))), [("RECETA", 0.6), ("SECRETA.", 0.8), ("SOLO PLANTAS.", 1.0)], [], "bright"),
    (sc_paper, dict(z=(1.2, 1.28), f=(530, RECIPE_Y[1] + 60), circle=1), [("INGREDIENTE", 0.7), ("NÚMERO UNO:", 0.8), ("*LUZ.", 0.9)], ["scribble"], "bright"),
    (F, dict(day=2.0, z=(1.9, 2.1), f=(560, 820), sun=(900, 330), rays=1, expr="happy", blur=8),
     [("LA ATRAPAS", 0.8), ("CON TUS HOJAS.", 1.1)], ["shine"], "bright"),
    (sc_paper, dict(z=(1.2, 1.28), f=(530, RECIPE_Y[2] + 60), circle=2), [("NÚMERO DOS:", 0.8), ("*AGUA.", 1.0)], ["scribble"], "bright"),
    (sc_roots, {}, [("LA BEBES", 0.7), ("POR LAS RAÍCES,", 1.0), ("DESDE EL SUELO.", 1.0)], ["bubble"], "bright"),
    (sc_paper, dict(z=(1.2, 1.28), f=(530, RECIPE_Y[3] + 60), circle=3), [("NÚMERO TRES:", 0.8), ("*DIÓXIDO", 0.6), ("*DE CARBONO.", 1.0)], ["scribble"], "bright"),
    (sc_stoma, dict(opening=(0.05, 0.05)), [("EN TUS HOJAS", 0.8), ("HAY POROS", 0.7), ("DIMINUTOS.", 0.9)], ["whoosh"], "tense"),
    (sc_stoma, dict(opening=(0.05, 1.0), co2=True, z=(1.1, 1.25)), [("SE ABREN.", 1.0), ("Y EL CO₂", 0.7), ("ENTRA.", 1.1)], ["door"], "tense"),
    (sc_tunnel, dict(speed=1.2), [("AHORA", 0.5), ("ENTRAS", 0.6), ("EN LA HOJA.", 0.9)], ["whoosh"], "tense"),
    (sc_tunnel, dict(speed=0.6), [("MILLONES DE", 0.7), ("*CLOROPLASTOS.", 1.1), ("FÁBRICAS VERDES.", 1.1)], [], "tense"),
    (sc_led, dict(lines=("FASE 1", "LUZ")), [("FASE UNO.", 1.2)], ["boom"], "tense"),
    (sc_split, dict(split=False), [("LA LUZ", 0.6), ("GOLPEA", 0.6), ("EL AGUA", 0.8)], ["shine"], "tense"),
    (sc_split, dict(split=True), [("Y LA ROMPE.", 0.9), ("SALE *OXÍGENO", 1.0), ("Y SE GUARDA", 0.7), ("*ENERGÍA.", 1.0)], ["boom"], "tense"),
    (sc_led, dict(lines=("FASE 2", "CICLO DE CALVIN")), [("FASE DOS.", 1.2)], ["boom"], "tense"),
    (sc_calvin, dict(glucose=False), [("CON ESA ENERGÍA,", 1.0), ("ATRAPAS", 0.6), ("EL CO₂", 0.9)], [], "tense"),
    (sc_calvin, dict(glucose=True), [("Y FABRICAS", 0.7), ("*GLUCOSA.", 1.0), ("AZÚCAR.", 0.8), ("TU COMIDA.", 1.0)], ["chime"], "bright"),
    (F, closeup(day=2.0, expr="happy", arms="up", sun=(900, 330)), [("YA NO", 0.5), ("TIENES HAMBRE.", 1.2)], [], "bright"),
    (F, dict(day=1.6, z=(1.0, 1.12), f=(600, 1050), sun=(900, 330), figure="dark", fig_in=0.6, expr="neutral"),
     [("PERO ENTONCES,", 1.0), ("OYES", 0.5), ("UNA RESPIRACIÓN", 1.0), ("JUSTO DETRÁS", 0.8), ("DE TI.", 0.9)], ["heart"], "creepy"),
    (F, dict(day=1.6, z=(2.4, 2.6), f=(660, 920), figure="dark", expr="scared", look=0.4, blur=14, shake=0.5),
     [("ALGO", 0.5), ("ESTÁ RESPIRANDO", 1.0), ("TU *OXÍGENO.", 1.1)], ["heart", "boom"], "creepy"),
    (F, dict(day=2.0, z=(1.35, 1.45), f=(690, 1050), sun=(900, 330), figure="friend", o2=True, expr="smile", look=0.4),
     [("ES UN HUMANO.", 1.1), ("Y SIN TI,", 0.8), ("NO PODRÍA", 0.7), ("RESPIRAR.", 1.1)], ["chime"], "bright"),
    (sc_led, dict(lines=("6CO2 + 6H2O + LUZ", "= C6H12O6 + 6O2")),
     [("ESA ES", 0.6), ("LA *FOTOSÍNTESIS:", 1.1), ("LUZ, AGUA Y CO₂", 1.1), ("SE CONVIERTEN", 0.8), ("EN *GLUCOSA", 0.8), ("Y *OXÍGENO.", 1.1)],
     ["beep"], "bright"),
    (F, dict(day=2.0, z=(1.0, 1.04), f=(540, 1000), sun=(900, 330), tags=True, expr="neutral", arms="hips"),
     [("ENTONCES,", 0.8), ("¿QUÉ NECESITA", 0.9), ("UNA PLANTA", 0.7), ("PARA VIVIR?", 1.2)], ["whoosh"], "bright"),
    (F, closeup(day=2.0, expr="smile", z=(3.2, 3.5), look=0.15), [("COMENTA", 0.7), ("1 O 2.", 1.6)], ["boom"], "bright"),
]

TIMELINE, TOTAL, NFRAMES = [], 0.0, 0


def build_timeline(shots):
    global TIMELINE, TOTAL, NFRAMES
    TIMELINE = []
    acc = 0.0
    for sh in shots:
        d = sum(dur for _, dur in sh[2])
        TIMELINE.append((acc, d, sh))
        acc += d
    TOTAL = acc
    NFRAMES = int(round(TOTAL * FPS))


build_timeline(SHOTS)


# ------------------------------------------------------------------ voz en off
VOICE_LEAD = 0.35      # segundos de imagen antes de que empiece la voz
VOICE_TAIL = 1.6       # segundos tras la última palabra


def syllables(txt):
    t = txt.lower().lstrip("*~")
    t = t.replace("co₂", " ce o dos ").replace("1 o 2", "uno o dos")
    t = re.sub(r"[^a-záéíóúüñ ]", " ", t)
    return max(1, len(re.findall(r"[aeiouáéíóúü]+", t)))


def speech_segments(path, thr="-35dB", min_sil=0.14):
    """Tramos con voz (inicio, fin) a partir de los silencios del audio."""
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                               capture_output=True, text=True).stdout)
    log = subprocess.run(["ffmpeg", "-i", path, "-af", f"silencedetect=n={thr}:d={min_sil}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", log)]
    en = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", log)]
    segs, cur = [], 0.0
    for s, e in zip(st, en):
        if s - cur > 0.05:
            segs.append([cur, s])
        cur = e
    if dur - cur > 0.05:
        segs.append([cur, dur])
    out = []
    for s in segs:  # descartar respiraciones y chasquidos muy cortos
        if s[1] - s[0] < 0.16:
            continue
        out.append(s)
    return out


def align_voice(segs):
    """Reparte los subtítulos (en orden) entre los tramos de voz según sus sílabas."""
    chunks = [txt for sh in SHOTS for txt, _ in sh[2]]
    syl = [syllables(c) for c in chunks]
    J, I = len(segs), len(chunks)
    speech = sum(b - a for a, b in segs)
    rate = speech / sum(syl)
    pre = [0]
    for s in syl:
        pre.append(pre[-1] + s)
    punct = [c.rstrip().endswith((".", ",", ":", "?", "!")) for c in chunks]
    INF = float("inf")
    dp = [[INF] * (I + 1) for _ in range(J + 1)]
    bk = [[None] * (I + 1) for _ in range(J + 1)]
    dp[0][0] = 0
    for j in range(1, J + 1):
        for g in range(1, 5):          # un grupo puede unir varios tramos de voz
            j0 = j - g
            if j0 < 0:
                break
            span = segs[j - 1][1] - segs[j0][0]
            gaps = span - sum(b - a for a, b in segs[j0:j])
            dur = span - 0.6 * gaps
            for i in range(1, I + 1):
                pen = 0 if (punct[i - 1] or i == I) else 0.5
                for a in range(max(0, i - 8), i):
                    if dp[j0][a] == INF:
                        continue
                    pred = rate * (pre[i] - pre[a])
                    cost = dp[j0][a] + ((dur - pred) / (pred + 0.4)) ** 2 + pen + 0.05 * (g - 1)
                    if cost < dp[j][i]:
                        dp[j][i], bk[j][i] = cost, (j0, a)
    i, j, bounds = I, J, []
    while j > 0:
        j0, a = bk[j][i]
        bounds.append((segs[j0][0], segs[j - 1][1], a, i))
        i, j = a, j0
    bounds.reverse()
    times, mapping = [0.0] * I, []
    for s0, s1, a, b in bounds:
        tot = pre[b] - pre[a]
        for k in range(a, b):
            times[k] = s0 + (s1 - s0) * (pre[k] - pre[a]) / tot
        mapping.append((s0, s1, chunks[a:b]))
    return times, mapping


def apply_voice(path):
    """Rehace el guion para que cortes y subtítulos sigan a la voz grabada."""
    segs = speech_segments(path)
    times, _ = align_voice(segs)
    end = segs[-1][1] + VOICE_TAIL
    starts = [VOICE_LEAD + t - 0.08 for t in times]
    starts[0] = 0.0
    ends = starts[1:] + [VOICE_LEAD + end]
    new, k = [], 0
    for fn, kw, caps, sfx, mood in SHOTS:
        nc = []
        for txt, _ in caps:
            nc.append((txt, ends[k] - starts[k]))
            k += 1
        new.append((fn, kw, nc, sfx, mood))
    build_timeline(new)


# ------------------------------------------------------------------ posproducción
_post = {}


def post_assets():
    if not _post:
        ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
        r = np.sqrt(((xs - W / 2) / (W * 0.62)) ** 2 + ((ys - H / 2) / (H * 0.62)) ** 2)
        _post["vig"] = (1 - 0.55 * np.clip((r - 0.55) / 0.6, 0, 1) ** 1.6)[..., None]
        rng = np.random.default_rng(1)
        _post["grain"] = [rng.normal(0, 5, (H, W, 1)).astype(np.float32) for _ in range(6)]
    return _post


def draw_caption(im, txt, tc):
    if not txt or txt.startswith("~"):
        return
    d = ImageDraw.Draw(im, "RGBA")
    words = txt.split(" ")
    pop = 0.86 + 0.14 * eo(prog(tc, 0, 0.12))
    size = 74 * pop
    f = font(size, "xb")
    plain = " ".join(w.lstrip("*") for w in words)
    lines, cur = [], []
    for w in words:
        test = " ".join(x.lstrip("*") for x in cur + [w])
        if f.getlength(test) > 940 and cur:
            lines.append(cur)
            cur = [w]
        else:
            cur.append(w)
    lines.append(cur)
    y = 1270 - (len(lines) - 1) * 44
    for ln in lines:
        full = " ".join(x.lstrip("*") for x in ln)
        x = W / 2 - f.getlength(full) / 2
        for w in ln:
            hl = w.startswith("*")
            ww = w.lstrip("*")
            d.text((x + 2, y + 7), ww, font=f, fill=(0, 0, 0, 120), anchor="lm", stroke_width=7, stroke_fill=(0, 0, 0, 120))
            d.text((x, y), ww, font=f, fill=(255, 214, 60) if hl else (255, 255, 255), anchor="lm",
                   stroke_width=6, stroke_fill=(0, 0, 0))
            x += f.getlength(ww + " ")
        y += 88
    _ = plain


def render(tg, frame_idx=0):
    for start, dur, (fn, kw, caps, _sfx, _m) in TIMELINE:
        if tg < start + dur or start == TIMELINE[-1][0]:
            t = tg - start
            c = Cv()
            fn(c, t, dur, **kw)
            if start == 0:
                c.cover((0, 0, 0), 1 - prog(t, 0, 0.6))
            if start == TIMELINE[-1][0]:
                c.cover((0, 0, 0), prog(t, dur - 0.5, 0.5))
            im = c.im.resize((W, H), Image.LANCZOS)
            pa = post_assets()
            arr = np.asarray(im, np.float32) * pa["vig"] + pa["grain"][frame_idx % 6]
            im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
            acc = 0.0
            for txt, cd in caps:
                if acc <= t < acc + cd:
                    draw_caption(im, txt, t - acc)
                acc += cd
            return im


def render_bytes(i):
    return render(i / FPS, i).tobytes()


# ------------------------------------------------------------------ audio
SR = 44100


def make_audio(path, voice=None):
    n = int(TOTAL * SR) + SR
    tt = np.arange(n) / SR
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    # capas de ambiente
    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * tt)
    dark = (np.sin(2 * np.pi * 55 * tt) + 0.6 * np.sin(2 * np.pi * 82.4 * tt) + 0.3 * np.sin(2 * np.pi * 110.3 * tt)) * lfo
    tense = (np.sin(2 * np.pi * 49 * tt) + 0.7 * np.sin(2 * np.pi * 51.9 * tt) + 0.15 * np.sin(2 * np.pi * 1244 * tt) * lfo)
    bright = np.zeros(n)
    chords = [[48, 55, 64, 71], [45, 52, 60, 67], [41, 48, 57, 64], [43, 50, 59, 62]]
    for k in range(int(TOTAL / 4) + 2):
        ch = chords[k % 4]
        s0 = int(k * 4 * SR)
        L = int(5.5 * SR)
        e = min(n, s0 + L)
        if s0 >= n:
            break
        tl = np.arange(e - s0) / SR
        env = np.minimum(1, tl / 1.0) * np.clip((5.5 - tl) / 1.5, 0, 1)
        bright[s0:e] += sum(np.sin(2 * np.pi * hz(m) * tl) for m in ch) * env * 0.5
        for j in range(8):
            m = ch[[1, 2, 3, 2][j % 4]] + 12
            p0 = s0 + int(j * 0.5 * SR)
            Lp = min(int(1.0 * SR), n - p0)
            if Lp <= 0:
                continue
            tp = np.arange(Lp) / SR
            bright[p0:p0 + Lp] += 0.45 * np.sin(2 * np.pi * hz(m) * tp) * np.exp(-tp * 5)
    gains = {"dark": (1, 0, 0), "creepy": (0.7, 0.6, 0), "tense": (0.35, 0.8, 0.25), "bright": (0.1, 0, 1)}
    g = np.zeros((n, 3))
    for start, dur, sh in TIMELINE:
        a, b = int(start * SR), int((start + dur) * SR)
        g[a:b] = gains[sh[4]]
    g[int(TOTAL * SR):] = g[int(TOTAL * SR) - 1]
    k = int(0.8 * SR)
    ker = np.ones(k) / k
    for i in range(3):
        g[:, i] = np.convolve(g[:, i], ker, mode="same")
    out = 0.10 * dark * g[:, 0] + 0.07 * tense * g[:, 1] + 0.05 * bright * g[:, 2]
    rng = np.random.default_rng(3)

    def add(at, sig):
        a = int(at * SR)
        e = min(n, a + len(sig))
        if a < n:
            out[a:e] += sig[: e - a]

    def noise(dur):
        return rng.normal(0, 1, int(dur * SR))

    def smooth(x, k):
        return np.convolve(x, np.ones(k) / k, mode="same")

    for start, dur, sh in TIMELINE:
        for fx in sh[3]:
            if fx == "whoosh":
                L = 0.6
                x = smooth(noise(L), 30)
                env = np.sin(np.pi * np.linspace(0, 1, len(x))) ** 2
                add(max(0, start - 0.25), 0.5 * x * env)
            elif fx == "boom":
                tl = np.arange(int(1.6 * SR)) / SR
                f = 70 * np.exp(-tl * 2) + 28
                add(start, 0.55 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tl * 2.2))
            elif fx in ("beep", "beep2"):
                tl = np.arange(int(0.12 * SR)) / SR
                add(start + (0.4 if fx == "beep2" else 0.05), 0.12 * np.sign(np.sin(2 * np.pi * 1000 * tl)) * np.exp(-tl * 20))
            elif fx in ("chime", "shine", "rise"):
                tl = np.arange(int(2.5 * SR)) / SR
                sig = sum(np.sin(2 * np.pi * hz(m) * tl) * np.exp(-tl * 1.8) for m in (84, 88, 91, 96)) * 0.06
                if fx == "rise":
                    sw = smooth(noise(2.0), 8) * np.linspace(0, 1, int(2.0 * SR)) ** 2 * 0.12
                    add(start, sw)
                    add(start + 1.6, sig)
                else:
                    add(start + 0.1, sig)
            elif fx == "scribble":
                x = smooth(noise(0.7), 4) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 7 * np.arange(int(0.7 * SR)) / SR)))
                add(start + 0.25, 0.08 * x)
            elif fx == "bubble":
                for j in range(8):
                    tl = np.arange(int(0.12 * SR)) / SR
                    f0 = 500 + 400 * rng.uniform()
                    add(start + 0.3 + j * 0.3, 0.07 * np.sin(2 * np.pi * (f0 + 3000 * tl) * tl) * np.exp(-tl * 30))
            elif fx == "door":
                x = smooth(noise(1.0), 60) * np.linspace(1, 0, int(1.0 * SR))
                add(start + 0.1, 0.5 * x)
            elif fx == "heart":
                for j in range(int(dur / 0.85)):
                    for off, amp in ((0, 0.5), (0.18, 0.35)):
                        tl = np.arange(int(0.18 * SR)) / SR
                        add(start + j * 0.85 + off, amp * np.sin(2 * np.pi * 50 * tl) * np.exp(-tl * 22))
    out[: int(0.6 * SR)] *= np.linspace(0, 1, int(0.6 * SR))
    end = int(TOTAL * SR)
    out[end - SR:end] *= np.linspace(1, 0, SR)
    out[end:] = 0
    out = out / max(1e-9, np.abs(out).max()) * 0.8
    if voice:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", voice, "-af",
                              "highpass=f=80,acompressor=threshold=-22dB:ratio=3:attack=5:release=120",
                              "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
        v = np.frombuffer(raw, np.float32).astype(np.float64)
        v = v / max(1e-9, np.abs(v).max()) * 0.95
        vt = np.zeros(n)
        a = int(VOICE_LEAD * SR)
        e = min(n, a + len(v))
        vt[a:e] = v[: e - a]
        env = np.convolve(np.abs(vt), np.ones(int(0.3 * SR)) / (0.3 * SR), mode="same")
        env = np.clip(env / max(1e-9, env.max()) * 4, 0, 1)
        out = out * 0.45 * (1 - 0.55 * env) + vt
        out = out / max(1e-9, np.abs(out).max()) * 0.95
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((out * 32767).astype(np.int16).tobytes())


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", type=float, nargs="*")
    ap.add_argument("--out", default=os.path.join(AQUI, "fotosintesis_vertical.mp4"))
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--voz", default=os.path.join(AQUI, "voz.mp3"),
                    help="audio con la narración (si no existe, el vídeo va sin voz)")
    args = ap.parse_args()
    voice = args.voz if args.voz and os.path.exists(args.voz) else None
    if voice:
        apply_voice(voice)
        print(f"Sincronizado con la voz: {voice} ({TOTAL:.1f} s)")
    if args.preview is not None:
        for s in args.preview:
            render(s).save(f"v_{s:05.1f}.png")
        print("duración total:", round(TOTAL, 1), "s")
        return
    audio = args.out + ".wav"
    make_audio(audio, voice)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", audio, "-vf", "hqdn3d=3:3:8:8",
           "-c:v", "libx264", "-preset", "slow", "-crf", "23",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", args.out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    import multiprocessing as mp
    with mp.get_context("fork").Pool(args.workers) as pool:
        for i, fr in enumerate(pool.imap(render_bytes, range(NFRAMES), chunksize=2)):
            ff.stdin.write(fr)
            if i % (FPS * 5) == 0:
                print(f"{i / FPS:5.1f}s / {TOTAL:.1f}s", flush=True)
    ff.stdin.close()
    ff.wait()
    os.remove(audio)
    print("Listo:", args.out)


if __name__ == "__main__":
    sys.exit(main())
