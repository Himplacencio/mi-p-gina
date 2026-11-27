"""Video de presentación de MoonOS con imágenes REALES del sistema.

Usa la misma voz (ElevenLabs) y el mismo guion que el primer video de presentación,
pero en vez de dibujos muestra grabaciones reales de MoonOS en una máquina virtual:

  arranque-real/arranque-real.mp4  arranque (texto del sistema y pantalla de carga)
  arranque-real/recorrido.mp4      Bienvenida, sus páginas, la Tienda (Comandos), dock y menú
  arranque-real/terminal.mp4       fastfetch y free -h
  arranque-real/musica.mp4         escritorio con el dock, widgets y música
  más capturas de la página web (página y panel de fallas).

Cada plano: grabación con esquinas redondeadas y zoom lento sobre un fondo desenfocado
de la misma grabación; textos estilo TikTok arriba.

Uso: python3 montar-presentacion-real.py [salida.mp4]
Requiere: ffmpeg, Pillow y Node con Playwright (Chromium).
"""
import json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
MK = os.path.join(HERE, '..')
REAL = os.path.join(MK, 'arranque-real')
WEB = os.path.join(HERE, 'web-capturas')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(MK, 'moonos-presentacion-real.mp4')
VOZ = os.path.join(HERE, 'voz-presentacion.m4a')
W, H, FPS = 1080, 1920, 30
TMP = tempfile.mkdtemp(prefix='presentacion-')

A = os.path.join(REAL, 'arranque-real.mp4')
R = os.path.join(REAL, 'recorrido.mp4')
T = os.path.join(REAL, 'terminal.mp4')
M = os.path.join(REAL, 'musica.mp4')
PAG = os.path.join(WEB, 'pagina-celular.png')
FAL = os.path.join(WEB, 'fallas.png')

# Tiempos de la grabación «recorrido» (segundos desde que empieza a grabar)
RT = json.load(open(os.path.join(HERE, 'recorrido-tiempos.json')))

# Planos: (inicio, fin, fuente, segundo de la fuente, (x, y, ancho, alto), zoom inicial, zoom final)
SHOTS = [
    (0.00, 5.40, A, 4.0, (0, 0, 860, 1000), 1.00, 1.18),               # texto del arranque
    (5.40, 8.90, M, 0.5, (0, 0, 1920, 1080), 1.30, 1.00),               # aparece el escritorio de MoonOS
    (8.90, 13.00, M, 4.0, (100, 40, 660, 720), 1.00, 1.12),             # widgets de vidrio
    (13.00, 17.30, M, 9.0, (760, 60, 1100, 1000), 1.00, 1.12),          # la luna animada
    (17.30, 21.70, A, 7.0, (0, 0, 900, 1000), 1.00, 1.15),              # texto del arranque
    (21.70, 24.30, A, 10.0, (500, 0, 900, 1000), 1.12, 1.00),           # más texto
    (24.30, 27.20, A, 13.0, (0, 80, 900, 1000), 1.00, 1.15),            # más texto
    (27.20, 32.55, A, 15.0, (0, 0, 1100, 1000), 1.20, 1.00),            # «comandos raros»
    (32.55, 34.80, R, RT['bienvenida'] + 0.5, RT['bienvenida_titulo'], 1.00, 1.10),
    (34.80, 37.95, R, RT['juegos'] + 0.3, RT['ventana'], 1.00, 1.08),
    (37.95, 39.90, R, RT['bienvenida'] + 2.5, RT['equipo'], 1.00, 1.08),
    (39.90, 42.95, T, RT['t_memoria'], RT['t_memoria_zona'], 1.00, 1.12),
    (42.95, 46.00, R, RT['tienda'] + 1.0, RT['ventana_tienda'], 1.00, 1.08),
    (46.00, 50.95, PAG, 0, (0, 0, 1170, 1992), 1.00, 1.12),
    (50.95, 54.60, T, RT['t_fastfetch'], RT['t_fastfetch_zona'], 1.00, 1.06),
    (54.60, 59.00, R, RT['bienvenida'] + 5.0, RT['equipo'], 1.10, 1.00),
    (59.00, 62.80, M, 12.0, (560, 560, 800, 520), 1.00, 1.30),          # el dock con Steam
    (62.80, 66.75, R, RT['bienvenida'] + 7.0, RT['instalar'], 1.00, 1.12),
    (66.75, 72.30, FAL, 0, (340, 126, 600, 608), 1.00, 1.10),
    (72.30, 77.32, R, RT['menu'] - 1.5, (0, 0, 1920, 1080), 1.12, 1.00),
]
CAPTIONS = [
    (0.00, 4.00, 'windows: «solo voy a<br>actualizar una cosita» 🙂'),
    (4.00, 5.40, '*3 horas después* 💀'),
    (5.40, 8.90, 'así que hice mi propio<br>sistema operativo 🌙'),
    (8.90, 11.90, 'hola 👋 soy quien<br>está creando moonos'),
    (11.90, 14.10, 'un sistema operativo<br>para gamers 🎮'),
    (14.10, 17.30, 'hecho desde cero…<br>bueno, casi 😅'),
    (17.30, 21.70, 'el problema: tu pc se pone<br>lento justo cuando vas a jugar 🐢'),
    (21.70, 24.30, 'las actualizaciones<br>aparecen cuando QUIEREN 🙃'),
    (24.30, 27.20, 'programas de fondo<br>comiéndose tu ram 🍽️'),
    (27.20, 32.55, 'y linux da miedo: drivers,<br>terminal, comandos raros 😱'),
    (32.55, 34.80, 'por eso nació moonos 💡'),
    (34.80, 37.95, 'tu pc 100 % enfocado<br>en el juego ⚡'),
    (37.95, 39.90, 'los drivers se<br>instalan solos 🪄'),
    (39.90, 42.95, 'ligero: funciona hasta<br>en pcs modestos 🪶'),
    (42.95, 46.00, 'gratis, en español<br>y para siempre 💜'),
    (46.00, 50.95, 'esta es su página 👀'),
    (50.95, 54.60, 'y sí, lo primero que hice fue<br>presumir con fastfetch 😎'),
    (54.60, 59.00, '¿nvidia, amd o intel?<br>moonos lo detecta solo'),
    (59.00, 62.80, 'abres un juego… y el pc<br>se pone en modo bestia 🔥'),
    (62.80, 66.75, 'instalarlo es más fácil que<br>explicarle a tu mamá qué es un kernel'),
    (66.75, 70.30, '¿encuentras una falla?<br>la reportas y todos la ven'),
    (70.30, 72.30, '…y la ves pasar a<br>✅ solucionada'),
    (72.30, 77.32, 'llega en 2027 🌙<br>síguenos para verlo nacer ✨'),
]
NOTAS = [  # letra chica abajo
    (0.0, 66.75, 'imágenes reales de MoonOS beta · grabado en una máquina virtual'),
    (66.75, 72.30, 'reportes de ejemplo · así se ve el panel de fallas de la página'),
    (72.30, 77.32, 'imágenes reales de MoonOS beta · grabado en una máquina virtual'),
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
