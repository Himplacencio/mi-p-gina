#!/usr/bin/env python3
"""Graba la pantalla de la máquina virtual de MoonOS.

Pide a QEMU una captura de pantalla (screendump) cada ~0,2 s por su socket
de monitor y guarda la hora real de cada una, para montar después un video
en tiempo real y sin cortes.

Modos:
  arranque  graba desde que se enciende hasta el final (y abre el menú al final)
  terminal  espera al escritorio, abre Konsole y escribe «fastfetch» y
            «free -h» tecla por tecla; solo graba esa parte

Uso: grabar-arranque.py <socket-monitor> <carpeta-salida> <segundos> [modo]
"""
import json
import os
import socket
import sys
import time

sock_path, out_dir, total = sys.argv[1], sys.argv[2], float(sys.argv[3])
mode = sys.argv[4] if len(sys.argv) > 4 else "arranque"
os.makedirs(out_dir, exist_ok=True)

s = socket.socket(socket.AF_UNIX)
for _ in range(100):
    try:
        s.connect(sock_path)
        break
    except OSError:
        time.sleep(0.1)
s.settimeout(2)


def cmd(c):
    s.sendall((c + "\n").encode())
    try:
        s.recv(65536)
    except socket.timeout:
        pass


# La VM usa teclado latinoamericano: el guion está donde en EE. UU. va «/»
KEYS = {" ": "spc", "-": "slash", "\n": "ret", ".": "dot"}


def type_text(text, start, gap=0.13):
    """Devuelve acciones (segundo, tecla) para escribir el texto como una persona."""
    out, t = [], start
    for ch in text:
        out.append((t, KEYS.get(ch, ch)))
        t += gap + (0.08 if ch == " " else 0)
    return out, t


try:
    s.recv(65536)  # saludo de QEMU
except socket.timeout:
    pass

if mode == "terminal":
    # Plasma tarda ~70 s en la VM; se empieza a grabar con el escritorio listo
    rec_from = 86.0
    actions = [(87.0, "ctrl-alt-t"), (90.5, "meta_l-pgup")]        # abrir Konsole y maximizarla
    actions += [(92.0 + i * 0.35, "ctrl-kp_add") for i in range(3)]  # letra más grande
    a, t = type_text("fastfetch\n", 95.0); actions += a
    a, t = type_text("free -h\n", t + 4.5); actions += a
    total = max(total, t + 6.0)
else:
    rec_from = 0.0
    actions = [(total - 9, "meta_l"), (total - 4, "esc")]  # abrir y cerrar el menú al final

frames = []
t0 = time.time()
while (now := time.time() - t0) < total:
    while actions and actions[0][0] <= now:
        cmd(f"sendkey {actions.pop(0)[1]}")
    if now >= rec_from:
        name = f"f_{len(frames):05d}.ppm"
        cmd(f"screendump {out_dir}/{name}")
        frames.append({"file": name, "t": round(now - rec_from, 3)})
        time.sleep(0.12)
    else:
        time.sleep(0.05)

json.dump({"frames": frames, "duracion": total - rec_from, "modo": mode}, open(f"{out_dir}/frames.json", "w"))
print(f"{len(frames)} capturas en {total - rec_from:.0f} s (modo {mode})")
