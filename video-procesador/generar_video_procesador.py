#!/usr/bin/env python3
"""
«¿Qué hace el procesador?»: vídeo vertical (9:16) para niños, pensado para
mantener la atención (TDAH): una idea por pantalla, cortes rápidos, colores
vivos, marcador «PARTE X DE 7», comparaciones cotidianas, resumen y pregunta.

Reutiliza el motor de dibujo, subtítulos y audio de
../video-fotosintesis/generar_video_vertical.py

Uso:
    python3 generar_video_procesador.py                  # crea procesador.mp4
    python3 generar_video_procesador.py --preview 3 20   # guarda esos segundos como PNG
    python3 generar_video_procesador.py --voz voz.mp3    # sincroniza con una narración
"""
import argparse
import math
import os
import random
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "video-fotosintesis"))
import generar_video_vertical as g  # noqa: E402
from generar_video_vertical import (Cv, back, clamp, eio, eo, face, lerp, lerp2, lerpc, mannequin,  # noqa: E402
                                    prog, tag, vgrad, W, H, FPS)

WHITE, INK = (255, 255, 255), (25, 25, 35)
GOLDPIN = (225, 185, 80)
PARTS = 7
BGS = {0: ((70, 50, 160), (30, 140, 220)), 1: ((255, 105, 90), (255, 175, 70)), 2: ((12, 18, 40), (25, 60, 110)),
       3: ((30, 165, 120), (20, 105, 165)), 4: ((255, 165, 40), (235, 85, 60)), 5: ((85, 85, 215), (155, 85, 215)),
       6: ((140, 55, 195), (235, 85, 155)), 7: ((220, 55, 50), (250, 145, 45)), 8: ((35, 35, 65), (70, 55, 135))}
TITLES = {1: "¿QUÉ HACE?", 2: "INTERRUPTORES", 3: "NÚCLEOS", 4: "EL RELOJ", 5: "MEMORIA", 6: "EL GPU", 7: "CALOR"}
ACCENT = [(255, 214, 60), (90, 200, 255), (120, 230, 120), (255, 130, 180), (255, 160, 60), (190, 140, 255), (255, 90, 90)]


# ------------------------------------------------------------------ piezas comunes
def bg(c, t, k):
    top, bot = BGS[k]
    c.im.paste(vgrad([(0, top), (1, bot)]))
    rnd = random.Random(k + 1)
    for i in range(16):
        x = rnd.uniform(0, W)
        y = (rnd.uniform(0, H + 200) - t * rnd.uniform(20, 60)) % (H + 200) - 100
        r = rnd.uniform(18, 60)
        if i % 3 == 0:
            c.line([(x - r, y), (x + r, y)], WHITE, 10, 0.12)
            c.line([(x, y - r), (x, y + r)], WHITE, 10, 0.12)
        elif i % 3 == 1:
            c.circle((x, y), r, None, 0.13, outline=WHITE, width=8)
        else:
            c.circle((x, y), r * 0.6, WHITE, 0.10)


def badge(c, t, n):
    """Marcador de progreso «PARTE n DE 7» con puntos."""
    if not n:
        return
    txt = f"PARTE {n} DE {PARTS} · {TITLES[n]}"
    w = g.font(36 * g.S, "xb").getlength(txt) / g.S + 70
    c.rrect((540 - w / 2 + 5, 72 + 7), (540 + w / 2 + 5, 148 + 7), 38, (0, 0, 0), 0.25)
    c.rrect((540 - w / 2, 72), (540 + w / 2, 148), 38, WHITE, 0.95)
    c.text((540, 111), txt, 36, INK, 1, "xb")
    for k in range(PARTS):
        x = 540 + (k - (PARTS - 1) / 2) * 46
        if k + 1 < n:
            c.circle((x, 190), 11, WHITE, 0.95)
        elif k + 1 == n:
            c.circle((x, 190), 15 + 3 * math.sin(t * 8), ACCENT[(n - 1) % 7], 1, outline=WHITE, width=4)
        else:
            c.circle((x, 190), 10, None, 0.7, outline=WHITE, width=3)


def chip(c, p, s=1.0, t=0.0, body=(45, 50, 72), label="CPU", expr="smile", heat=0.0, glow=0.0, look=0,
         showface=True, a=1.0):
    x, y = p
    h = 150 * s
    if glow > 0:
        c.glow(p, h * 1.25, (255, 240, 150), glow, 4)
    c.rrect((x - h + 14 * s, y - h + 20 * s), (x + h + 14 * s, y + h + 20 * s), 36 * s, (0, 0, 0), 0.25 * a)
    n = 7
    for k in range(n):
        off = (k - (n - 1) / 2) * h * 2 / (n + 0.6)
        c.rrect((x + off - 8 * s, y - h - 34 * s), (x + off + 8 * s, y + h + 34 * s), 5 * s, GOLDPIN, a)
        c.rrect((x - h - 34 * s, y + off - 8 * s), (x + h + 34 * s, y + off + 8 * s), 5 * s, GOLDPIN, a)
    bcol = lerpc(body, (205, 50, 40), heat)
    c.rrect((x - h, y - h), (x + h, y + h), 34 * s, bcol, a)
    c.rrect((x - h + 10 * s, y - h + 8 * s), (x + h - 10 * s, y + h - 16 * s), 28 * s, lerpc(bcol, WHITE, 0.12), a)
    d = h * 0.64
    c.rrect((x - d, y - d - 14 * s), (x + d, y + d - 14 * s), 20 * s, lerpc((195, 200, 212), (255, 170, 150), heat), a)
    c.rrect((x - d + 10 * s, y - d - 6 * s), (x + d - 6 * s, y + d - 20 * s), 16 * s, lerpc((225, 228, 238), (255, 200, 185), heat), a)
    if showface:
        face(c, (x, y - 12 * s), d * 0.95, expr, look, t, a)
    if label:
        c.text((x, y + h - 24 * s), label, 26 * s, (235, 235, 245), a, "xb")
    if heat > 0.05:
        for k in range(3):
            xx = x + (k - 1) * 90 * s
            ph = (t * 1.2 + k * 0.33) % 1
            pts = [(xx + 14 * s * math.sin(v * 0.12 + t * 6), y - h - 60 * s - v * s - ph * 120 * s) for v in range(0, 140, 10)]
            c.line(pts, (255, 140, 60), 9 * s, heat * (1 - ph))
        for k in range(2):
            ph = (t * 0.9 + k * 0.5) % 1
            dx = x + (1 if k else -1) * d * 0.9
            c.circle((dx, y - d * 0.4 + ph * 80 * s), 12 * s, (110, 190, 255), heat * (1 - ph))
            c.poly([(dx, y - d * 0.4 + ph * 80 * s - 26 * s), (dx - 11 * s, y - d * 0.4 + ph * 80 * s - 4 * s),
                    (dx + 11 * s, y - d * 0.4 + ph * 80 * s - 4 * s)], (110, 190, 255), heat * (1 - ph))


