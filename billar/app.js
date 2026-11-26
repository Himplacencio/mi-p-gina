"use strict";
/* Línea Guía 8 Bolas — calculadora de tiro para billar.
   Unidades de mesa: ancho W = 1, largo L = 2 (proporción real 1:2). */

const W = 1, L = 2;
const R = 0.026;          // radio de bola (57 mm en mesa de ~2,2 m)
const RAIL = 0.075;       // grosor de la banda dibujada
const EPS = 1e-7;

// Troneras: centro de captura (x, y), radio de captura c, punto de mira (ax, ay), radio dibujado
const POCKETS = [
  { x: -0.01,     y: -0.01,     c: 0.065, ax: 0.014,     ay: 0.014,     r: 0.052 },
  { x: W + 0.01,  y: -0.01,     c: 0.065, ax: W - 0.014, ay: 0.014,     r: 0.052 },
  { x: -0.025,    y: L / 2,     c: 0.060, ax: 0,         ay: L / 2,     r: 0.046 },
  { x: W + 0.025, y: L / 2,     c: 0.060, ax: W,         ay: L / 2,     r: 0.046 },
  { x: -0.01,     y: L + 0.01,  c: 0.065, ax: 0.014,     ay: L - 0.014, r: 0.052 },
  { x: W + 0.01,  y: L + 0.01,  c: 0.065, ax: W - 0.014, ay: L - 0.014, r: 0.052 },
];

const COLORS = {
  0: "#f6f4ea", 1: "#f5c518", 2: "#1e4fd8", 3: "#d62828", 4: "#6a1b9a",
  5: "#f57c00", 6: "#1b7f3b", 7: "#7b2d26", 8: "#141414",
};
const ballColor = (n) => COLORS[n > 8 ? n - 8 : n];

// ---------- Estado ----------
const DEFAULT = () => ({
  balls: [ { n: 0, x: 0.5, y: 1.5 }, { n: 1, x: 0.64, y: 0.62 }, { n: 8, x: 0.42, y: 0.5 } ],
  ang: -Math.PI / 2,
  spin: 0,
  bounces: 2,
  selected: 1,
  auto: { ball: 1, pocket: 1 },
});

let st = load() || DEFAULT();

function load() {
  try {
    const s = JSON.parse(localStorage.getItem("linea-guia-estado"));
    if (s && Array.isArray(s.balls) && s.balls[0] && s.balls[0].n === 0) return s;
  } catch (e) { /* sin almacenamiento */ }
  return null;
}
function save() {
  try { localStorage.setItem("linea-guia-estado", JSON.stringify(st)); } catch (e) { /* ignorar */ }
}

// ---------- Geometría ----------
const norm = (x, y) => { const m = Math.hypot(x, y) || 1; return { x: x / m, y: y / m }; };

/* Traza el recorrido de una bola desde p en dirección d, con rebotes en las bandas.
   Se detiene al tocar otra bola, al caer en una tronera o al agotar los rebotes. */
