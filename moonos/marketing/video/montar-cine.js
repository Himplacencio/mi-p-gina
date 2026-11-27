// Monta el video «cinematográfico» de MoonOS (16:9) dibujando cada cuadro con cine.html.
// Uso: node montar-cine.js <carpeta-cuadros (s1..s9)> <salida.mp4> [desde] [hasta]
//   La carpeta de cuadros se prepara con ffmpeg a partir de arranque-real/*.mp4 (ver README).
const { chromium } = require('playwright');
const { execFileSync } = require('child_process');
const fs = require('fs'), path = require('path'), os = require('os');

(async () => {
  const [frames, out, desde, hasta] = process.argv.slice(2);
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'cine-'));
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto('file://' + path.join(__dirname, 'cine.html') + '?frames=' + encodeURIComponent('file://' + path.resolve(frames)));
  await p.evaluate(() => window.listo);
  const total = await p.evaluate(() => window.TOTAL_FRAMES);
  const a = desde ? +desde : 0, z = hasta ? +hasta : total;
  for (let i = a; i < z; i++) {
    await p.evaluate(i => window.render(i), i);
    await p.screenshot({ path: path.join(tmp, `c_${String(i - a).padStart(5, '0')}.jpg`), type: 'jpeg', quality: 93 });
    if (i % 150 === 0) console.log(`cuadro ${i}/${z}`);
  }
  await b.close();
  execFileSync('ffmpeg', ['-v', 'error', '-y', '-framerate', '30', '-i', path.join(tmp, 'c_%05d.jpg'),
    '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', '-shortest',
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-movflags', '+faststart', out]);
  fs.rmSync(tmp, { recursive: true });
  console.log('Video:', out);
})();