def sparkles(c, t, p, r, n=8, col=(255, 240, 150), a=1):
    for k in range(n):
        ang = k * 2 * math.pi / n + t * 0.8
        rr = r * (1 + 0.12 * math.sin(t * 5 + k))
        q = (p[0] + math.cos(ang) * rr, p[1] + math.sin(ang) * rr)
        sz = 16 + 8 * math.sin(t * 7 + k * 2)
        c.poly([(q[0], q[1] - sz), (q[0] + sz * 0.3, q[1] - sz * 0.3), (q[0] + sz, q[1]), (q[0] + sz * 0.3, q[1] + sz * 0.3),
                (q[0], q[1] + sz), (q[0] - sz * 0.3, q[1] + sz * 0.3), (q[0] - sz, q[1]), (q[0] - sz * 0.3, q[1] - sz * 0.3)], col, a)


# ---- iconos sencillos
def icon(c, kind, p, s=1.0, a=1.0):
    x, y = p
    if kind == "camera":
        c.rrect((x - 55 * s, y - 35 * s), (x + 55 * s, y + 40 * s), 14 * s, (60, 64, 80), a)
        c.rrect((x - 22 * s, y - 50 * s), (x + 18 * s, y - 30 * s), 6 * s, (60, 64, 80), a)
        c.circle((x, y + 3 * s), 27 * s, (200, 220, 255), a, outline=(30, 30, 40), width=7 * s)
        c.circle((x - 8 * s, y - 5 * s), 7 * s, WHITE, a)
    elif kind == "note":
        c.ellipse((x - 22 * s, y + 35 * s), 24 * s, 18 * s, (40, 40, 60), a)
        c.line([(x, y + 32 * s), (x, y - 45 * s)], (40, 40, 60), 10 * s, a)
        c.poly([(x, y - 48 * s), (x + 40 * s, y - 30 * s), (x + 40 * s, y - 12 * s), (x, y - 28 * s)], (40, 40, 60), a)
    elif kind == "game":
        c.rrect((x - 62 * s, y - 32 * s), (x + 62 * s, y + 32 * s), 32 * s, (70, 70, 95), a)
        c.line([(x - 40 * s, y), (x - 16 * s, y)], WHITE, 9 * s, a)
        c.line([(x - 28 * s, y - 12 * s), (x - 28 * s, y + 12 * s)], WHITE, 9 * s, a)
        c.circle((x + 26 * s, y - 8 * s), 9 * s, (255, 90, 90), a)
        c.circle((x + 42 * s, y + 8 * s), 9 * s, (90, 200, 255), a)
    elif kind == "screen":
        c.rrect((x - 34 * s, y - 58 * s), (x + 34 * s, y + 58 * s), 12 * s, (40, 40, 55), a)
        c.rrect((x - 27 * s, y - 48 * s), (x + 27 * s, y + 46 * s), 7 * s, (90, 180, 255), a)
    elif kind == "chat":
        c.rrect((x - 55 * s, y - 40 * s), (x + 55 * s, y + 28 * s), 24 * s, (80, 200, 120), a)
        c.poly([(x - 25 * s, y + 25 * s), (x - 40 * s, y + 52 * s), (x - 5 * s, y + 25 * s)], (80, 200, 120), a)
        for k in (-1, 0, 1):
            c.circle((x + k * 24 * s, y - 6 * s), 7 * s, WHITE, a)
    elif kind == "pin":
        c.circle((x, y - 15 * s), 34 * s, (240, 80, 80), a)
        c.poly([(x - 30 * s, y - 2 * s), (x + 30 * s, y - 2 * s), (x, y + 52 * s)], (240, 80, 80), a)
        c.circle((x, y - 15 * s), 13 * s, WHITE, a)
    elif kind == "mail":
        c.rrect((x - 55 * s, y - 36 * s), (x + 55 * s, y + 36 * s), 8 * s, (255, 210, 80), a)
        c.line([(x - 50 * s, y - 30 * s), (x, y + 5 * s), (x + 50 * s, y - 30 * s)], (180, 130, 30), 7 * s, a)
    elif kind == "play":
        c.rrect((x - 60 * s, y - 40 * s), (x + 60 * s, y + 40 * s), 18 * s, (240, 60, 60), a)
        c.poly([(x - 14 * s, y - 20 * s), (x + 22 * s, y), (x - 14 * s, y + 20 * s)], WHITE, a)