function trace(p, d, excl, maxBounces) {
  const pts = [{ x: p.x, y: p.y }];
  let px = p.x, py = p.y, dx = d.x, dy = d.y;

  for (let b = 0; b <= maxBounces; b++) {
    let tx = Infinity, ty = Infinity;
    if (dx > EPS) tx = (W - R - px) / dx; else if (dx < -EPS) tx = (R - px) / dx;
    if (dy > EPS) ty = (L - R - py) / dy; else if (dy < -EPS) ty = (R - py) / dy;
    tx = Math.max(tx, 0); ty = Math.max(ty, 0);
    let tMin = Math.min(tx, ty), kind = "wall", idx = -1;

    st.balls.forEach((B, j) => {
      if (excl.includes(j)) return;
      const fx = px - B.x, fy = py - B.y;
      const bb = fx * dx + fy * dy, c = fx * fx + fy * fy - 4 * R * R;
      if (c < 0) return;
      const disc = bb * bb - c;
      if (disc < 0) return;
      const t = -bb - Math.sqrt(disc);
      if (t > EPS && t < tMin) { tMin = t; kind = "ball"; idx = j; }
    });

    POCKETS.forEach((P, k) => {
      const fx = px - P.x, fy = py - P.y;
      const bb = fx * dx + fy * dy, c = fx * fx + fy * fy - P.c * P.c;
      let t;
      if (c < 0) { if (bb >= 0) return; t = 0; }
      else { const disc = bb * bb - c; if (disc < 0) return; t = -bb - Math.sqrt(disc); }
      if (t >= 0 && t <= tMin) { tMin = t; kind = "pocket"; idx = k; }
    });

    px += dx * tMin; py += dy * tMin;
    pts.push({ x: px, y: py });

    if (kind === "ball") return { pts, hit: idx, at: { x: px, y: py }, dir: { x: dx, y: dy } };
    if (kind === "pocket") return { pts, pocket: idx };
    if (b === maxBounces) break;
    if (Math.abs(tx - tMin) < 1e-9) dx = -dx;
    if (Math.abs(ty - tMin) < 1e-9) dy = -dy;
  }
  return { pts };
}

function computeShot() {
  const cue = st.balls[0];
  const d = { x: Math.cos(st.ang), y: Math.sin(st.ang) };
  const res = { cue: trace(cue, d, [0], st.bounces) };
  if (res.cue.hit !== undefined) {
    const j = res.cue.hit, B = st.balls[j], C = res.cue.at, dir = res.cue.dir;
    const n = norm(B.x - C.x, B.y - C.y);
    const dn = dir.x * n.x + dir.y * n.y;
    res.cut = Math.acos(Math.min(1, Math.max(-1, dn))) * 180 / Math.PI;
    res.obj = trace(B, n, [0, j], st.bounces);
    // Blanca tras el impacto: tangente (regla de 90°) + aproximación del efecto
    const k = st.spin > 0 ? 0.55 : 0.75;
    let ax = dir.x - dn * n.x + st.spin * k * dn * n.x;
    let ay = dir.y - dn * n.y + st.spin * k * dn * n.y;
    const m = Math.hypot(ax, ay);
    if (m > 0.02) res.after = trace(C, { x: ax / m, y: ay / m }, [0, j], st.bounces);
    else res.stop = C;
  }
  return res;
}

function autoAim() {
  const a = st.auto;
  if (!a) return;
  const B = st.balls.find((b) => b.n === a.ball);
  const P = POCKETS[a.pocket];
  if (!B || !P) { st.auto = null; return; }
  const u = norm(P.ax - B.x, P.ay - B.y);
  const gx = B.x - u.x * 2 * R, gy = B.y - u.y * 2 * R;   // bola fantasma
  const cue = st.balls[0];
  st.ang = Math.atan2(gy - cue.y, gx - cue.x);
}

// ---------- Dibujo ----------
const canvas = document.getElementById("table");
const ctx = canvas.getContext("2d");
const stage = document.getElementById("stage");
const info = document.getElementById("info");
let view = { s: 1, ox: 0, oy: 0, rot: false, w: 0, h: 0 };

function resize() {
  const w = stage.clientWidth, h = stage.clientHeight, dpr = window.devicePixelRatio || 1;
  if (w < 40 || h < 40) return;
  canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const tw = W + 2 * RAIL, tl = L + 2 * RAIL, pad = 10;
  const rot = w > h * 1.05;
  const s = rot ? Math.min((w - pad * 2) / tl, (h - pad * 2) / tw) : Math.min((w - pad * 2) / tw, (h - pad * 2) / tl);
  const ox = (w - (rot ? tl : tw) * s) / 2, oy = (h - (rot ? tw : tl) * s) / 2;
  view = { s, ox, oy, rot, w, h };
  draw();
}

