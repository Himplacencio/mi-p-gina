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
const CARDS = 'file://' + __dirname + '/cards.html?s=';
// Página web con reportes de EJEMPLO en el tablero de fallas (solo para el video)
const WEB_DEMO_ISSUES = 'file://' + __dirname + '/../moonos-web/test.html';
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
    // Si hay un panel modal abierto, el texto va dentro (los modales tapan todo lo demás)
    (document.querySelector('dialog[open]') || document.body).append(c);
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
  // at(seg): espera hasta el segundo «seg» de la escena (tiempo del video final)
  const at = async sec => { const w = t0 * 1000 + sec * 1000 * SLOW - Date.now(); if (w > 0) await new Promise(r => setTimeout(r, w)); };
  await act(p, at);
  const t1 = Date.now() / 1000;
  await cdp.send('Page.stopScreencast');
  await ctx.close();
  fs.writeFileSync(path.join(dir, 'frames.json'), JSON.stringify({ frames, start: t0, end: t1 }));
  console.log(`${name}: ${frames.length} cuadros, ${(t1 - t0).toFixed(1)} s`);
}

// Duración de cada escena = lo que dura su frase en la voz (+0,25 s que se come la transición)
const ALIGN = JSON.parse(fs.readFileSync(__dirname + '/voice-align.json', 'utf8')).durs;
const X = 0.25;
const DUR = name => ALIGN[name] + (name === '11-final' ? 1.2 : X);