def phone(c, p, s=1.0, t=0.0, open_=0.0, tap=None, app=0.0, a=1.0):
    x, y = p
    w, h = 215 * s, 440 * s
    c.rrect((x - w + 16 * s, y - h + 22 * s), (x + w + 16 * s, y + h + 22 * s), 70 * s, (0, 0, 0), 0.3 * a)
    c.rrect((x - w, y - h), (x + w, y + h), 70 * s, (28, 28, 36), a)
    c.rrect((x + w - 4 * s, y - h * 0.5), (x + w + 8 * s, y - h * 0.3), 4 * s, (60, 60, 70), a)
    iw, ih = w - 18 * s, h - 18 * s
    # placa por dentro
    c.rrect((x - iw, y - ih), (x + iw, y + ih), 56 * s, (30, 120, 75), a)
    rnd = random.Random(2)
    for _ in range(18):
        x0 = x + rnd.uniform(-iw + 30 * s, iw - 30 * s)
        y0 = y + rnd.uniform(-ih + 40 * s, ih - 40 * s)
        x1 = x0 + rnd.choice([-1, 1]) * rnd.uniform(40, 120) * s
        c.line([(x0, y0), (x1, y0), (x1, y0 + rnd.uniform(-80, 80) * s)], (200, 190, 90), 4 * s, a * 0.8)
    for _ in range(9):
        q = (x + rnd.uniform(-iw + 50 * s, iw - 50 * s), y + rnd.uniform(-ih + 60 * s, ih - 60 * s))
        c.rrect((q[0] - 22 * s, q[1] - 14 * s), (q[0] + 22 * s, q[1] + 14 * s), 4 * s, (40, 40, 50), a)
    c.rrect((x - 120 * s, y + 170 * s), (x + 120 * s, y + 330 * s), 20 * s, (190, 195, 200), a)  # batería
    c.text((x, y + 250 * s), "BATERÍA", 26 * s, (90, 95, 100), a, "xb")
    chip(c, (x, y - 110 * s), 0.62 * s, t, glow=0.5 * open_, a=a)
    # pantalla (se desliza al «abrir»)
    if open_ < 1:
        oy = -open_ * h * 2.4
        sa = a * (1 - eo(open_))
        c.rrect((x - iw, y - ih + oy), (x + iw, y + ih + oy), 56 * s, (22, 28, 60), sa)
        c.circle((x - 60 * s, y - 200 * s + oy), 160 * s, (90, 60, 200), sa * 0.6)
        c.circle((x + 90 * s, y + 160 * s + oy), 190 * s, (30, 140, 220), sa * 0.5)
        cols = [(255, 90, 90), (255, 200, 60), (80, 200, 120), (90, 160, 255), (190, 110, 255), (255, 140, 60)]
        for i in range(4):
            for j in range(5):
                q = (x + (i - 1.5) * 92 * s, y - 280 * s + j * 120 * s + oy)
                c.rrect((q[0] - 34 * s, q[1] - 34 * s), (q[0] + 34 * s, q[1] + 34 * s), 18 * s, cols[(i + j * 3) % 6], sa)
        cam = (x + 0.5 * 92 * s, y - 280 * s + 2 * 120 * s + oy)
        c.rrect((cam[0] - 34 * s, cam[1] - 34 * s), (cam[0] + 34 * s, cam[1] + 34 * s), 18 * s, (60, 64, 80), sa)
        c.circle(cam, 16 * s, (200, 220, 255), sa, outline=WHITE, width=4 * s)
        c.rrect((x - 60 * s, y - ih + 14 * s + oy), (x + 60 * s, y - ih + 40 * s + oy), 13 * s, (10, 10, 14), sa)
        if tap is not None and tap > 0:
            c.circle(cam, 40 * s + tap * 80 * s, None, (1 - tap) * sa, outline=WHITE, width=6 * s)
        if app > 0:
            c.rrect((x - iw, y - ih), (x + iw, y + ih), 56 * s, (15, 15, 20), a * app)
            c.rrect((x - iw + 20 * s, y - ih + 90 * s), (x + iw - 20 * s, y + ih - 220 * s), 20 * s, (120, 190, 240), a * app)
            c.circle((x, y + ih - 110 * s), 52 * s, WHITE, a * app, outline=(160, 160, 170), width=8 * s)
        return cam


def finger(c, p, a=1.0):
    x, y = p
    c.capsule((x + 10, y + 30), (x + 60, y + 330), 42, (240, 190, 160), a, 0.25)
    c.ellipse((x + 2, y + 10), 22, 14, (255, 225, 210), a * 0.8)


# ------------------------------------------------------------------ escenas
def sc_phone(c, t, d, open_=(0.0, 0.0), z=(1.0, 1.0), f=(540, 760)):
    u = t / d
    bg(c, t, 0)
    c.cam(g.anim(z, u), *g.animp(f, u))
    pop = back(prog(t, 0, 0.45))
    o = lerp(open_[0], open_[1], eio(prog(t, 0.2, 0.9)))
    phone(c, (540, 760 + 6 * math.sin(t * 2)), 0.92 * (pop if open_[0] == 0 and open_[1] == 0 else 1), t, o)
    if open_[1] == 0:
        for k in range(5):
            ang = k * 1.25 + t * 0.6
            q = (540 + math.cos(ang) * 400, 700 + math.sin(ang) * 470)
            c.text(q, "?", 90, WHITE, 0.85 * eo(prog(t, 0.3 + k * 0.1, 0.3)), "xb", stroke=4, scol=(60, 40, 140))
    else:
        sparkles(c, t, (540, 658), 230, 8, a=prog(t, 0.8, 0.4))


def sc_chip_hero(c, t, d, cookie=False):
    bg(c, t, 0)
    if not cookie:
        s = 1.45 * back(prog(t, 0, 0.5))
        sparkles(c, t, (540, 640), 330, 10, a=eo(prog(t, 0.3, 0.4)))
        chip(c, (540, 640), s, t, glow=0.6, look=0.2 * math.sin(t * 2))
        a = eo(prog(t, 0.6, 0.4))
        c.text((540, 1030 + (1 - a) * 30), "PROCESADOR", 96, WHITE, a, "xb", stroke=6, scol=(40, 30, 110))
    else:
        chip(c, (300, 680), 0.62 * back(prog(t, 0, 0.4)), t, look=0.4)
        x, y, r = 760, 680, 200 * back(prog(t, 0.25, 0.4))
        c.circle((x + 10, y + 16), r, (0, 0, 0), 0.25)
        c.circle((x, y), r, (205, 145, 70))
        c.circle((x - r * 0.1, y - r * 0.1), r * 0.85, (225, 170, 95))
        rnd = random.Random(3)
        for _ in range(9):
            ang, rr = rnd.uniform(0, 6.28), r * math.sqrt(rnd.uniform(0.02, 0.6))
            c.ellipse((x + math.cos(ang) * rr, y + math.sin(ang) * rr), r * 0.11, r * 0.08, (85, 50, 30))
        c.text((530, 690), "<", 150, WHITE, eo(prog(t, 0.5, 0.3)), "xb", stroke=5, scol=(40, 30, 110))
        c.text((300, 930), "PROCESADOR", 40, WHITE, 1, "xb", stroke=3, scol=(40, 30, 110))
        c.text((760, 930), "GALLETA", 40, WHITE, 1, "xb", stroke=3, scol=(40, 30, 110))


def sc_orders(c, t, d):
    bg(c, t, 1)
    ctr = (540, 730)
    kinds = ["screen", "camera", "note", "game"]
    pos = [(250, 430), (830, 430), (250, 1050), (830, 1050)]
    for k, (kd, q) in enumerate(zip(kinds, pos)):
        c.line([ctr, q], WHITE, 6, 0.5)
        t0 = 0.9 + k * 0.45
        u = prog(t, t0, 0.35)
        if 0 < u < 1:
            c.glow(lerp2(ctr, q, u), 16, (255, 255, 200), 1, 3)
            c.circle(lerp2(ctr, q, u), 14, WHITE)
        hit = prog(t, t0 + 0.35, 0.25)
        sc = 1 + 0.25 * math.sin(math.pi * hit)
        if hit > 0:
            c.glow(q, 100, (255, 255, 220), 0.7, 3)
        c.circle((q[0] + 6, q[1] + 10), 105 * sc, (0, 0, 0), 0.2)
        c.circle(q, 105 * sc, WHITE, 0.96)
        icon(c, kd, q, 1.15 * sc)
    chip(c, ctr, 0.85 * back(prog(t, 0, 0.4)), t, glow=0.4, expr="smile" if t > 0.9 else "neutral")