function S(x, y) {
  const { s, ox, oy, rot } = view;
  return rot ? { x: ox + (y + RAIL) * s, y: oy + (W - x + RAIL) * s } : { x: ox + (x + RAIL) * s, y: oy + (y + RAIL) * s };
}
function T(sx, sy) {
  const { s, ox, oy, rot } = view;
  return rot ? { x: W - ((sy - oy) / s - RAIL), y: (sx - ox) / s - RAIL } : { x: (sx - ox) / s - RAIL, y: (sy - oy) / s - RAIL };
}

function rectT(x0, y0, x1, y1) {
  const a = S(x0, y0), b = S(x1, y1);
  return [Math.min(a.x, b.x), Math.min(a.y, b.y), Math.abs(b.x - a.x), Math.abs(b.y - a.y)];
}

function drawTable() {
  const { s } = view;
  // banda de madera
  const [rx, ry, rw, rh] = rectT(-RAIL, -RAIL, W + RAIL, L + RAIL);
  const g = ctx.createLinearGradient(rx, ry, rx + rw, ry + rh);
  g.addColorStop(0, "#5a3417"); g.addColorStop(0.5, "#7a4a22"); g.addColorStop(1, "#4a2a12");
  ctx.fillStyle = g;
  roundRect(rx, ry, rw, rh, RAIL * s * 0.6); ctx.fill();
  // cojín
  ctx.fillStyle = "#0b5a36";
  ctx.fillRect(...rectT(-0.03, -0.03, W + 0.03, L + 0.03));
  // paño
  const [fx, fy, fw, fh] = rectT(0, 0, W, L);
  const fg = ctx.createRadialGradient(fx + fw / 2, fy + fh / 2, 10, fx + fw / 2, fy + fh / 2, Math.max(fw, fh) * 0.7);
  fg.addColorStop(0, "#17935a"); fg.addColorStop(1, "#0f7346");
  ctx.fillStyle = fg; ctx.fillRect(fx, fy, fw, fh);
  // línea de cabecera y punto de pie
  ctx.strokeStyle = "rgba(255,255,255,.14)"; ctx.lineWidth = 1;
  const h1 = S(0, L * 0.75), h2 = S(W, L * 0.75);
  ctx.beginPath(); ctx.moveTo(h1.x, h1.y); ctx.lineTo(h2.x, h2.y); ctx.stroke();
  const spot = S(W / 2, L * 0.25);
  ctx.fillStyle = "rgba(255,255,255,.3)";
  ctx.beginPath(); ctx.arc(spot.x, spot.y, 2, 0, Math.PI * 2); ctx.fill();
  // diamantes
  ctx.fillStyle = "#f3e3b5";
  const dm = (x, y) => { const p = S(x, y); ctx.beginPath(); ctx.arc(p.x, p.y, Math.max(1.5, s * 0.008), 0, Math.PI * 2); ctx.fill(); };
  for (let i = 1; i < 8; i++) if (i !== 4) { dm(-RAIL * 0.55, (L * i) / 8); dm(W + RAIL * 0.55, (L * i) / 8); }
  for (let i = 1; i < 4; i++) { dm((W * i) / 4, -RAIL * 0.55); dm((W * i) / 4, L + RAIL * 0.55); }
  // troneras
  POCKETS.forEach((P) => {
    const p = S(P.x, P.y);
    ctx.fillStyle = "#050505";
    ctx.beginPath(); ctx.arc(p.x, p.y, P.r * s, 0, Math.PI * 2); ctx.fill();
  });
}

function roundRect(x, y, w, h, r) {
  ctx.beginPath();
  ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
}

