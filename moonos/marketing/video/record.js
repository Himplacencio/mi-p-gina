// Graba el video de TikTok de MoonOS escena por escena a 1080x1920.
// Usa el "screencast" de Chromium (cuadros en resolución real) y guarda
// cada cuadro con su marca de tiempo para montarlo luego con ffmpeg.
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const OUT = __dirname + '/frames';
const WEB = 'file:///home/user/mi-p-gina/moonos/index.html';
const DEMO = 'file:///home/user/mi-p-gina/moonos/demo/index.html';
const FINAL = 'file://' + __dirname + '/final.html';
// Cámara lenta: todo corre 4 veces más lento y luego el video se acelera 4x,
// así hay muchos más cuadros por segundo aunque renderizar en 1080p sea lento.
const SLOW = 4;
const sleep = ms => new Promise(r => setTimeout(r, ms * SLOW));
const SLOW_SCRIPT = `(() => { const S = ${SLOW};
  const pn = performance.now.bind(performance), base = pn();
  performance.now = () => base + (pn() - base) / S;
  const raf = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = cb => raf(() => cb(performance.now()));
  const st = window.setTimeout.bind(window); window.setTimeout = (f, d = 0, ...a) => st(f, d * S, ...a);
  const si = window.setInterval.bind(window); window.setInterval = (f, d = 0, ...a) => si(f, d * S, ...a);
  const dn = Date.now, d0 = dn(); Date.now = () => d0 + (dn() - d0) / S; })();`;

const CAP_CSS = `
#cap{position:fixed;left:14px;right:14px;z-index:999999;display:grid;gap:8px;justify-items:center;pointer-events:none;text-align:center}
#cap .l{font-family:'Unbounded','Noto Sans',sans-serif;font-weight:700;font-size:25px;line-height:1.18;color:#fff;
 background:rgba(9,7,28,.86);padding:9px 15px;border-radius:14px;box-shadow:0 10px 30px rgba(0,0,0,.55);
 border:1px solid rgba(169,150,255,.35);animation:capPop .38s cubic-bezier(.2,1.5,.4,1) both}
#cap .l.y{background:#f4ecd0;color:#1b1406;border-color:#f4ecd0}
#cap .l.small{font-size:19px;font-family:'Manrope','Noto Sans',sans-serif}
#cap .l:nth-child(2){animation-delay:.12s}
@keyframes capPop{from{transform:scale(.55) rotate(-3deg);opacity:0}}`;

async function caption(page, lines, top = 92) {
  await page.evaluate(({ lines, top, css }) => {
    if (!document.getElementById('cap-style')) {
      const l = document.createElement('link'); l.rel = 'stylesheet';
      l.href = 'https://fonts.googleapis.com/css2?family=Unbounded:wght@700&family=Manrope:wght@700&display=swap';
      document.head.append(l);
      const s = document.createElement('style'); s.id = 'cap-style'; s.textContent = css; document.head.append(s);
    }
    document.getElementById('cap')?.remove();
    const c = document.createElement('div'); c.id = 'cap'; c.style.top = top + 'px';
    c.innerHTML = lines.map(x => typeof x === 'string' ? `<div class="l">${x}</div>` : `<div class="l ${x.c}">${x.t}</div>`).join('');
    document.body.append(c);
  }, { lines, top, css: CAP_CSS });
}

const ONLY = process.env.ONLY;
async function scene(browser, name, url, setup, act) {
  if (ONLY && name !== ONLY) return;
  // La página se carga en un iframe de 432x768 (diseño de celular) ampliado 2,5x
  // dentro de un lienzo de 1080x1920, para que los cuadros salgan nítidos.
  const ctx = await browser.newContext({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await ctx.addInitScript(SLOW_SCRIPT);
  const page = await ctx.newPage();
  const cdpA = await ctx.newCDPSession(page);
  await cdpA.send('Animation.enable');
  await cdpA.send('Animation.setPlaybackRate', { playbackRate: 1 / SLOW });
  await page.goto('file://' + __dirname + '/host.html#' + encodeURIComponent(url));
  await page.waitForTimeout(400);
  const f = page.frames().find(x => x !== page.mainFrame());
  await f.waitForLoadState('load');
  const p = {
    click: (...a) => f.click(...a), fill: (...a) => f.fill(...a), evaluate: (...a) => f.evaluate(...a),
    waitForTimeout: ms => page.waitForTimeout(ms * SLOW), keyboard: page.keyboard,
    reload: async () => { await f.goto(url); await f.waitForLoadState('load'); },
  };
  if (setup) await setup(p);
  const dir = path.join(OUT, name); fs.mkdirSync(dir, { recursive: true });
  const cdp = await ctx.newCDPSession(page);
  const frames = [];
  cdp.on('Page.screencastFrame', async fr => {
    const file = path.join(dir, String(frames.length).padStart(5, '0') + '.jpg');
    fs.writeFileSync(file, Buffer.from(fr.data, 'base64'));
    frames.push({ file, t: fr.metadata.timestamp });
    try { await cdp.send('Page.screencastFrameAck', { sessionId: fr.sessionId }); } catch {}
  });
  await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 72, maxWidth: 1080, maxHeight: 1920, everyNthFrame: 1 });
  const t0 = Date.now() / 1000;
  await act(p);
  const t1 = Date.now() / 1000;
  await cdp.send('Page.stopScreencast');
  await ctx.close();
  fs.writeFileSync(path.join(dir, 'frames.json'), JSON.stringify({ frames, start: t0, end: t1 }));
  console.log(`${name}: ${frames.length} cuadros, ${(t1 - t0).toFixed(1)} s`);
}