def sc_tap(c, t, d):
    bg(c, t, 1)
    u = t / d
    pp, cp = (330, 760), (810, 640)
    wire = [(420, 760), (600, 760), (600, 640), (720, 640)]
    c.line(wire, (255, 240, 200), 10, 0.6)
    app = eo(prog(u, 0.8, 0.12))
    tapv = prog(u, 0.08, 0.15)
    cam = phone(c, pp, 0.62, t, 0, tap=tapv if tapv < 1 else None, app=app)
    fy = lerp(-120, 0, eio(prog(u, 0.0, 0.1))) + lerp(0, -260, eio(prog(u, 0.2, 0.12)))
    if u < 0.34:
        finger(c, (cam[0], cam[1] + fy))
    go = prog(u, 0.18, 0.18)
    if 0 < go < 1:
        c.glow(g.along(wire, go), 22, (255, 255, 160), 1, 3)
    think = 0.36 <= u < 0.66
    if think:
        gx, gy, rot = cp[0], cp[1] - 250, t * 4
        pts = []
        for k in range(16):
            ang = rot + k * math.pi / 8
            r = 70 if k % 2 == 0 else 52
            pts.append((gx + math.cos(ang) * r, gy + math.sin(ang) * r))
        c.poly(pts, (240, 240, 250))
        c.circle((gx, gy), 22, (255, 140, 80))
        c.text((gx + 120, gy - 50), "?", 70, WHITE, 1, "xb", stroke=4, scol=(150, 60, 40))
    back_ = prog(u, 0.66, 0.14)
    if 0 < back_ < 1:
        c.glow(g.along(wire[::-1], back_), 22, (160, 255, 200), 1, 3)
    chip(c, cp, 0.7, t, glow=0.6 if think else 0.2, expr="neutral" if think else "smile", look=-0.4 if u < 0.36 else 0)


def sc_switches(c, t, d, mode="grid"):
    bg(c, t, 2)
    if mode == "grid":
        chip(c, (540, 740), 2.4, t, showface=False, label="", a=0.35)
        ctr, R = (540, 720), 330 * eo(prog(t, 0, 0.5))
        c.circle(ctr, R + 26, (220, 225, 235))
        c.circle(ctr, R, (14, 22, 40))
        step = 46
        for i in range(-8, 9):
            for j in range(-8, 9):
                q = (ctr[0] + i * step, ctr[1] + j * step)
                if math.dist(q, ctr) > R - 26:
                    continue
                on = (hash((i, j, int(t * 7))) % 3) != 0
                c.rrect((q[0] - 15, q[1] - 15), (q[0] + 15, q[1] + 15), 6, (45, 55, 80))
                if on:
                    c.circle(q, 14, (90, 255, 170), 0.3)
                c.circle(q, 8, (90, 255, 170) if on else (30, 50, 50))
        c.capsule((ctr[0] + R * 0.72, ctr[1] + R * 0.72), (ctr[0] + R * 1.15, ctr[1] + R * 1.15), 30, (120, 80, 50))
        c.circle((ctr[0] - R * 0.45, ctr[1] - R * 0.5), R * 0.18, WHITE, 0.12)
    elif mode == "one":
        on = (t >= 2.2 and t < 3.3) or (t < 2.2 and int(t * 2.5) % 2 == 0)
        c.rrect((180, 470), (480, 1000), 40, (235, 238, 245))
        c.rrect((235, 560), (425, 910), 30, (190, 195, 210))
        lev = 590 if on else 880
        c.capsule((330, 735), (330, lev), 34, (60, 65, 80))
        c.ball((330, lev), 52, (255, 90, 90) if on else (120, 125, 140))
        c.text((330, 1060), "ON" if on else "OFF", 56, WHITE, 1, "xb", stroke=4, scol=INK)
        bx, by = 760, 600
        if on:
            c.glow((bx, by), 150, (255, 230, 100), 1, 5)
        c.circle((bx, by), 140, (255, 225, 90) if on else (110, 115, 130))
        c.rrect((bx - 70, by + 120), (bx + 70, by + 230), 20, (160, 165, 175))
        for k in range(3):
            c.line([(bx - 70, by + 150 + k * 28), (bx + 70, by + 150 + k * 28)], (120, 125, 135), 6, caps=False)
        c.text((bx, 960), "1" if on else "0", 210, (255, 225, 90) if on else (170, 180, 200), 1, "xb", stroke=6, scol=INK)
    else:
        rnd = random.Random(5)
        for col in range(14):
            x = 40 + col * 77
            sp = rnd.uniform(160, 320)
            off = rnd.uniform(0, 2000)
            for r in range(16):
                y = (off + t * sp + r * 90) % 2100 - 120
                ch = "1" if hash((col, r, int(t * 3))) % 2 else "0"
                c.text((x, y), ch, 50, (90, 255, 170), 0.25 + 0.6 * (r / 16), "xb")
        chip(c, (540, 700), 1.25 * back(prog(t, 0, 0.4)), t, glow=0.8, expr="happy")


CORE_COLS = [(255, 120, 120), (255, 190, 90), (120, 220, 130), (100, 180, 255), (190, 140, 255),
             (255, 140, 200), (90, 220, 220), (240, 230, 110)]
CORE_ICONS = ["note", "camera", "chat", "game", "pin", "mail", "play", "screen"]