function drawBall(b, highlight) {
  const p = S(b.x, b.y), r = R * view.s;
  ctx.save();
  ctx.fillStyle = "rgba(0,0,0,.35)";
  ctx.beginPath(); ctx.arc(p.x + r * 0.15, p.y + r * 0.2, r, 0, Math.PI * 2); ctx.fill();
  const col = ballColor(b.n);
  ctx.beginPath(); ctx.arc(p.x, p.y, r, 0, Math.PI * 2); ctx.closePath();
  ctx.fillStyle = b.n > 8 ? "#f6f4ea" : col; ctx.fill();
  if (b.n > 8) {
    ctx.save(); ctx.clip();
    ctx.fillStyle = col; ctx.fillRect(p.x - r, p.y - r * 0.55, r * 2, r * 1.1);
    ctx.restore();
  }
  const sh = ctx.createRadialGradient(p.x - r * 0.35, p.y - r * 0.4, r * 0.1, p.x, p.y, r);
  sh.addColorStop(0, "rgba(255,255,255,.55)"); sh.addColorStop(0.35, "rgba(255,255,255,0)"); sh.addColorStop(1, "rgba(0,0,0,.35)");
  ctx.fillStyle = sh; ctx.beginPath(); ctx.arc(p.x, p.y, r, 0, Math.PI * 2); ctx.fill();
  if (b.n > 0 && r > 6) {
    ctx.fillStyle = "#fff"; ctx.beginPath(); ctx.arc(p.x, p.y, r * 0.48, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = "#111"; ctx.font = `700 ${Math.round(r * 0.62)}px system-ui, sans-serif`;
    ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(String(b.n), p.x, p.y + r * 0.04);
  }
  if (highlight) {
    ctx.strokeStyle = "#ffd54a"; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.arc(p.x, p.y, r + 3, 0, Math.PI * 2); ctx.stroke();
  }
  ctx.restore();
}

function drawPath(pts, color, width, dash, arrow) {
  if (!pts || pts.length < 2) return;
  ctx.save();
  ctx.strokeStyle = color; ctx.lineWidth = width; ctx.lineCap = "round"; ctx.lineJoin = "round";
  ctx.setLineDash(dash || []);
  ctx.shadowColor = "rgba(0,0,0,.5)"; ctx.shadowBlur = 3;
  ctx.beginPath();
  pts.forEach((q, i) => { const p = S(q.x, q.y); i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y); });
  ctx.stroke();
  if (arrow) {
    const a = S(pts[pts.length - 2].x, pts[pts.length - 2].y), b = S(pts[pts.length - 1].x, pts[pts.length - 1].y);
    const ang = Math.atan2(b.y - a.y, b.x - a.x), h = 9;
    ctx.setLineDash([]); ctx.fillStyle = color;
    ctx.beginPath(); ctx.moveTo(b.x, b.y);
    ctx.lineTo(b.x - h * Math.cos(ang - 0.45), b.y - h * Math.sin(ang - 0.45));
    ctx.lineTo(b.x - h * Math.cos(ang + 0.45), b.y - h * Math.sin(ang + 0.45));
    ctx.closePath(); ctx.fill();
  }
  ctx.restore();
}

function ringPocket(k, color) {
  const P = POCKETS[k], p = S(P.x, P.y);
  ctx.save(); ctx.strokeStyle = color; ctx.lineWidth = 3;
  ctx.beginPath(); ctx.arc(p.x, p.y, P.r * view.s + 3, 0, Math.PI * 2); ctx.stroke(); ctx.restore();
}

