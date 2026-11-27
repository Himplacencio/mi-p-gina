"""Monta el video de TikTok a partir de los cuadros grabados por record.js.

Uso: python3 assemble.py [salida.mp4] [voz.mp3]
Si hay voice-align.json, cada escena se recorta/alarga a la duración exacta
de su frase en la voz, para que el audio quede sincronizado.
"""
import json, os, subprocess, sys

D = os.path.dirname(os.path.abspath(__file__))
SLOW = 4          # record.js graba en cámara lenta x4
XFADE = 0.25      # duración de cada transición
OUT = sys.argv[1] if len(sys.argv) > 1 else f'{D}/moonos-tiktok.mp4'
VOICE = sys.argv[2] if len(sys.argv) > 2 else None
ALIGN = json.load(open(f'{D}/voice-align.json'))['durs'] if os.path.exists(f'{D}/voice-align.json') else {}

scenes = sorted(d for d in os.listdir(f'{D}/frames') if os.path.isdir(f'{D}/frames/{d}'))
durs = []
for k, s in enumerate(scenes):
    j = json.load(open(f'{D}/frames/{s}/frames.json'))
    fr, start, end = j['frames'], j['start'], j['end']
    lines = []
    for i, f in enumerate(fr):
        t = max(f['t'], start) if i == 0 else f['t']
        nxt = fr[i + 1]['t'] if i + 1 < len(fr) else end
        dur = (nxt - (start if i == 0 else t)) / SLOW
        lines.append(f"file '{f['file']}'\nduration {max(0.001, dur):.5f}")
    lines.append(f"file '{fr[-1]['file']}'")
    open(f'{D}/frames/{s}/list.txt', 'w').write('\n'.join(lines))
    last = k == len(scenes) - 1
    target = ALIGN.get(s)
    if target is not None:
        target += 1.2 if last else XFADE
    vf = 'fps=30,scale=1080:1920,format=yuv420p'
    if target:
        vf += f',tpad=stop_mode=clone:stop_duration=3,trim=duration={target:.3f},setpts=PTS-STARTPTS'
    out = f'{D}/{s}.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{D}/frames/{s}/list.txt',
                    '-vf', vf, '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-r', '30', out], check=True)
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', out],
                               capture_output=True, text=True).stdout)
    durs.append(dur)
    print(f'{s}: {dur:.2f} s (objetivo {target or "-"}), {len(fr)} cuadros grabados')

inputs = []
for s in scenes:
    inputs += ['-i', f'{D}/{s}.mp4']
filt, prev, off = [], '[0:v]', 0.0
transitions = ['slideup', 'smoothleft', 'slideup', 'smoothleft', 'fadewhite']
for i in range(1, len(scenes)):
    off += durs[i - 1] - XFADE
    filt.append(f'{prev}[{i}:v]xfade=transition={transitions[(i - 1) % len(transitions)]}:duration={XFADE}:offset={off:.3f}[v{i}]')
    prev = f'[v{i}]'
total = sum(durs) - XFADE * (len(scenes) - 1)
if VOICE:
    audio_in = ['-i', VOICE]
    filt.append(f'[{len(scenes)}:a]aresample=44100,apad,atrim=duration={total:.3f},afade=t=out:st={total - 0.6:.3f}:d=0.6[a]')
    amap = '[a]'
else:
    audio_in = ['-f', 'lavfi', '-t', f'{total:.3f}', '-i', 'anullsrc=r=44100:cl=stereo']
    amap = f'{len(scenes)}:a'
subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, *audio_in,
                '-filter_complex', ';'.join(filt), '-map', prev, '-map', amap,
                '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '160k',
                '-t', f'{total:.3f}', '-movflags', '+faststart', OUT], check=True)
print(f'Video final: {OUT} ({total:.1f} s)')