def sc_cores(c, t, d, mode="reveal"):
    bg(c, t, 3)
    if mode == "reveal":
        chip(c, (540, 700), 2.2, t, showface=False, label="")
        for k in range(8):
            i, j = k % 2, k // 2
            q = (540 + (i - 0.5) * 190, 470 + j * 150)
            a = back(prog(t, 0.2 + k * 0.12, 0.3))
            c.rrect((q[0] - 80 * a, q[1] - 60 * a), (q[0] + 80 * a, q[1] + 60 * a), 16, CORE_COLS[k], min(1, a))
            c.text(q, str(k + 1), 56 * max(0.01, a), WHITE, min(1, a), "xb", stroke=3, scol=INK)
    elif mode == "one":
        c.rrect((190, 380), (890, 1120), 50, (255, 255, 255), 0.25)
        c.rrect((210, 400), (870, 1100), 44, CORE_COLS[3], 0.95)
        c.text((540, 460), "NÚCLEO 1", 48, WHITE, 1, "xb", stroke=3, scol=INK)
        mannequin(c, 540, 1060, 0.62, (245, 245, 250), "happy", "up", 0, t, sprout=False)
        q = (540, 560 + 10 * math.sin(t * 4))
        c.circle(q, 62, WHITE)
        icon(c, "note", q, 0.75)
    else:
        for k in range(8):
            i, j = k % 2, k // 2
            q = (540 + (i - 0.5) * 420, 330 + j * 225)
            a = eo(prog(t, k * 0.1, 0.3))
            c.rrect((q[0] - 195, q[1] - 100), (q[0] + 195, q[1] + 100), 30, CORE_COLS[k], a * 0.95)
            arms = "up" if (int(t * 3 + k) % 2) else "open"
            mannequin(c, q[0] - 80, q[1] + 92, 0.25, (245, 245, 250), "happy", arms, 0, t + k, sprout=False, a=a)
            ic = (q[0] + 85, q[1] + 6 * math.sin(t * 5 + k))
            c.circle(ic, 62, WHITE, a)
            icon(c, CORE_ICONS[k], ic, 0.7, a)


def sc_clock(c, t, d, mode="tick"):
    bg(c, t, 4)
    if mode == "tick":
        x, y = 540, 760
        c.poly([(x - 230, y + 330), (x + 230, y + 330), (x + 110, y - 330), (x - 110, y - 330)], (150, 90, 50))
        c.poly([(x - 180, y + 300), (x + 180, y + 300), (x + 85, y - 290), (x - 85, y - 290)], (190, 125, 70))
        ang = 32 * math.sin(2 * math.pi * t * 1.2)
        piv = (x, y + 250)
        tip = (piv[0] + 520 * math.sin(math.radians(ang)), piv[1] - 520 * math.cos(math.radians(ang)))
        c.capsule(piv, tip, 12, (230, 230, 235))
        wq = lerp2(piv, tip, 0.62)
        c.rrect((wq[0] - 45, wq[1] - 30), (wq[0] + 45, wq[1] + 30), 10, (255, 215, 80))
        c.ball(piv, 24, (90, 90, 100))
        ph = math.sin(2 * math.pi * t * 1.2)
        side = "TIC" if math.cos(2 * math.pi * t * 1.2) > 0 else "TAC"
        a = clamp(abs(ph) * 1.5 - 0.5)
        c.text((x + (-330 if side == "TIC" else 330), 420), side, 90, WHITE, a, "xb", stroke=5, scol=(150, 60, 30))
    elif mode == "count":
        for k in range(14):
            y = 300 + k * 70
            ph = (t * 2.5 + k * 0.37) % 1
            x0 = -200 + ph * 1500
            c.line([(x0, y), (x0 + 220, y)], WHITE, 6, 0.25)
        v = int(3_000_000_000 * eo(prog(t, 0.1, max(0.4, d - 0.6))))
        s = f"{v:,}".replace(",", ".")
        c.text((540, 640), s, 104, WHITE, 1, "xb", stroke=6, scol=(150, 60, 30))
        c.text((540, 760), "TICS EN 1 SEGUNDO", 44, (255, 240, 200), 1, "xb", stroke=3, scol=(150, 60, 30))
        a = eo(prog(t, d - 1.2, 0.4))
        c.rrect((330, 860), (750, 990), 65, WHITE, a)
        c.text((540, 926), "= 3 GHz", 72, (230, 90, 40), a, "xb")
    else:
        x, y = 540, 650
        lid = clamp(math.sin(math.pi * prog(t, 0.3, 0.6)))
        c.ellipse((x, y), 320, 200, WHITE, 1, outline=INK, width=12)
        c.circle((x + 20, y), 120, (70, 150, 230))
        c.circle((x + 20, y), 60, INK)
        c.circle((x - 10, y - 35), 22, WHITE)
        if lid > 0:
            c.poly([(x - 340, y - 220), (x + 340, y - 220), (x + 340, y - 220 + 420 * lid), (x - 340, y - 220 + 420 * lid)],
                   (255, 200, 150))
            c.line([(x - 320, y - 220 + 420 * lid), (x + 320, y - 220 + 420 * lid)], INK, 12)
        c.text((540, 360), "1 PARPADEO", 64, WHITE, 1, "xb", stroke=4, scol=(150, 60, 30))
        a = eo(prog(t, 0.6, 0.4))
        c.text((540, 960), "= 300 MILLONES", 70, (255, 240, 120), a, "xb", stroke=5, scol=(150, 60, 30))
        c.text((540, 1050), "DE TICS", 70, (255, 240, 120), a, "xb", stroke=5, scol=(150, 60, 30))


MEM = [("CACHÉ", "su bolsillo", 1.0, 0.15, "pocket"), ("RAM", "su mesa de trabajo", 0.7, 0.4, "table"),
       ("ALMACENAMIENTO", "su mochila", 0.25, 1.0, "bag")]


def mem_icon(c, kind, p, a=1.0):
    x, y = p
    if kind == "pocket":
        c.poly([(x - 60, y - 55), (x + 60, y - 55), (x + 55, y + 30), (x, y + 62), (x - 55, y + 30)], (60, 110, 200), a)
        c.line([(x - 50, y - 40), (x + 50, y - 40)], (250, 200, 90), 4, a)
        c.rrect((x - 20, y - 85), (x + 26, y - 40), 6, WHITE, a)
    elif kind == "table":
        c.rrect((x - 75, y - 25), (x + 75, y - 5), 6, (170, 110, 60), a)
        c.line([(x - 60, y - 5), (x - 60, y + 60)], (130, 80, 40), 12, a)
        c.line([(x + 60, y - 5), (x + 60, y + 60)], (130, 80, 40), 12, a)
        c.rrect((x - 40, y - 70), (x + 30, y - 25), 6, (60, 64, 80), a)
        c.rrect((x - 34, y - 64), (x + 24, y - 32), 4, (120, 190, 255), a)
    else:
        c.line([(x - 30, y - 62), (x - 30, y - 84), (x + 30, y - 84), (x + 30, y - 62)], (150, 40, 40), 10, a)
        c.rrect((x - 62, y - 65), (x + 62, y + 70), 34, (225, 70, 70), a)
        c.rrect((x - 42, y + 5), (x + 42, y + 55), 14, (190, 50, 50), a)
        c.line([(x - 42, y + 18), (x + 42, y + 18)], (255, 210, 90), 4, a)