(async () => {
  if (!ONLY) fs.rmSync(OUT, { recursive: true, force: true }); else fs.rmSync(path.join(OUT, ONLY), { recursive: true, force: true });
  const browser = await chromium.launch();
  const clearToasts = p => p.evaluate(() => document.querySelectorAll('.toast').forEach(t => t.remove()));
  const scrollTo = (p, sel, ms) => p.evaluate(({ sel, ms }) => new Promise(res => {
    document.documentElement.style.scrollBehavior = 'auto';
    const target = document.querySelector(sel).getBoundingClientRect().top + scrollY - 40;
    const from = scrollY, t0 = performance.now();
    const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    (function step() { const k = Math.min(1, (performance.now() - t0) / ms); window.scrollTo(0, from + (target - from) * ease(k)); k < 1 ? requestAnimationFrame(step) : res(); })();
  }), { sel, ms });

  // 01 GANCHO  "Windows: solo voy a actualizar una cosita… tres horas después. Así que hice mi propio sistema operativo."
  await scene(browser, '01-gancho', WEB, async p => {
    await p.waitForTimeout(1500);
    await p.evaluate(() => { const h = document.querySelector('.hero-copy'); h.style.transition = 'none'; h.style.opacity = '0'; h.style.transform = 'translateY(24px)'; });
    await p.waitForTimeout(200);
  }, async (p, at) => {
    await caption(p, ['Windows: “solo voy a actualizar una cosita” 🙂'], 250);
    await p.evaluate(() => { const m = document.querySelector('.big-moon'); m.style.animation = 'none'; m.offsetWidth; m.style.animation = ''; });
    await at(3.9);
    await caption(p, ['Windows: “solo voy a actualizar una cosita” 🙂', { t: '*3 horas después* 💀', c: 'y' }], 250);
    await at(5.55);
    await p.evaluate(() => { const h = document.querySelector('.hero-copy'); h.style.transition = 'opacity .5s, transform .5s'; h.style.opacity = '1'; h.style.transform = 'none'; });
    await caption(p, ['Así que hice MI PROPIO', { t: 'sistema operativo 🌙', c: 'y' }], 470);
    await at(DUR('01-gancho'));
  });

  // 02-04 Tarjetas sincronizadas con las pausas de la voz
  const card = (name, id, times) => scene(browser, name, CARDS + id, async p => { await p.waitForTimeout(600); }, async (p, at) => {
    await p.evaluate(t => window.playAt(t), times);
    await at(DUR(name));
  });
  await card('02-intro', 'intro', [0, 250, 900, 3000, 5100]);
  await card('03-problema', 'problema', [0, 700, 3300, 6000, 8900]);
  await card('04-motivo', 'motivo', [0, 2100, 5300, 7300, 10300, 11800]);

  // 05 La página  "Esta es su página. Cuando abres un juego, el sistema se dedica solo a él."
  await scene(browser, '05-pagina', WEB, async p => {
    await p.waitForTimeout(1500);
    await caption(p, ['Esta es su página 👀', { t: 'Linux para jugar, ligero y en español', c: 'small' }], 150);
  }, async (p, at) => {
    await at(0.4);
    const sc = scrollTo(p, '#caracteristicas', 2600);
    await at(1.5);
    await caption(p, ['Modo juego automático ⚡', { t: 'Abres un juego y el PC se dedica solo a él', c: 'small' }], 330);
    await sc;
    await at(DUR('05-pagina'));
  });

  // 06 Terminal  "Y sí, lo primero que hice fue presumir con fast fetch."
  await scene(browser, '06-terminal', DEMO, async p => {
    await p.waitForTimeout(2400); await clearToasts(p);
    await p.click('.dicon[data-app=terminal]'); await p.waitForTimeout(300);
    await p.click('.term');
    await caption(p, ['Lo primero que hace todo usuario de Linux:'], 430);
  }, async (p, at) => {
    await p.keyboard.type('fastfetch', { delay: 45 * SLOW });
    await p.keyboard.press('Enter');
    await at(1.7);
    await caption(p, ['Lo primero que hace todo usuario de Linux:', { t: 'presumir con fastfetch 🤓', c: 'y' }], 430);
    await at(DUR('06-terminal'));
  });

  // 07 Drivers  "¿Nvidia, AMD o Intel? MoonOS lo detecta solo."
  await scene(browser, '07-drivers', DEMO, async p => {
    await p.waitForTimeout(2400); await clearToasts(p);
    await p.click('.dicon[data-app=drivers]'); await p.waitForTimeout(300);
    await caption(p, ['¿NVIDIA, AMD o Intel?'], 500);
  }, async (p, at) => {
    await at(0.9); await p.click('[data-g=amd]');
    await at(2.1);
    await caption(p, ['¿NVIDIA, AMD o Intel?', { t: 'MoonOS lo detecta solo 🪄', c: 'y' }], 500);
    await p.click('#d-run');
    await at(DUR('07-drivers'));
  });

  // 08 Juegos  "Abres un juego… y el PC se pone en modo bestia."
  await scene(browser, '08-juegos', DEMO, async p => {
    await p.waitForTimeout(2400); await clearToasts(p);
    await p.click('.dicon[data-app=games]'); await p.waitForTimeout(300);
    await caption(p, ['Abres un juego…'], 470);
  }, async (p, at) => {
    await at(0.9); await p.click('[data-game="0"]');
    await at(1.15);
    await caption(p, ['…y el PC se pone', { t: 'en modo bestia 🏎️💨', c: 'y' }], 150);
    await p.keyboard.press('Space');
    for (const [k, t] of [['ArrowLeft', 1.9], ['ArrowRight', 2.6], ['ArrowLeft', 3.3]]) { await p.keyboard.down(k); await at(t); await p.keyboard.up(k); }
    await at(DUR('08-juegos'));
  });

  // 09 Instalador  "Instalarlo es más fácil que explicarle a tu mamá qué es un kernel."
  await scene(browser, '09-instalador', DEMO, async p => {
    await p.waitForTimeout(2400); await clearToasts(p);
    await p.click('.dicon[data-app=install]'); await p.waitForTimeout(300);
    await caption(p, ['Instalarlo es más fácil que…'], 470);
  }, async (p, at) => {
    for (let i = 0; i < 4; i++) { await at(0.2 + i * 0.25); await p.click('[data-n=next]'); }
    await p.fill('#i-name', 'Gamer Lunar'); await p.fill('#i-p1', 'luna'); await p.fill('#i-p2', 'luna');
    await at(1.5);
    await caption(p, ['Instalarlo es más fácil que…', { t: 'explicarle a tu mamá qué es un kernel 😅', c: 'y' }], 470);
    await at(2.4); await p.click('[data-n=next]');
    await at(2.8); await p.click('[data-n=next]');
    await at(DUR('09-instalador'));
  });

  // 10 Comunidad  "Y si encuentras una falla, la reportas, todos la ven… y la ves pasar a solucionada."
  await scene(browser, '10-comunidad', WEB_DEMO_ISSUES, async p => {
    await p.waitForTimeout(1500);
    await caption(p, ['¿Encuentras una falla? 🐛'], 300);
  }, async (p, at) => {
    await at(0.9); await p.click('#fab');
    await at(1.6);
    await caption(p, ['La reportas y todos la ven 👀'], 520);
    await at(3.4);
    await caption(p, ['La reportas y todos la ven 👀', { t: '…y la ves pasar a ✓ solucionada', c: 'y' }], 520);
    await at(DUR('10-comunidad'));
  });

  // 11 Final  "Llega en dos mil veintisiete. Síguenos para verlo nacer."
  await scene(browser, '11-final', FINAL, async p => { await p.waitForTimeout(900); await p.reload(); await p.waitForTimeout(50); }, async (p, at) => {
    await p.evaluate(() => document.querySelectorAll('*').forEach(e => { if (getComputedStyle(e).animationName !== 'none') { e.style.animation = 'none'; e.offsetWidth; e.style.animation = ''; } }));
    await at(DUR('11-final'));
  });

  await browser.close();
})();
