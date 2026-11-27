"""Video 3 de MoonOS: «cómo va por dentro», con imágenes REALES del sistema.

Voz: voz-recorrido.mp3 (ElevenLabs). Grabaciones (workflow «Grabar el arranque de MoonOS»):
  arranque-real/terminal-antes.mp4  fastfetch de antes, con el logo de CachyOS
  arranque-real/terminal.mp4        fastfetch de ahora, con la luna de MoonOS, y free -h
  arranque-real/recorrido.mp4       pantalla de carga, Bienvenida, Hazlo tuyo, Tienda, escritorio y menú
Los tiempos dentro de cada grabación están en recorrido-tiempos.json.

Uso: python3 montar-recorrido-real.py [salida.mp4]
Requiere: ffmpeg, Pillow y Node con Playwright (Chromium).
"""
import json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
MK = os.path.join(HERE, '..')
REAL = os.path.join(MK, 'arranque-real')
WEB = os.path.join(HERE, 'web-capturas')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(MK, 'moonos-por-dentro-tiktok.mp4')
VOZ = os.path.join(HERE, 'voz-recorrido.mp3')
W, H, FPS = 1080, 1920, 30
TMP = tempfile.mkdtemp(prefix='recorrido-')

A = os.path.join(REAL, 'arranque-real.mp4')
R = os.path.join(REAL, 'recorrido.mp4')
T = os.path.join(REAL, 'terminal.mp4')
TA = os.path.join(REAL, 'terminal-antes.mp4')

# Tiempos de la grabación «recorrido» (segundos desde que empieza a grabar)
RT = json.load(open(os.path.join(HERE, 'recorrido-tiempos.json')))

# Planos: (inicio, fin, fuente, segundo de la fuente, (x, y, ancho, alto), zoom inicial, zoom final)
Z = RT['zonas']
SHOTS = [
    (0.00, 4.10, TA, RT['ta_fastfetch'], Z['ta_logo'], 1.00, 1.15),        # el logo de CachyOS de antes
    (4.10, 7.05, TA, RT['ta_fastfetch'] + 1, Z['ta_todo'], 1.15, 1.00),
    (7.05, 13.40, TA, RT['ta_fastfetch'] + 2, Z['ta_kernel'], 1.00, 1.15), # Kernel: linux-cachyos
    (13.40, 16.50, T, RT['t_fastfetch'], Z['t_logo'], 1.20, 1.00),         # la luna de MoonOS
    (16.50, 21.50, R, RT['splash'], Z['splash'], 1.00, 1.12),              # pantalla de carga
    (21.50, 23.85, R, RT['bienvenida'] + 0.5, Z['ventana'], 1.10, 1.00),
    (23.85, 26.30, R, RT['bienvenida'] + 3.0, Z['instalar'], 1.00, 1.10),
    (26.30, 28.95, R, RT['bienvenida'] + 5.5, Z['equipo'], 1.00, 1.10),
    (28.95, 35.05, R, RT['tuyo'] + 0.5, Z['ventana'], 1.00, 1.10),
    (35.05, 40.00, R, RT['tienda'] + 1.0, Z['tienda'], 1.00, 1.08),
    (40.00, 44.30, R, RT['comandos'] + 0.5, Z['tienda'], 1.08, 1.00),
    (44.30, 49.05, R, RT['escritorio'] + 1.0, Z['barra_musica'], 1.00, 1.15),
    (49.05, 50.70, R, RT['escritorio'] + 6.0, Z['dock'], 1.00, 1.15),
    (50.70, 53.35, R, RT['escritorio'] + 8.0, Z['luna'], 1.00, 1.12),
    (53.35, 57.55, T, RT['t_free'], Z['t_free'], 1.00, 1.15),
    (57.55, 63.79, R, RT['menu'] - 2.5, Z['completo'], 1.12, 1.00),
]
CAPTIONS = [
    (0.00, 4.10, 'me dijeron que moonos es solo<br>cachyos con otro nombre 🤨'),
    (4.10, 7.05, 'así que les muestro<br>cómo va por dentro 👀'),
    (7.05, 10.70, 'sí, está basado en cachyos<br>y no lo escondo'),
    (10.70, 13.40, 'es de lo más rápido<br>que hay en linux ⚡'),
    (13.40, 16.50, 'pero todo lo que van a ver<br>ahora lo hice yo'),
    (16.50, 21.50, 'al prenderlo ya no sale el logo<br>de nadie: sale la luna 🌙'),
    (21.50, 23.85, 'te recibe una bienvenida<br>en español 👋'),
    (23.85, 28.95, 'lo instalas con un botón<br>y ve qué tarjeta gráfica tienes'),
    (28.95, 35.05, '«hazlo tuyo»: colores, fondo<br>y estilo, sin cosas raras 🎨'),
    (35.05, 40.00, 'la tienda: spotify, discord,<br>steam… a un clic 🛍️'),
    (40.00, 44.30, 'y te explica los comandos<br>de la terminal con ejemplos 💻'),
    (44.30, 49.05, 'arriba tu música: la canción,<br>cuánto falta y los controles 🎵'),
    (49.05, 50.70, 'abajo, tus apps'),
    (50.70, 53.35, 'y de fondo una luna<br>que se mueve ✨'),
    (53.35, 57.55, 'todo esto usando apenas<br>1 giga de ram 🪶'),
    (57.55, 60.55, 'todavía falta, pero<br>cada semana avanza 🚀'),
    (60.55, 63.79, '¿qué le agregarían ustedes?<br>los leo en comentarios 👇'),
]
NOTAS = [
    (0.0, 13.40, 'grabación de antes · así se veía fastfetch hace unos días'),
    (13.40, 63.79, 'imágenes reales de MoonOS beta · grabado en una máquina virtual · música de prueba'),
]
END = SHOTS[-1][1]
TOP = 230          # dónde van los textos
CY = 1010          # centro vertical de la grabación
FW = 1000          # ancho de la grabación en el video