def sc_memory(c, t, d, focus=0):
    bg(c, t, 5)
    for k, (title, sub, spd, size, kind) in enumerate(MEM):
        y0 = 290 + k * 300
        a = eo(prog(t, 0.2 + k * 0.35, 0.35)) if focus == 0 else (1 if focus == k + 1 else 0.4)
        off = (1 - eo(prog(t, 0.2 + k * 0.35, 0.35))) * 300 if focus == 0 else 0
        hl = focus == k + 1
        if hl:
            c.glow((540, y0 + 130), 330, (255, 240, 180), 0.5, 3)
        c.rrect((80 + off + 8, y0 + 12), (1000 + off + 8, y0 + 272), 40, (0, 0, 0), 0.2 * a)
        c.rrect((80 + off, y0), (1000 + off, y0 + 260), 40, WHITE, a, outline=ACCENT[k] if hl else None, width=10)
        c.circle((205 + off, y0 + 130), 100, lerpc(ACCENT[k], WHITE, 0.55), a)
        mem_icon(c, kind, (205 + off, y0 + 135), a)
        c.text((335 + off, y0 + 62), title, 48, INK, a, "xb", anchor="lm")
        c.text((335 + off, y0 + 108), sub, 32, (100, 100, 120), a, "semi", anchor="lm")
        for j, (lbl, v, col) in enumerate((("RAPIDEZ", spd, (90, 200, 120)), ("ESPACIO", size, (90, 150, 255)))):
            yy = y0 + 160 + j * 52
            c.text((335 + off, yy), lbl, 24, (120, 120, 140), a, "xb", anchor="lm")
            fill = v * (eo(prog(t, 0.5 + k * 0.35, 0.6)) if focus == 0 else 1)
            c.rrect((480 + off, yy - 14), (950 + off, yy + 14), 14, (230, 232, 240), a)
            c.rrect((480 + off, yy - 14), (480 + off + max(28, 470 * fill), yy + 14), 14, col, a)


def sc_gpu(c, t, d, mode="hello"):
    bg(c, t, 6)
    purple = (110, 55, 170)
    if mode == "hello":
        rnd = random.Random(4)
        for k in range(14):
            q = (rnd.uniform(100, 980), rnd.uniform(300, 1150))
            a = back(prog(t, k * 0.12, 0.3))
            c.circle(q, rnd.uniform(25, 60) * max(0.01, a), ACCENT[k % 7], min(1, a) * 0.9)
        p = (540, 690)
        chip(c, p, 1.3 * back(prog(t, 0, 0.45)), t, body=purple, label="GPU", glow=0.5)
        c.ellipse((p[0] - 30, p[1] - 245), 170, 50, (30, 30, 40))
        c.circle((p[0] - 30, p[1] - 300), 20, (30, 30, 40))
        ang = math.radians(35 + 18 * math.sin(t * 5))
        b0 = (p[0] + 300, p[1] + 80)
        b1 = (b0[0] + math.cos(ang) * 230, b0[1] - math.sin(ang) * 230)
        c.capsule(b0, b1, 16, (170, 110, 60))
        c.capsule(b1, (b1[0] + math.cos(ang) * 60, b1[1] - math.sin(ang) * 60), 22, (255, 90, 120))
    else:
        mx, my, mw, mh = 540, 690, 450, 300
        c.rrect((mx - mw - 26, my - mh - 26), (mx + mw + 26, my + mh + 26), 36, (30, 30, 40))
        c.rrect((mx - 60, my + mh + 26), (mx + 60, my + mh + 110), 10, (60, 60, 70))
        c.rrect((mx - 200, my + mh + 100), (mx + 200, my + mh + 130), 14, (60, 60, 70))
        if mode == "paint":
            cols_, rows_ = 24, 16
            cw, ch = 2 * mw / cols_, 2 * mh / rows_
            ph = (t * 1.6) % 1.0
            for i in range(cols_):
                for j in range(rows_):
                    if (i + j * 0.6) / (cols_ + rows_ * 0.6) > ph * 1.15:
                        continue
                    x, y = mx - mw + i * cw, my - mh + j * ch
                    u, v = i / cols_, j / rows_
                    if (u - 0.75) ** 2 + (v - 0.25) ** 2 < 0.012:
                        col = (255, 220, 70)
                    elif v > 0.68 + 0.08 * math.sin(u * 7):
                        col = (80, 190, 90)
                    else:
                        col = lerpc((90, 160, 255), (190, 225, 255), v)
                    c.rrect((x + 1, y + 1), (x + cw - 1, y + ch - 1), 3, col)
            n = int(t * 60) % 60 + 1
            c.text((540, 1110), f"DIBUJO Nº {n}", 56, WHITE, 1, "xb", stroke=4, scol=(90, 30, 120))
        else:
            c.rrect((mx - mw, my - mh), (mx + mw, my + mh), 14, (120, 200, 255))
            c.rrect((mx - mw, my + mh - 70), (mx + mw, my + mh), 0, (90, 190, 90))
            for k, (px, py, pw) in enumerate(((-250, 120, 120), (40, 40, 130), (300, -40, 110))):
                c.rrect((mx + px - pw, my + py), (mx + px + pw, my + py + 30), 10, (150, 100, 60))
            ph = (t * 0.55) % 1
            xs = lerp(-380, 380, ph)
            ys = my + mh - 110 - abs(math.sin(ph * math.pi * 3)) * 220
            for k in range(5):  # estela
                q = lerp(-380, 380, max(0, ph - k * 0.012))
                yk = my + mh - 110 - abs(math.sin(max(0, ph - k * 0.012) * math.pi * 3)) * 220
                c.circle((mx + q, yk), 34 - k * 4, WHITE, 0.15)
            c.ball((mx + xs, ys), 36, (255, 90, 90))
            for k in range(3):
                q = (mx - 250 + k * 280, my - 30 - k * 60)
                w = abs(math.cos(t * 4 + k)) * 22 + 3
                c.ellipse(q, w, 24, (255, 215, 60), 1, outline=(200, 150, 20), width=3)
            c.rrect((mx + mw - 170, my - mh + 20), (mx + mw - 20, my - mh + 80), 20, (20, 20, 30), 0.8)
            c.text((mx + mw - 95, my - mh + 51), "60 FPS", 30, (120, 255, 150), 1, "xb")


