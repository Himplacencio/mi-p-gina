#!/usr/bin/env python3
"""Graba la pantalla de la máquina virtual mientras MoonOS arranca.

Pide a QEMU una captura de pantalla (screendump) cada ~0,2 s por su socket
de monitor y guarda la hora real de cada una, para montar después un video
en tiempo real y sin cortes.

Uso: grabar-arranque.py <socket-monitor> <carpeta-salida> <segundos>
"""
import json
import os
import socket
import sys
import time

sock_path, out_dir, total = sys.argv[1], sys.argv[2], float(sys.argv[3])
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


try:
    s.recv(65536)  # saludo de QEMU
except socket.timeout:
    pass

frames = []
t0 = time.time()
menu_abierto = menu_cerrado = False
while (now := time.time() - t0) < total:
    name = f"f_{len(frames):05d}.ppm"
    cmd(f"screendump {out_dir}/{name}")
    frames.append({"file": name, "t": round(time.time() - t0, 3)})
    # Ya en el escritorio: abrir y cerrar el menú para mostrar que responde
    if now > total - 9 and not menu_abierto:
        cmd("sendkey meta_l")
        menu_abierto = True
    if now > total - 4 and not menu_cerrado:
        cmd("sendkey esc")
        menu_cerrado = True
    time.sleep(0.15)

json.dump({"frames": frames, "duracion": total}, open(f"{out_dir}/frames.json", "w"))
print(f"{len(frames)} capturas en {total:.0f} s")
