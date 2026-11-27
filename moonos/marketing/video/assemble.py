"""Monta el video de TikTok a partir de los cuadros grabados por record.js."""
import json, os, subprocess, sys

D = os.path.dirname(os.path.abspath(__file__))
SLOW = 4          # record.js graba en cámara lenta x4
XFADE = 0.25      # duración de cada transición
OUT = sys.argv[1] if len(sys.argv) > 1 else f'{D}/moonos-tiktok.mp4'

scenes = sorted(d for d in os.listdir(f'{D}/frames') if os.path.isdir(f'{D}/frames/{d}'))
durs = []
for s in scenes:
    j = json.load(open(f'{D}/frames/{s}/frames.json'))
    fr, end = j['frames'], j['end']
    lines = []
    for i, f in enumerate(fr):
        nxt = fr[i + 1]['t'] if i + 1 < len(fr) else end
        lines.append(f"file '{f['file']}'\nduration {max(0.001, (nxt - f['t']) / SLOW):.5f}")
    lines.append(f"file '{fr[-1]['file']}'")
    open(f'{D}/frames/{s}/list.txt', 'w').write('\n'.join(lines))
    out = f'{D}/{s}.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{D}/frames/{s}/list.txt',
                    '-vf', 'fps=30,scale=1080:1920,format=yuv420p', '-c:v', 'libx264', '-preset', 'slow',
                    '-crf', '18', '-r', '30', out], check=True)
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', out],
                               capture_output=True, text=True).stdout)
    durs.append(dur)
    print(f'{s}: {dur:.2f} s, {len(fr)} cuadros grabados (~{len(fr) / dur:.0f} fps)')

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
subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, '-f', 'lavfi', '-t', f'{total:.3f}', '-i', 'anullsrc=r=44100:cl=stereo',
                '-filter_complex', ';'.join(filt), '-map', prev, '-map', f'{len(scenes)}:a',
                '-c:v', 'libx264', '-preset', 'slow', '-crf', '19', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k',
                '-shortest', '-movflags', '+faststart', OUT], check=True)
print(f'Video final: {OUT} ({total:.1f} s)')