def sc_heat(c, t, d, mode="hot"):
    bg(c, t, 7)
    if mode == "hot":
        h = eo(prog(t, 0.2, 1.4))
        chip(c, (540, 650), 1.2, t, heat=h, expr="worried" if h > 0.4 else "neutral")
        x, y0, y1 = 920, 380, 900
        c.rrect((x - 34, y0), (x + 34, y1), 34, WHITE)
        lvl = lerp(y1 - 60, y0 + 40, h)
        c.rrect((x - 18, lvl), (x + 18, y1 - 30), 18, (230, 50, 40))
        c.circle((x, y1 + 20), 62, WHITE)
        c.circle((x, y1 + 20), 46, (230, 50, 40))
        pa = eo(prog(t, d * 0.55, 0.4))
        if pa > 0:
            c.glow((230, 1000), 150, (255, 120, 60), pa, 3)
            phone(c, (230, 1000), 0.35, t, 0, a=pa)
    else:
        fx, fy = 540, 560
        c.circle((fx, fy), 300, (60, 60, 75))
        c.circle((fx, fy), 270, (200, 230, 255))
        rot = t * 14
        for k in range(5):
            for ghost, al in ((0.12, 0.35), (0, 1)):
                ang = rot - ghost * 2 + k * 2 * math.pi / 5
                pts = [(fx, fy)]
                for v in range(9):
                    aa = ang + v * 0.09
                    rr = 250
                    pts.append((fx + math.cos(aa) * rr, fy + math.sin(aa) * rr))
                c.poly(pts, (90, 150, 230), al)
        c.circle((fx, fy), 60, (60, 60, 75))
        for k in range(6):
            ph = (t * 1.5 + k / 6) % 1
            x = 330 + k * 85
            pts = [(x + 20 * math.sin(v * 0.05 + t * 5), 880 + v - ph * 0) for v in range(0, 160, 20)]
            c.line(pts, WHITE, 6, 0.6 * (1 - ph) + 0.2)
        chip(c, (540, 1110), 0.75, t, expr="happy", body=(45, 80, 120))


RECAP = [("PROCESADOR = CEREBRO", ACCENT[0]), ("INTERRUPTORES: 0 Y 1", ACCENT[1]),
         ("NÚCLEOS = TRABAJADORES", ACCENT[2]), ("RELOJ = RITMO (GHz)", ACCENT[3]),
         ("MEMORIA: BOLSILLO, MESA, MOCHILA", ACCENT[4]), ("GPU = PINTOR", ACCENT[5]),
         ("MUCHO TRABAJO = CALOR", ACCENT[6])]


def sc_recap(c, t, d, times=()):
    bg(c, t, 8)
    c.text((540, 220), "RESUMEN", 96, (255, 214, 60), eo(prog(t, 0, 0.3)), "xb", stroke=5, scol=INK)
    for k, (txt, col) in enumerate(RECAP):
        t0 = times[k] if k < len(times) else 0.4 + k * 0.6
        a = eo(prog(t, t0, 0.25))
        if a <= 0:
            continue
        y = 360 + k * 118
        x = 80 + (1 - a) * 120
        c.rrect((x, y - 48), (1000, y + 48), 48, WHITE, a * 0.95)
        c.circle((x + 48, y), 36, col, a)
        c.line([(x + 32, y + 2), (x + 45, y + 15), (x + 66, y - 14)], WHITE, 9, a)
        size = 40 if len(txt) < 26 else 32
        c.text((x + 104, y + 2), txt, size, INK, a, "xb", anchor="lm")


def sc_quiz(c, t, d):
    bg(c, t, 0)
    chip(c, (290, 720), 0.75, t, label="CPU", look=0.4)
    chip(c, (790, 720), 0.75, t, body=(110, 55, 170), label="GPU", look=-0.4)
    tag(c, (150, 430), 1, "CPU", (60, 120, 230), eo(prog(t, 0.3, 0.3)), anchor=(290, 560))
    tag(c, (650, 430), 2, "GPU", (150, 70, 200), eo(prog(t, 0.6, 0.3)), anchor=(790, 560))
    c.text((540, 270 + 15 * math.sin(t * 5)), "?", 150, WHITE, 1, "xb", stroke=6, scol=INK)
    c.text((540, 1020), "¿QUIÉN PINTA LA PANTALLA?", 46, WHITE, 1, "xb", stroke=4, scol=INK)


def with_badge(fn, n):
    def run(c, t, d, **kw):
        fn(c, t, d, **kw)
        c.cam(1, W / 2, H / 2)
        badge(c, t, n)
    return run


# ------------------------------------------------------------------ guion
def S(fn, kw, caps, sfx=(), part=None):
    return (with_badge(fn, part) if part else fn, kw, caps, list(sfx), "fun")


RECAP_CAPS = [("~RESUMEN.", 1.0), ("~EL PROCESADOR ES EL CEREBRO.", 1.2), ("~TIENE INTERRUPTORES DE CERO Y UNO.", 1.2),
              ("~SUS NÚCLEOS SON TRABAJADORES.", 1.2), ("~SU RELOJ MARCA EL RITMO.", 1.2),
              ("~USA SU BOLSILLO, SU MESA Y SU MOCHILA.", 1.4), ("~EL GPU ES EL PINTOR.", 1.1),
              ("~Y MUCHO TRABAJO DA CALOR.", 1.4)]
RECAP_TIMES = [sum(dd for _, dd in RECAP_CAPS[:k + 1]) for k in range(7)]

