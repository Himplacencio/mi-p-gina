"""Monta el video vertical «cuánta RAM usa MoonOS» a partir de la grabación real.

Entrada: moonos/marketing/arranque-real/terminal.mp4 (workflow «Grabar el arranque
de MoonOS», modo terminal). Corta en planos con zoom sobre lo importante y pone
textos al estilo TikTok (blanco con borde negro, en minúsculas).

Uso: python3 montar-terminal.py [salida.mp4]
Requiere: ffmpeg y Node con Playwright (Chromium).
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'arranque-real', 'terminal.mp4')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'moonos-ram-tiktok.mp4')
W, H, FPS = 1080, 1920, 30
TMP = tempfile.mkdtemp(prefix='terminal-')

# Planos: (inicio, fin, recorte x, y, ancho, alto) sobre la grabación de 1920x1080
SHOTS = [
    (0.0, 4.5, 0, 0, 1920, 1080),        # pantalla completa: se abre la terminal
    (4.5, 10.6, 0, 70, 520, 230),        # zoom: se escribe «fastfetch»
    (10.6, 15.6, 578, 176, 520, 326),    # zoom: Kernel … Memory
    (15.6, 23.5, 0, 652, 470, 82),       # zoom: free -h
]
# Resaltado (x, y, w, h en coordenadas de la grabación) por plano
HIGHLIGHT = {2: (582, 474, 330, 24), 3: (262, 676, 74, 44)}
CAPTIONS = [
    (0.0, 4.5, 'mi sistema operativo usa<br>poquísima ram, mira 👀'),
    (4.5, 10.6, 'abro la terminal y escribo fastfetch'),
    (10.6, 15.6, '1,15 gb con el escritorio abierto 🪶'),
    (15.6, 19.5, 'y free -h lo confirma ✅'),
    (19.5, 23.5, '¿cuánta usa tu pc<br>sin abrir nada? 👇'),
]
END = SHOTS[-1][1]
VY = 600  # dónde empieza la grabación en el video vertical

def run(*a):
    subprocess.run(a, check=True)

html = '''<html><head><meta charset="utf-8"><style>
html,body{margin:0;background:transparent}
div{width:1000px;padding:10px 40px;font-family:"Noto Sans","DejaVu Sans",sans-serif;font-weight:800;font-size:58px;line-height:1.22;
 color:#fff;text-align:center;-webkit-text-stroke:9px #000;paint-order:stroke fill;letter-spacing:-.5px}
div.nota{font-size:30px;font-weight:700;-webkit-text-stroke:6px #000;color:#e8e8e8}
</style></head><body><div id="t" class="CLS">TEXT</div></body></html>'''
# Los textos se dibujan con Chromium (Playwright de Node) para que los emojis salgan bien
jobs = [{'html': html.replace('TEXT', t).replace('CLS', ''), 'out': f'{TMP}/cap{i}.png'} for i, (_, _, t) in enumerate(CAPTIONS)]
jobs.append({'html': html.replace('TEXT', 'grabado en una máquina virtual · MoonOS beta').replace('CLS', 'nota'), 'out': f'{TMP}/nota.png'})
json.dump(jobs, open(f'{TMP}/jobs.json', 'w'))
node = """const { chromium } = require('playwright'); const jobs = require(process.argv[1]);
(async () => { const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1080, height: 400 } });
  for (const j of jobs) { await p.setContent(j.html); await p.locator('#t').screenshot({ path: j.out, omitBackground: true }); }
  await b.close(); })();"""
run('node', '-e', node, f'{TMP}/jobs.json')

# Cada plano: fondo desenfocado de la pantalla completa + recorte ampliado al centro
parts = []
for i, (a, z, x, y, w, h) in enumerate(SHOTS):
    fh = round(W * h / w / 2) * 2
    vy = VY if i == 0 else VY + max(0, (607 - fh) // 2)
    hl = ''
    if i in HIGHLIGHT:
        hx, hy, hw, hh = HIGHLIGHT[i]
        k = W / w
        hl = (f',drawbox=x={(hx - x) * k:.0f}:y={(hy - y) * k:.0f}:w={hw * k:.0f}:h={hh * k:.0f}'
              f':color=yellow@0.9:t=6')
    out = f'{TMP}/p{i}.mp4'
    fc = (f'[0:v]trim={a}:{z},setpts=PTS-STARTPTS,split[s1][s2];'
          f'[s1]scale=-2:{H},crop={W}:{H},boxblur=30:3,eq=brightness=-0.3[bg];'
          f'[s2]crop={w}:{h}:{x}:{y},scale={W}:{fh}:flags=lanczos{hl}[fg];'
          f'[bg][fg]overlay=0:{vy},fps={FPS},format=yuv420p[v]')
    run('ffmpeg', '-v', 'error', '-y', '-i', SRC, '-filter_complex', fc, '-map', '[v]',
        '-c:v', 'libx264', '-crf', '18', '-preset', 'slow', '-r', str(FPS), out)
    parts.append(out)

open(f'{TMP}/lista.txt', 'w').write(''.join(f"file '{p}'\n" for p in parts))
run('ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{TMP}/lista.txt', '-c', 'copy', f'{TMP}/base.mp4')

inputs = ['-i', f'{TMP}/base.mp4']
fc, last = [], '0:v'
for i, (a, z, _) in enumerate(CAPTIONS):
    inputs += ['-i', f'{TMP}/cap{i}.png']
    fc.append(f'[{last}][{i + 1}:v]overlay=(W-w)/2:{VY - 330}:enable=\'between(t,{a},{z})\'[c{i}]')
    last = f'c{i}'
inputs += ['-i', f'{TMP}/nota.png']
fc.append(f'[{last}][{len(CAPTIONS) + 1}:v]overlay=(W-w)/2:{VY + 740}[out]')
run('ffmpeg', '-v', 'error', '-y', *inputs, '-f', 'lavfi', '-t', str(END), '-i', 'anullsrc=r=44100:cl=stereo',
    '-filter_complex', ';'.join(fc), '-map', '[out]', '-map', f'{len(CAPTIONS) + 2}:a',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-pix_fmt', 'yuv420p', '-c:a', 'aac',
    '-t', str(END), '-movflags', '+faststart', OUT)
print(f'Video: {OUT} ({END:.1f} s)')