(async () => {
  if (!ONLY) fs.rmSync(OUT, { recursive: true, force: true }); else fs.rmSync(path.join(OUT, ONLY), { recursive: true, force: true });
  const browser = await chromium.launch();

  // 1) GANCHO: el chiste de las actualizaciones de Windows + la luna saliendo
  await scene(browser, '1-gancho', WEB, async p => {
    await p.waitForTimeout(1500);
    // En el gancho solo se ve la luna y el chiste; el titular aparece después
    await p.evaluate(() => { const h = document.querySelector('.hero-copy'); h.style.transition = 'none'; h.style.opacity = '0'; h.style.transform = 'translateY(24px)'; });
    await p.waitForTimeout(200);
  }, async p => {
    await caption(p, ['Windows: “solo voy a actualizar una cosita” 🙂'], 250);
    await p.evaluate(() => { const m = document.querySelector('.big-moon'); m.style.animation = 'none'; m.offsetWidth; m.style.animation = ''; });
    await sleep(1300);
    await caption(p, ['Windows: “solo voy a actualizar una cosita” 🙂', { t: '*3 horas después* 💀', c: 'y' }], 250);
    await sleep(1400);
    await p.evaluate(() => { const h = document.querySelector('.hero-copy'); h.style.transition = 'opacity .5s, transform .5s'; h.style.opacity = '1'; h.style.transform = 'none'; });
    await caption(p, ['Así que hice MI PROPIO', { t: 'sistema operativo 🌙', c: 'y' }], 470);
    await sleep(1500);
  });

  // 2) La página: se llama MoonOS
  await scene(browser, '2-pagina', WEB, async p => {
    await p.waitForTimeout(1500);
    await caption(p, ['Se llama MoonOS 🌙', { t: 'Linux para jugar, ligero y en español', c: 'small' }], 150);
  }, async p => {
    await sleep(700);
    await p.evaluate(() => { document.documentElement.style.scrollBehavior = 'auto'; });
    await p.evaluate(() => new Promise(res => {
      const target = document.querySelector('#caracteristicas').getBoundingClientRect().top + scrollY - 40;
      const from = scrollY, dur = 3000, t0 = performance.now();
      const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
      (function step(now) { const k = Math.min(1, (now - t0) / dur); scrollTo(0, from + (target - from) * ease(k)); k < 1 ? requestAnimationFrame(step) : res(); })(t0);
    }));
    await caption(p, ['Los drivers se instalan solos 🪄', { t: 'Sí, también los de NVIDIA', c: 'small' }], 330);
    await sleep(1400);
  });

  // 3) Terminal: fastfetch
  await scene(browser, '3-terminal', DEMO, async p => {
    await p.waitForTimeout(2400);
    await p.evaluate(() => document.querySelectorAll('.toast').forEach(t => t.remove()));
    await p.click('.dicon[data-app=terminal]');
    await p.waitForTimeout(300);
    await caption(p, ['Lo primero que hace todo usuario de Linux:'], 430);
  }, async p => {
    await sleep(500);
    await p.click('.term');
    await p.keyboard.type('fastfetch', { delay: 85 * SLOW });
    await sleep(250);
    await p.keyboard.press('Enter');
    await sleep(500);
    await caption(p, ['Lo primero que hace todo usuario de Linux:', { t: 'presumir con fastfetch 🤓', c: 'y' }], 430);
    await sleep(2000);
  });

  // 4) Juegos + modo juego
  await scene(browser, '4-juegos', DEMO, async p => {
    await p.waitForTimeout(2400);
    await p.evaluate(() => document.querySelectorAll('.toast').forEach(t => t.remove()));
    await p.click('.dicon[data-app=games]');
    await p.waitForTimeout(300);
    await caption(p, ['Abres un juego…'], 470);
  }, async p => {
    await sleep(900);
    await p.click('[data-game="0"]');
    await sleep(250);
    await caption(p, ['…y el PC se pone', { t: 'en modo bestia 🏎️💨', c: 'y' }], 150);
    await sleep(400);
    await p.keyboard.press('Space');
    for (const k of ['ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight']) {
      await p.keyboard.down(k); await sleep(650); await p.keyboard.up(k);
    }
    await sleep(300);
  });

  // 5) Instalador
  await scene(browser, '5-instalador', DEMO, async p => {
    await p.waitForTimeout(2400);
    await p.evaluate(() => document.querySelectorAll('.toast').forEach(t => t.remove()));
    await p.click('.dicon[data-app=install]');
    await p.waitForTimeout(300);
    await caption(p, ['Instalarlo es más fácil que…'], 470);
  }, async p => {
    await sleep(800);
    for (let i = 0; i < 4; i++) { await p.click('[data-n=next]'); await sleep(330); }
    await p.click('#i-name');
    await p.keyboard.type('Gamer Lunar', { delay: 45 * SLOW });
    await caption(p, ['Instalarlo es más fácil que…', { t: 'explicarle a tu mamá qué es un kernel 😅', c: 'y' }], 470);
    await p.fill('#i-p1', 'luna'); await p.fill('#i-p2', 'luna');
    await sleep(900);
    await p.click('[data-n=next]'); await sleep(300); await p.click('[data-n=next]');
    await sleep(1400);
  });

  // 6) Final: disponible en 2027
  await scene(browser, '6-final', FINAL, async p => { await p.waitForTimeout(900); await p.reload(); await p.waitForTimeout(50); }, async p => {
    await p.evaluate(() => document.querySelectorAll('*').forEach(e => { if (getComputedStyle(e).animationName !== 'none') { e.style.animation = 'none'; e.offsetWidth; e.style.animation = ''; } }));
    await sleep(4300);
  });

  await browser.close();
})();