SHOTS = [
    S(sc_phone, dict(), [("¿SABÍAS QUE", 0.9), ("TU CELULAR", 0.8), ("TIENE UN *CEREBRO?", 1.4)], ["whoosh"]),
    S(sc_phone, dict(open_=(0, 1), z=(1.0, 1.25), f=((540, 760), (540, 660))), [("¡MIRA ADENTRO!", 1.2), ("¡AQUÍ ESTÁ!", 1.1)], ["door"]),
    S(sc_chip_hero, dict(), [("SE LLAMA", 0.7), ("*PROCESADOR.", 1.2), ("O *CPU.", 1.0)], ["boom", "chime"]),
    S(sc_chip_hero, dict(cookie=True), [("ES MÁS PEQUEÑO", 0.9), ("QUE UNA GALLETA,", 1.1), ("¡PERO", 0.4), ("SÚPER LISTO!", 1.0)], ["pop"]),
    S(sc_orders, dict(), [("¿QUÉ HACE?", 1.0), ("DA *TODAS", 0.7), ("LAS ÓRDENES:", 0.9), ("PANTALLA, CÁMARA,", 0.9), ("MÚSICA, JUEGOS...", 1.1)], ["whoosh"], 1),
    S(sc_tap, dict(), [("TOCAS LA CÁMARA...", 1.2), ("EL CPU PIENSA...", 1.3), ("¡Y SE ABRE!", 1.2)], ["pop"], 1),
    S(sc_switches, dict(mode="grid"), [("POR DENTRO TIENE", 0.9), ("MILES DE MILLONES", 1.0), ("DE *INTERRUPTORES.", 1.3)], ["whoosh"], 2),
    S(sc_switches, dict(mode="one"), [("CADA UNO", 0.7), ("SOLO SABE", 0.7), ("DOS COSAS:", 0.8), ("*ENCENDIDO = 1", 1.1), ("*APAGADO = 0", 1.2)], ["pop"], 2),
    S(sc_switches, dict(mode="binary"), [("¡CON CEROS Y UNOS", 1.1), ("HACE *TODO!", 1.2)], ["chime"], 2),
    S(sc_cores, dict(mode="reveal"), [("TIENE *NÚCLEOS.", 1.2), ("¡COMO 8 CUARTITOS!", 1.2)], ["pop"], 3),
    S(sc_cores, dict(mode="one"), [("CADA NÚCLEO", 0.8), ("ES UN *TRABAJADOR", 1.1), ("QUE HACE UNA TAREA.", 1.1)], [], 3),
    S(sc_cores, dict(mode="eight"), [("MÁS TRABAJADORES...", 1.1), ("¡MÁS COSAS", 0.8), ("*A LA VEZ!", 1.2)], ["pop"], 3),
    S(sc_clock, dict(mode="tick"), [("TIENE UN *RELOJ", 1.1), ("QUE MARCA EL RITMO:", 1.1), ("TIC, TAC, TIC, TAC.", 1.4)], ["tick"], 4),
    S(sc_clock, dict(mode="count"), [("¡HACE TIC", 0.7), ("*3.000 MILLONES", 1.1), ("DE VECES", 0.6), ("POR SEGUNDO!", 1.3)], ["rise"], 4),
    S(sc_clock, dict(mode="blink"), [("¡MÁS RÁPIDO", 0.8), ("QUE UN PARPADEO!", 1.4)], ["boom"], 4),
    S(sc_memory, dict(focus=0), [("PARA TRABAJAR", 0.8), ("NECESITA *MEMORIA.", 1.1), ("TRES LUGARES:", 1.2)], ["whoosh"], 5),
    S(sc_memory, dict(focus=1), [("*CACHÉ:", 0.7), ("SU BOLSILLO.", 0.9), ("PEQUEÑA, PERO", 0.8), ("¡SÚPER RÁPIDA!", 1.1)], ["pop"], 5),
    S(sc_memory, dict(focus=2), [("*RAM:", 0.6), ("SU MESA.", 0.8), ("SE BORRA", 0.6), ("AL APAGAR.", 1.0)], ["pop"], 5),
    S(sc_memory, dict(focus=3), [("*ALMACENAMIENTO:", 1.1), ("SU MOCHILA.", 0.9), ("AQUÍ VIVEN", 0.7), ("TUS FOTOS Y JUEGOS.", 1.3)], ["pop"], 5),
    S(sc_gpu, dict(mode="hello"), [("SU AMIGO", 0.7), ("EL *GPU:", 1.0), ("¡EL PINTOR!", 1.1)], ["chime"], 6),
    S(sc_gpu, dict(mode="paint"), [("PINTA LA PANTALLA", 1.1), ("*60 VECES", 0.9), ("POR SEGUNDO.", 1.1)], ["pop"], 6),
    S(sc_gpu, dict(mode="game"), [("POR ESO", 0.5), ("LOS JUEGOS", 0.6), ("SE VEN", 0.5), ("¡TAN SUAVES!", 1.2)], [], 6),
    S(sc_heat, dict(mode="hot"), [("TANTO TRABAJO", 0.9), ("DA *CALOR.", 1.1), ("POR ESO TU CELULAR", 1.1), ("SE CALIENTA.", 1.1)], ["boom"], 7),
    S(sc_heat, dict(mode="fan"), [("LAS COMPUTADORAS", 1.0), ("USAN *VENTILADORES", 1.1), ("PARA ENFRIARLO.", 1.2)], ["whoosh"], 7),
    S(sc_recap, dict(times=RECAP_TIMES), RECAP_CAPS, ["chime"]),
    S(sc_quiz, dict(), [("PREGUNTA:", 0.8), ("¿QUIÉN PINTA", 0.8), ("LA PANTALLA?", 1.0), ("¿1 O 2?", 1.1), ("¡COMÉNTALO!", 1.6)], ["boom"]),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", type=float, nargs="*")
    ap.add_argument("--out", default=os.path.join(AQUI, "procesador.mp4"))
    ap.add_argument("--workers", type=int, default=os.cpu_count())
    ap.add_argument("--voz", default=os.path.join(AQUI, "voz.mp3"), help="narración opcional")
    args = ap.parse_args()
    g.SHOTS = SHOTS
    g.build_timeline(SHOTS)
    voice = args.voz if args.voz and os.path.exists(args.voz) else None
    if voice:
        g.apply_voice(voice)
        print(f"Sincronizado con la voz: {voice}")
    print(f"Duración: {g.TOTAL:.1f} s")
    if args.preview is not None:
        for s in args.preview:
            g.render(s).save(f"p_{s:05.1f}.png")
        return
    audio = args.out + ".wav"
    g.make_audio(audio, voice)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(FPS), "-i", "-", "-i", audio, "-vf", "hqdn3d=3:3:8:8", "-c:v", "libx264", "-preset", "slow",
           "-crf", "23", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart",
           args.out]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    import multiprocessing as mp
    with mp.get_context("fork").Pool(args.workers) as pool:
        for i, fr in enumerate(pool.imap(g.render_bytes, range(g.NFRAMES), chunksize=2)):
            ff.stdin.write(fr)
            if i % (FPS * 5) == 0:
                print(f"{i / FPS:5.1f}s / {g.TOTAL:.1f}s", flush=True)
    ff.stdin.close()
    ff.wait()
    os.remove(audio)
    print("Listo:", args.out)


if __name__ == "__main__":
    sys.exit(main())
