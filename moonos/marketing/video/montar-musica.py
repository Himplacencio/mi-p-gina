"""Monta el video vertical «música en la barra de MoonOS» a partir de la grabación real.

Entrada: moonos/marketing/arranque-real/musica.mp4 (workflow «Grabar el arranque
de MoonOS», modo musica). Corta en planos con zoom sobre lo importante y pone
textos al estilo TikTok (blanco con borde negro, en minúsculas).

Uso: python3 montar-musica.py [salida.mp4]
Requiere: ffmpeg y Node con Playwright (Chromium).
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'arranque-real', 'musica.mp4')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'moonos-musica-tiktok.mp4')
W, H, FPS = 1080, 1920, 30
TMP = tempfile.mkdtemp(prefix='musica-')

# Planos: (inicio, fin, recorte x, y, ancho, alto) sobre la grabación de 1920x1080
SHOTS = [
    (0.0, 4.0, 0, 0, 1500, 820),         # escritorio completo (barra, widgets, luna animada)
    (4.0, 11.0, 1380, 0, 420, 40),       # zoom: la música en la barra de arriba (⏭ a los 8 s)
    (11.0, 19.5, 120, 520, 610, 225),    # zoom: tarjeta de música de vidrio (pausa y play)
    (19.5, 26.0, 0, 0, 1500, 820),       # escritorio completo (⏮ a los 21 s)
]
HIGHLIGHT = {}
CAPTIONS = [
    (0.0, 4.0, 'le puse música a la barra<br>de mi sistema operativo 🎵'),
    (4.0, 7.6, 'arriba ves la canción<br>y cuánto le falta'),
    (7.6, 11.0, '⏭ siguiente canción'),
    (11.0, 13.8, 'y una tarjeta de vidrio<br>en el escritorio'),
    (13.8, 19.5, '⏯ pausa y play<br>con las teclas de música'),
    (19.5, 26.0, 'funciona con spotify 💜<br>moonos · se viene en 2027 🌙'),
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
jobs.append({'html': html.replace('TEXT', 'grabado en una máquina virtual · MoonOS beta · reproductor de prueba').replace('CLS', 'nota'), 'out': f'{TMP}/nota.png'})
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
    vy = VY + max(0, (600 - fh) // 2)
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
