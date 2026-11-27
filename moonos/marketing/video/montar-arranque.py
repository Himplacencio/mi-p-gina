"""Monta el video vertical «arranque en tiempo real» para TikTok.

Entrada: moonos/marketing/arranque-real/arranque-real.mp4 (grabación real de
la máquina virtual, generada por el workflow «Grabar el arranque de MoonOS»).
Detecta solo en qué segundo aparece el escritorio y pone un cronómetro que
se detiene ahí, más textos al estilo TikTok (letra blanca con borde negro).

Uso: python3 montar-arranque.py salida.mp4
Requiere: ffmpeg, Pillow y Playwright (para dibujar los textos con emojis).
"""
import json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageStat

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'arranque-real', 'arranque-real.mp4')
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', 'moonos-arranque-tiktok.mp4')
W, H, FPS = 1080, 1920, 30
TMP = tempfile.mkdtemp(prefix='arranque-')

def run(*a):
    subprocess.run(a, check=True)

# 1) Detectar el segundo en que aparece el escritorio (la imagen deja de cambiar
#    y se parece al escritorio final, antes de abrir el menú)
run('ffmpeg', '-v', 'error', '-i', SRC, '-vf', 'fps=10,scale=240:135', f'{TMP}/s_%05d.png')
samples = sorted(f for f in os.listdir(TMP) if f.startswith('s_'))
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', SRC],
                           capture_output=True, text=True).stdout)
ref_t = dur - 10.5   # el menú se abre 9 s antes del final: tomar el escritorio justo antes
ref = Image.open(f'{TMP}/{samples[int(ref_t * 10)]}').convert('L')
desk = None
for i, f in enumerate(samples):
    d = ImageStat.Stat(ImageChops.difference(Image.open(f'{TMP}/{f}').convert('L'), ref)).mean[0]
    if d < 6:
        desk = i / 10
        break
if desk is None:
    sys.exit('No se encontró el momento en que aparece el escritorio')
print(f'Escritorio visible en el segundo {desk:.1f} (grabación de {dur:.1f} s)')
END = min(dur, desk + 8.5)   # el video termina 8,5 s después de llegar al escritorio

# 2) Textos (HTML -> PNG transparente, para que los emojis salgan bien)
captions = [
    ('cap1', 0.0, 3.2, 'prendí mi pc con el sistema<br>operativo que estoy haciendo 👀'),
    ('cap2', 3.2, desk, 'sin cortes. tiempo real ⏱️'),
    ('cap3', desk, desk + 4.2, f'y ya está en el escritorio 🌙'),
    ('cap4', desk + 4.2, END, '¿cuánto tarda el tuyo? 👇'),
]
html = '''<html><head><meta charset="utf-8"><style>
html,body{margin:0;background:transparent}
div{width:1000px;padding:10px 40px;font-family:"Noto Sans","DejaVu Sans",sans-serif;font-weight:800;font-size:56px;line-height:1.25;
 color:#fff;text-align:center;-webkit-text-stroke:9px #000;paint-order:stroke fill;letter-spacing:-.5px}
small{display:block;font-size:30px;font-weight:700;-webkit-text-stroke:6px #000;margin-top:6px;color:#e8e8e8}
</style></head><body><div id="t">TEXT</div></body></html>'''
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 1080, 'height': 400})
    for name, _, _, text in captions:
        pg.set_content(html.replace('TEXT', text))
        pg.locator('#t').screenshot(path=f'{TMP}/{name}.png', omit_background=True)
    pg.set_content(html.replace('TEXT', '<small>grabado en una máquina virtual · MoonOS beta</small>'))
    pg.locator('#t').screenshot(path=f'{TMP}/nota.png', omit_background=True)
    b.close()

# 3) Cronómetro: una imagen por cuadro (se detiene al llegar al escritorio)
mono = ImageFont.truetype(next(p for p in ['/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-Bold.ttf',
                                            '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'] if os.path.exists(p)), 118)
os.makedirs(f'{TMP}/crono', exist_ok=True)
for i in range(int(END * FPS) + 1):
    t = i / FPS
    shown = min(t, desk)
    im = Image.new('RGBA', (W, 200), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    txt = f'{int(shown // 60):02d}:{shown % 60:04.1f}'.replace('.', ',')
    color = (125, 235, 170, 255) if t >= desk else (255, 255, 255, 255)
    tw = d.textlength(txt, font=mono)
    d.text(((W - tw) / 2, 30), txt, font=mono, fill=color, stroke_width=8, stroke_fill=(0, 0, 0, 255))
    im.save(f'{TMP}/crono/c_{i:05d}.png')

# 4) Montaje: fondo desenfocado + grabación al centro + textos + cronómetro
VID_H = int(W * 9 / 16)          # 1080x607
VY = 560                         # posición vertical de la grabación
fc = [
    f'[0:v]trim=0:{END:.3f},setpts=PTS-STARTPTS,split[a][b]',
    f'[a]scale=-2:{H},crop={W}:{H},boxblur=30:3,eq=brightness=-0.25[bg]',
    f'[b]scale={W}:{VID_H}[fg]',
    f'[bg][fg]overlay=0:{VY}[v0]',
    f'[v0][1:v]overlay=0:{VY + VID_H + 40}[v1]',
]
inputs = ['-i', SRC, '-framerate', str(FPS), '-i', f'{TMP}/crono/c_%05d.png']
last = 'v1'
for k, (name, a, b_, _) in enumerate(captions):
    inputs += ['-i', f'{TMP}/{name}.png']
    fc.append(f'[{last}][{k + 2}:v]overlay=(W-w)/2:{VY - 300}:enable=\'between(t,{a:.2f},{b_:.2f})\'[c{k}]')
    last = f'c{k}'
inputs += ['-i', f'{TMP}/nota.png']
fc.append(f'[{last}][{len(captions) + 2}:v]overlay=(W-w)/2:{VY + VID_H + 230}[out]')
run('ffmpeg', '-v', 'error', '-y', *inputs, '-f', 'lavfi', '-t', f'{END:.3f}', '-i', 'anullsrc=r=44100:cl=stereo',
    '-filter_complex', ';'.join(fc), '-map', '[out]', '-map', f'{len(captions) + 3}:a',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-pix_fmt', 'yuv420p', '-r', str(FPS),
    '-c:a', 'aac', '-t', f'{END:.3f}', '-movflags', '+faststart', OUT)
json.dump({'escritorio_seg': desk, 'duracion_video': END}, open(OUT + '.json', 'w'))
print(f'Video: {OUT} ({END:.1f} s) · escritorio en {desk:.1f} s')