def run(*a):
    subprocess.run(a, check=True)


html = '''<html><head><meta charset="utf-8"><style>
html,body{margin:0;background:transparent}
div{width:1000px;padding:10px 40px;font-family:"Noto Sans","DejaVu Sans",sans-serif;font-weight:800;font-size:60px;line-height:1.2;
 color:#fff;text-align:center;-webkit-text-stroke:10px #000;paint-order:stroke fill;letter-spacing:-.5px}
div.nota{font-size:28px;font-weight:700;-webkit-text-stroke:6px #000;color:#e6e1ff}
</style></head><body><div id="t" class="CLS">TEXT</div></body></html>'''
jobs = [{'html': html.replace('TEXT', t).replace('CLS', ''), 'out': f'{TMP}/cap{i}.png'} for i, (_, _, t) in enumerate(CAPTIONS)]
jobs += [{'html': html.replace('TEXT', t).replace('CLS', 'nota'), 'out': f'{TMP}/nota{i}.png'} for i, (_, _, t) in enumerate(NOTAS)]
json.dump(jobs, open(f'{TMP}/jobs.json', 'w'))
node = """const { chromium } = require('playwright'); const jobs = require(process.argv[1]);
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 400 } });
  for (const j of jobs) { await p.setContent(j.html); await p.locator('#t').screenshot({ path: j.out, omitBackground: true }); }
  await b.close(); })();"""
run('node', '-e', node, f'{TMP}/jobs.json')


def mask(w, h, r=34):
    path = f'{TMP}/mask-{w}x{h}.png'
    if not os.path.exists(path):
        m = Image.new('L', (w, h), 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=255)
        m.save(path)
    return path


parts = []
for i, (a, z, src, ss, (x, y, cw, ch), z0, z1) in enumerate(SHOTS):
    d = z - a
    n = max(1, round(d * FPS))
    fh = min(1240, round(FW * ch / cw / 2) * 2)
    fw = FW if fh < 1240 else round(1240 * cw / ch / 2) * 2
    img = src.endswith('.png')
    inp = (['-loop', '1', '-framerate', str(FPS), '-t', f'{d:.3f}', '-i', src] if img
           else ['-ss', f'{ss:.3f}', '-t', f'{d + 0.2:.3f}', '-i', src])
    fc = (f'[0:v]fps={FPS},split[s1][s2];'
          f'[s1]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=28:3,eq=brightness=-0.32:saturation=1.2[bg];'
          f'[s2]crop={cw}:{ch}:{x}:{y},scale={fw * 2}:{fh * 2}:flags=lanczos,'
          f"zoompan=z='{z0}+({z1}-{z0})*on/{n}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s={fw}x{fh}:fps={FPS},format=rgba[fg0];"
          f'[1:v]format=gray[m];[fg0][m]alphamerge[fg];'
          f'[bg][fg]overlay=({W}-{fw})/2:{CY}-{fh}/2,trim=end_frame={n},setpts=PTS-STARTPTS,format=yuv420p[v]')
    out = f'{TMP}/p{i:02d}.mp4'
    run('ffmpeg', '-v', 'error', '-y', *inp, '-loop', '1', '-i', mask(fw, fh), '-filter_complex', fc,
        '-map', '[v]', '-frames:v', str(n), '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-r', str(FPS), out)
    parts.append(out)

open(f'{TMP}/lista.txt', 'w').write(''.join(f"file '{p}'\n" for p in parts))
run('ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{TMP}/lista.txt', '-c', 'copy', f'{TMP}/base.mp4')

inputs, fc, last, k = ['-i', f'{TMP}/base.mp4'], [], '0:v', 1
for i, (a, z, _) in enumerate(CAPTIONS):
    inputs += ['-i', f'{TMP}/cap{i}.png']
    fc.append(f"[{last}][{k}:v]overlay=(W-w)/2:{TOP}:enable='between(t,{a},{z - 0.001})'[c{i}]")
    last, k = f'c{i}', k + 1
for i, (a, z, _) in enumerate(NOTAS):
    inputs += ['-i', f'{TMP}/nota{i}.png']
    fc.append(f"[{last}][{k}:v]overlay=(W-w)/2:1700:enable='between(t,{a},{z - 0.001})'[n{i}]")
    last, k = f'n{i}', k + 1
fc[-1] = fc[-1].rsplit('[', 1)[0] + '[out]'
run('ffmpeg', '-v', 'error', '-y', *inputs, '-i', VOZ, '-filter_complex', ';'.join(fc),
    '-map', '[out]', '-map', f'{k}:a', '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '192k', '-t', str(END), '-movflags', '+faststart', OUT)
print(f'Video: {OUT} ({END:.1f} s)')