function draw() {
  ctx.clearRect(0, 0, view.w, view.h);
  drawTable();
  const shot = computeShot();

  // bolas primero (las líneas van encima)
  st.balls.forEach((b, i) => { if (i) drawBall(b, i === st.selected); });
  drawBall(st.balls[0], false);

  drawPath(shot.cue.pts, "rgba(255,255,255,.95)", 2.2, null, shot.cue.hit === undefined);
  if (shot.cue.hit !== undefined) {
    const g = S(shot.cue.at.x, shot.cue.at.y);
    ctx.save(); ctx.strokeStyle = "rgba(255,255,255,.95)"; ctx.lineWidth = 1.6; ctx.setLineDash([4, 3]);
    ctx.beginPath(); ctx.arc(g.x, g.y, R * view.s, 0, Math.PI * 2); ctx.stroke(); ctx.restore();
    const objCol = shot.obj.pocket !== undefined ? "#4ade80" : "#ffd54a";
    drawPath(shot.obj.pts, objCol, 2.4, null, true);
    if (shot.after) drawPath(shot.after.pts, "rgba(125,211,252,.9)", 1.8, [6, 5], true);
    if (shot.stop) {
      ctx.save(); ctx.fillStyle = "rgba(125,211,252,.9)"; ctx.beginPath(); ctx.arc(g.x, g.y, 3, 0, Math.PI * 2); ctx.fill(); ctx.restore();
    }
    if (shot.obj.pocket !== undefined) ringPocket(shot.obj.pocket, "#4ade80");
  }
  const scratch = [shot.cue, shot.after].find((t) => t && t.pocket !== undefined);
  if (scratch) ringPocket(scratch.pocket, "#f87171");

  updateInfo(shot, !!scratch);
}

function updateInfo(shot, scratch) {
  let html;
  if (shot.cue.hit === undefined) {
    html = scratch ? `<span class="bad">⚠ Blanca a la tronera</span>` : `Sin contacto con bola`;
  } else {
    const n = st.balls[shot.cue.hit].n;
    const cut = shot.cut.toFixed(1);
    const res = shot.obj.pocket !== undefined ? `<span class="ok">✓ Entra</span>` : `<span class="bad">✗ No entra</span>`;
    html = `Bola <b>${n}</b> · corte <b>${cut}°</b><br>${res}${scratch ? ` · <span class="bad">⚠ blanca cae</span>` : ""}`;
  }
  info.innerHTML = html;
}

// ---------- Interacción ----------
let drag = null;

function hitBall(t) {
  const tol = Math.max(R * 1.4, 26 / view.s);
  let best = -1, bd = Infinity;
  st.balls.forEach((b, i) => { const d = Math.hypot(b.x - t.x, b.y - t.y); if (d < tol && d < bd) { bd = d; best = i; } });
  return best;
}
function hitPocket(t) {
  let best = -1, bd = 0.1;
  POCKETS.forEach((P, k) => { const d = Math.hypot(P.x - t.x, P.y - t.y); if (d < bd) { bd = d; best = k; } });
  return best;
}
function canPlace(i, x, y) {
  return st.balls.every((b, j) => j === i || Math.hypot(b.x - x, b.y - y) >= 2 * R - 1e-4);
}
function pt(e) { const r = canvas.getBoundingClientRect(); return T(e.clientX - r.left, e.clientY - r.top); }

canvas.addEventListener("pointerdown", (e) => {
  if (!e.isPrimary) return;
  canvas.setPointerCapture(e.pointerId);
  const t = pt(e);
  const bi = hitBall(t);
  if (bi >= 0) {
    const b = st.balls[bi];
    drag = { type: "ball", i: bi, dx: b.x - t.x, dy: b.y - t.y };
    if (bi > 0) st.selected = bi;
  } else {
    const k = hitPocket(t);
    const sel = st.balls[st.selected];
    if (k >= 0 && sel && st.selected > 0) {
      st.auto = { ball: sel.n, pocket: k };
      autoAim();
      drag = null;
    } else {
      st.auto = null;
      drag = { type: "aim" };
      aimAt(t);
    }
  }
  draw();
});

canvas.addEventListener("pointermove", (e) => {
  if (!drag || !e.isPrimary) return;
  const t = pt(e);
  if (drag.type === "ball") {
    const x = Math.min(W - R, Math.max(R, t.x + drag.dx));
    const y = Math.min(L - R, Math.max(R, t.y + drag.dy));
    const b = st.balls[drag.i];
    if (canPlace(drag.i, x, y)) { b.x = x; b.y = y; }
    else if (canPlace(drag.i, x, b.y)) b.x = x;
    else if (canPlace(drag.i, b.x, y)) b.y = y;
    autoAim();
  } else aimAt(t);
  draw();
});

