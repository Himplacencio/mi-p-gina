#!/usr/bin/env python3
"""Prueba automática de la ISO de MoonOS en QEMU.

Se conecta a la consola serie de la máquina virtual, espera el arranque,
inicia sesión como "liveuser" (sin contraseña en el modo Live) y ejecuta
comprobaciones. Guarda todo lo que sale por la consola en un archivo.

Uso: moonos-vm-test.py <socket-serie> <archivo-log>
"""
import socket
import sys
import time

sock_path, log_path = sys.argv[1], sys.argv[2]
mon_path = sys.argv[3] if len(sys.argv) > 3 else None
log = open(log_path, "wb")
buf = b""


def connect():
    for _ in range(60):
        try:
            s = socket.socket(socket.AF_UNIX)
            s.connect(sock_path)
            s.settimeout(1)
            return s
        except OSError:
            time.sleep(1)
    sys.exit("No se pudo conectar a la consola serie")


s = connect()


def pump():
    global buf
    try:
        data = s.recv(65536)
    except socket.timeout:
        return
    if data:
        buf += data
        log.write(data)
        log.flush()


def wait_for(patterns, timeout):
    """Espera a que aparezca alguno de los textos. Devuelve el que apareció."""
    global buf
    end = time.time() + timeout
    while time.time() < end:
        pump()
        for p in patterns:
            i = buf.find(p)
            if i >= 0:
                buf = buf[i + len(p):]
                return p
    return None


def send(text):
    s.sendall(text.encode())


print("Esperando el arranque (hasta 8 minutos)...")
if not wait_for([b"login:"], 480):
    print("RESULTADO: la VM no llegó a la pantalla de login por consola")
    sys.exit(0)
print("Login por consola disponible")

logged = False
for attempt in range(6):
    time.sleep(5)
    send("liveuser\r")
    r = wait_for([b"$ ", b"Password:", b"Login incorrect", b"login:"], 40)
    if r == b"Password:":
        send("\r")
        r = wait_for([b"$ ", b"Login incorrect", b"login:"], 30)
    if r == b"$ ":
        logged = True
        break
    print(f"Intento de login {attempt + 1} sin éxito ({r}), reintentando...")

if not logged:
    print("RESULTADO: no se pudo iniciar sesión como liveuser")
    sys.exit(0)

print("Sesión iniciada. Esperando 60 s a que el escritorio termine de cargar...")
end = time.time() + 60
while time.time() < end:
    pump()

checks = r"""
export TERM=dumb PAGER=cat SYSTEMD_PAGER=cat
echo ===MOONOS-TEST-START===
echo '--- Sistema'; grep -E '^(NAME|PRETTY_NAME)=' /etc/os-release; uname -r
echo '--- Estado de systemd'; systemctl is-system-running
echo '--- Servicios con error'; systemctl --failed --no-legend --plain || true
echo '--- Sesiones gráficas'; loginctl list-sessions --no-legend; for id in $(loginctl list-sessions --no-legend | awk '{print $1}'); do loginctl show-session "$id" -p Name -p Type -p State; done
echo '--- Procesos del escritorio'; pgrep -a sddm | head -3; pgrep -a kwin_wayland | head -2; pgrep -a plasmashell || echo 'plasmashell NO está corriendo'
echo '--- Tiempo de arranque'; systemd-analyze; systemd-analyze blame --no-pager | head -8
echo '--- Diagnóstico pantalla negra'; sudo journalctl -b --no-pager -o short-monotonic | grep -iE 'sddm|kwin|plasma|portal|timed out|timeout|failed|kwallet|polkit' | head -60; systemctl --user --no-pager --failed; systemd-analyze --user blame --no-pager | head -12
echo '--- Bienvenida y fondo animado'; pgrep -af moonos-bienvenida || echo 'bienvenida NO está abierta'; ls /usr/share/plasma/wallpapers/ | grep -i moonos
echo '--- Paneles de Plasma'; export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus; ls ~/.config/moonos-user-setup-done 2>&1; busctl --user call org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell evaluateScript s 'print(JSON.stringify(panels().map(function(p){return {lugar:p.location,alto:p.height,flota:p.floating,widgets:p.widgets().map(function(w){return w.type})}})));print(JSON.stringify(desktops().map(function(d){return d.widgets().map(function(w){return w.type})})))' 2>&1 | head -c 1500; echo
sudo journalctl -b --no-pager -o cat | grep -iE 'moonos-user-setup|evaluateScript|plasmashell.*(error|warn).*(panel|script|qml)' | tail -15
pkill -f moonos-bienvenida; sleep 3
echo '--- Detalle de paneles'; busctl --user call org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell evaluateScript s 'panels().forEach(function(p){var o={lugar:p.location,alto:p.height,hiding:p.hiding,largo:p.lengthMode,alin:p.alignment,flota:p.floating,opac:p.opacity,min:p.minimumLength,max:p.maximumLength,len:p.length,off:p.offset,pantalla:p.screen};p.widgets().forEach(function(w){if(w.type.indexOf("tasks")>0){w.currentConfigGroup=["General"];o.launchers=String(w.readConfig("launchers","?"));o.geom=JSON.stringify(w.geometry);print("DOCK-ANCHO="+Math.round(p.length)+" ")}});print(JSON.stringify(o))})' 2>&1 | head -c 2500; echo
echo '--- plasmashell en el journal'; journalctl --user -b --no-pager -o cat 2>/dev/null | grep -iE 'plasmashell|panel|tasks|launcher' | grep -viE 'kf.svg|icon' | tail -30
echo '--- fastfetch'; fastfetch --pipe true -s OS:Kernel:Memory 2>&1 | head -20
echo '--- Memoria (MiB)'; free -m
echo '--- Kernel y tarjeta gráfica'; lspci -k | grep -A3 -Ei 'vga|3d' | head -8
echo '--- Modo juego'; head -20 /etc/gamemode.ini; ls -l /usr/local/share/applications/steam.desktop && grep '^Exec' /usr/local/share/applications/steam.desktop
echo '--- Instalador'; ls /etc/calamares /etc/calamares/modules | head -40; command -v calamares
echo '--- Paquetes clave'; pacman -Q linux-cachyos plasma-workspace steam gamemode chwd cachyos-calamares 2>&1
echo '--- Errores del arranque'; sudo journalctl -b -p err --no-pager | tail -40
echo ===MOONOS-TEST-$((1+1))-END===
"""
for line in checks.strip().splitlines():
    send(line + "\r")
    time.sleep(0.3)

if wait_for([b"===MOONOS-TEST-2-END==="], 180):
    print("RESULTADO: comprobaciones completadas")
else:
    print("RESULTADO: las comprobaciones no terminaron a tiempo")
def shot(name):
    if not mon_path:
        return
    m = socket.socket(socket.AF_UNIX)
    m.connect(mon_path)
    time.sleep(0.5)
    m.sendall(f"screendump /tmp/vm/{name}.ppm\n".encode())
    time.sleep(2)
    m.close()


def run(cmd, wait=6):
    send(cmd + "\r")
    end = time.time() + wait
    while time.time() < end:
        pump()


end = time.time() + 3
while time.time() < end:
    pump()