const endDrag = () => { if (drag) { drag = null; save(); } };
canvas.addEventListener("pointerup", endDrag);
canvas.addEventListener("pointercancel", endDrag);

function aimAt(t) {
  const c = st.balls[0];
  if (Math.hypot(t.x - c.x, t.y - c.y) > 1e-4) st.ang = Math.atan2(t.y - c.y, t.x - c.x);
}

// Ajuste fino (mantener pulsado repite)
document.querySelectorAll("[data-rot]").forEach((btn) => {
  let timer = null, delay = null;
  const step = () => { st.auto = null; st.ang += (parseFloat(btn.dataset.rot) * Math.PI) / 180; draw(); };
  const stop = () => { clearTimeout(delay); clearInterval(timer); timer = delay = null; save(); };
  btn.addEventListener("pointerdown", (e) => {
    e.preventDefault(); step();
    delay = setTimeout(() => { timer = setInterval(step, 50); }, 350);
  });
  ["pointerup", "pointerleave", "pointercancel"].forEach((ev) => btn.addEventListener(ev, stop));
  btn.addEventListener("contextmenu", (e) => e.preventDefault());
});

function bindSeg(id, key) {
  const el = document.getElementById(id);
  const sync = () => el.querySelectorAll("button").forEach((b) => b.classList.toggle("on", Number(b.dataset.v) === st[key]));
  el.addEventListener("click", (e) => {
    const b = e.target.closest("button"); if (!b) return;
    st[key] = Number(b.dataset.v); sync(); draw(); save();
  });
  sync();
  return sync;
}
const syncSpin = bindSeg("spin", "spin");
const syncBounces = bindSeg("bounces", "bounces");

document.getElementById("add").addEventListener("click", () => {
  const used = new Set(st.balls.map((b) => b.n));
  let n = 1; while (used.has(n) && n <= 15) n++;
  if (n > 15) return;
  for (let tries = 0; tries < 300; tries++) {
    const x = R + Math.random() * (W - 2 * R), y = R + Math.random() * (L * 0.6);
    if (canPlace(-1, x, y)) { st.balls.push({ n, x, y }); st.selected = st.balls.length - 1; break; }
  }
  autoAim(); draw(); save();
});

document.getElementById("remove").addEventListener("click", () => {
  if (st.balls.length <= 1) return;
  const i = st.selected > 0 && st.selected < st.balls.length ? st.selected : st.balls.length - 1;
  const [gone] = st.balls.splice(i, 1);
  if (st.auto && st.auto.ball === gone.n) st.auto = null;
  st.selected = st.balls.length > 1 ? st.balls.length - 1 : 0;
  draw(); save();
});

document.getElementById("rack").addEventListener("click", () => {
  st = DEFAULT(); autoAim();
  syncSpin(); syncBounces();
  draw(); save();
});

const help = document.getElementById("help");
let helpSeen = false;
try { helpSeen = localStorage.getItem("linea-guia-ayuda") === "1"; } catch (e) { /* ignorar */ }
if (helpSeen) help.classList.add("hidden");
document.getElementById("helpOk").addEventListener("click", () => {
  help.classList.add("hidden");
  try { localStorage.setItem("linea-guia-ayuda", "1"); } catch (e) { /* ignorar */ }
});
document.getElementById("helpBtn").addEventListener("click", () => help.classList.toggle("hidden"));

window.addEventListener("resize", resize);
new ResizeObserver(resize).observe(stage);
autoAim();
resize();

if ("serviceWorker" in navigator && location.protocol !== "file:") {
  navigator.serviceWorker.register("sw.js").catch(() => {});
}
