// ui.js — shared arcade UI kit: markup helpers, toasts, loader, pixel charts.
import { sprite } from './sprites.js';

/* ─── Escaping ──────────────────────────────────────────────────────
   Everything that reaches innerHTML goes through esc(): topic names and
   AI reasoning are model/user supplied and must never be parsed as HTML. */
export function esc(v) {
  if (v === null || v === undefined) return '';
  return String(v)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

/** Truncate to n chars, appending an ellipsis only when something was cut. */
export const trunc = (v, n) => {
  const t = String(v ?? '');
  return t.length > n ? t.slice(0, n - 1).trimEnd() + '…' : t;
};

export const el = (sel, root = document) => root.querySelector(sel);
export const els = (sel, root = document) => [...root.querySelectorAll(sel)];

/* ─── Toasts ─────────────────────────────────────────────────────── */
const TOAST_ICON = { ok: 'onelife', err: 'skull', info: 'star' };

export function toast(kind, title, msg = '', ms = 5200) {
  const host = el('#toasts');
  const node = document.createElement('div');
  node.className = `toast ${kind}`;
  node.innerHTML =
    `${sprite(TOAST_ICON[kind] || 'star', 30, 'bob')}
     <div class="grow"><span class="t-title">${esc(title)}</span>
     ${msg ? `<div class="t-msg">${esc(msg)}</div>` : ''}</div>`;
  host.appendChild(node);
  setTimeout(() => {
    node.style.transition = 'opacity .3s';
    node.style.opacity = '0';
    setTimeout(() => node.remove(), 320);
  }, ms);
}

/* ─── Full-screen loader for long AI calls ───────────────────────── */
const LOADING_LINES = [
  'CONSULTING THE ORACLE',
  'ROLLING FOR INITIATIVE',
  'SPAWNING STUDY AGENTS',
  'CALIBRATING DIFFICULTY',
  'READING THE SCROLLS',
  'CHARGING SPECIAL MOVE',
  'THIS CAN TAKE A MINUTE',
  'DO NOT TURN OFF THE CONSOLE',
];

let loaderTimer = null;

export function showLoader(title = 'LOADING') {
  hideLoader();
  const node = document.createElement('div');
  node.className = 'loading';
  node.id = 'loader';
  node.innerHTML =
    `<div class="sprite-row">
       ${sprite('brain', 44, 'bob bd1')}${sprite('bolt', 44, 'bob bd2')}${sprite('coin', 44, 'bob bd3')}
     </div>
     <div class="l-title">${esc(title)}...</div>
     <div class="loading-bar"><i></i></div>
     <div class="l-sub" id="loader-sub">${LOADING_LINES[0]}</div>`;
  document.body.appendChild(node);
  let i = 0;
  loaderTimer = setInterval(() => {
    i = (i + 1) % LOADING_LINES.length;
    const sub = el('#loader-sub');
    if (sub) sub.textContent = LOADING_LINES[i];
  }, 1900);
}

export function hideLoader() {
  clearInterval(loaderTimer);
  const node = el('#loader');
  if (node) node.remove();
}

/** Run an async action behind the loader, reporting failures as a toast. */
export async function withLoader(title, fn) {
  showLoader(title);
  try {
    return await fn();
  } catch (err) {
    toast('err', 'GAME OVER', err.message);
    return null;
  } finally {
    hideLoader();
  }
}

/* ─── Markup helpers ─────────────────────────────────────────────── */
export const badge = (text, kind = '') =>
  `<span class="badge ${esc(kind)}">${esc(text)}</span>`;

export const tile = (label, value, sub = '', color = 'blue', icon = 'coin') =>
  `<div class="tile ${color}">
     ${sprite(icon, 36, 'bob')}
     <div class="tile-body">
       <div class="tile-label">${esc(label)}</div>
       <div class="tile-value">${esc(value)}</div>
       ${sub ? `<div class="tile-sub">${esc(sub)}</div>` : ''}
     </div>
   </div>`;

export function meter(pct) {
  const v = Math.max(0, Math.min(100, Number(pct) || 0));
  const cls = v >= 60 ? '' : v >= 30 ? 'mid' : 'low';
  return `<span class="meter ${cls}"><i style="width:${v}%"></i></span>`;
}

export const panel = (title, bodyHtml, color = '', icon = '') =>
  `<section class="panel">
     ${title ? `<div class="panel-head ${color}">${icon ? sprite(icon, 22) : ''}<span>${esc(title)}</span></div>` : ''}
     ${bodyHtml}
   </section>`;

/**
 * A panel that stays shut until asked for. Native <details> so keyboard and
 * screen readers get the toggle behaviour for free.
 * @param {boolean} open  start expanded
 * @param {string}  note  small right-aligned hint in the header (e.g. a count)
 */
export const collapsible = (title, bodyHtml, { open = false, color = '', icon = '', note = '' } = {}) =>
  `<details class="fold" ${open ? 'open' : ''}>
     <summary class="panel-head ${esc(color)}">
       ${icon ? sprite(icon, 22) : ''}
       <span>${esc(title)}</span>
       ${note ? `<span class="fold-note">${esc(note)}</span>` : ''}
       <span class="fold-caret" aria-hidden="true"></span>
     </summary>
     <div class="fold-body">${bodyHtml}</div>
   </details>`;

export const dialogue = (label, text, icon = 'brain') =>
  `<div class="dialogue">
     <div class="dialogue-label">${sprite(icon, 22)}<span>${esc(label)}</span></div>
     <div>${esc(text)}</div>
   </div>`;

export const empty = (title, msg, icon = 'ghost') =>
  `<div class="empty">
     ${sprite(icon, 52, 'bob')}
     <span class="display">${esc(title)}</span>
     <div>${esc(msg)}</div>
   </div>`;

export const unitBar = (text, icon = 'brick') =>
  `<div class="unit-bar">${sprite(icon, 18)}<span>${esc(text)}</span></div>`;

export const pageTitle = (level, title, subtitle, icon) =>
  `<div class="level-tag">LEVEL ${esc(level)}</div>
   <div class="page-title">${sprite(icon, 46, 'bob')}<h1>${esc(title)}</h1></div>
   <p class="muted" style="margin:0 0 26px">${esc(subtitle)}</p>`;

/** Tab strip. Returns HTML; wire it with mountTabs(). */
export function tabs(id, names) {
  return `<div class="tabs" id="${esc(id)}">${names
    .map((n, i) => `<button class="tab ${i === 0 ? 'active' : ''}" data-tab="${i}">${esc(n)}</button>`)
    .join('')}</div>`;
}

export function mountTabs(id, onChange) {
  const strip = el(`#${id}`);
  if (!strip) return;
  strip.addEventListener('click', (e) => {
    const btn = e.target.closest('.tab');
    if (!btn) return;
    els('.tab', strip).forEach((t) => t.classList.toggle('active', t === btn));
    onChange(Number(btn.dataset.tab));
  });
}

/* ─── Pixel charts (SVG, no chart library) ───────────────────────── */
const INK = '#1A1A2E';
export const CHART_COLORS = {
  blue: '#2A6FDB', red: '#E63946', green: '#3FA34D',
  yellow: '#FFC94A', purple: '#7B4FBF', teal: '#2AB7B0', orange: '#F4801F',
};
const SERIES = ['blue', 'purple', 'teal', 'orange', 'green', 'red'];

/**
 * Horizontal bar chart drawn as chunky blocks with hard shadows.
 * rows: [{label, value, max?, color?}]
 */
export function barChart(rows, { max = 100, unit = '%' } = {}) {
  if (!rows.length) return '';
  const rowH = 46, pad = 10, labelW = 150, barW = 520;
  const h = rows.length * rowH + pad * 2;
  const w = labelW + barW + 90;
  let out = `<svg class="chart" viewBox="0 0 ${w} ${h}" shape-rendering="crispEdges" role="img">`;
  rows.forEach((r, i) => {
    const y = pad + i * rowH;
    const cap = Math.max(0, Math.min(r.max ?? max, Number(r.value) || 0));
    const len = Math.max(4, Math.round((cap / (r.max ?? max)) * barW));
    const fill = CHART_COLORS[r.color] || CHART_COLORS[SERIES[i % SERIES.length]];
    out +=
      `<text x="0" y="${y + 22}" font-family="VT323, monospace" font-size="20" fill="${INK}">${esc(
        String(r.label).slice(0, 20)
      )}</text>` +
      `<rect x="${labelW}" y="${y + 6}" width="${barW}" height="26" fill="#F5EAD0" stroke="${INK}" stroke-width="3"/>` +
      `<rect x="${labelW + 4}" y="${y + 10}" width="${len}" height="18" fill="${fill}"/>` +
      `<text x="${labelW + barW + 12}" y="${y + 26}" font-family="'Press Start 2P', monospace" font-size="11" fill="${INK}">${esc(
        Math.round(cap) + unit
      )}</text>`;
  });
  return out + '</svg>';
}

/**
 * Grouped two-series bar chart (e.g. expected vs actual).
 * rows: [{label, a, b}]
 */
export function dualBarChart(rows, labelA = 'A', labelB = 'B') {
  if (!rows.length) return '';
  const rowH = 62, pad = 10, labelW = 150, barW = 500;
  const h = rows.length * rowH + pad * 2;
  const w = labelW + barW + 90;
  let out = `<svg class="chart" viewBox="0 0 ${w} ${h}" shape-rendering="crispEdges" role="img">`;
  rows.forEach((r, i) => {
    const y = pad + i * rowH;
    const la = Math.max(3, Math.round((Math.min(100, r.a) / 100) * barW));
    const lb = Math.max(3, Math.round((Math.min(100, r.b) / 100) * barW));
    out +=
      `<text x="0" y="${y + 30}" font-family="VT323, monospace" font-size="20" fill="${INK}">${esc(
        String(r.label).slice(0, 20)
      )}</text>` +
      `<rect x="${labelW}" y="${y + 4}" width="${la}" height="20" fill="${CHART_COLORS.purple}" stroke="${INK}" stroke-width="3"/>` +
      `<rect x="${labelW}" y="${y + 30}" width="${lb}" height="20" fill="${CHART_COLORS.blue}" stroke="${INK}" stroke-width="3"/>` +
      `<text x="${labelW + Math.max(la, lb) + 12}" y="${y + 21}" font-family="'Press Start 2P', monospace" font-size="9" fill="${INK}">${Math.round(r.a)}%</text>` +
      `<text x="${labelW + Math.max(la, lb) + 12}" y="${y + 47}" font-family="'Press Start 2P', monospace" font-size="9" fill="${INK}">${Math.round(r.b)}%</text>`;
  });
  out += '</svg>';
  return (
    out +
    `<div class="legend" style="margin-top:10px">
       <span><i style="background:${CHART_COLORS.purple}"></i>${esc(labelA)}</span>
       <span><i style="background:${CHART_COLORS.blue}"></i>${esc(labelB)}</span>
     </div>`
  );
}

/** Stacked difficulty distribution as a single segmented block bar. */
export function stackBar(parts) {
  const total = parts.reduce((s, p) => s + p.value, 0) || 1;
  const w = 600, h = 42;
  let x = 3;
  let out = `<svg class="chart" viewBox="0 0 ${w} ${h}" shape-rendering="crispEdges" role="img">
    <rect x="0" y="0" width="${w}" height="${h}" fill="#F5EAD0" stroke="${INK}" stroke-width="3"/>`;
  parts.forEach((p) => {
    const seg = Math.round((p.value / total) * (w - 6));
    if (seg <= 0) return;
    out += `<rect x="${x}" y="3" width="${seg}" height="${h - 6}" fill="${CHART_COLORS[p.color]}" stroke="${INK}" stroke-width="3"/>`;
    if (seg > 46) {
      out += `<text x="${x + seg / 2}" y="${h / 2 + 5}" text-anchor="middle" font-family="'Press Start 2P', monospace" font-size="10" fill="#fff">${p.value}</text>`;
    }
    x += seg;
  });
  out += '</svg>';
  return (
    out +
    `<div class="legend" style="margin-top:12px">${parts
      .map((p) => `<span><i style="background:${CHART_COLORS[p.color]}"></i>${esc(p.label)} (${p.value})</span>`)
      .join('')}</div>`
  );
}

/** Coverage as a row of hearts — full, half, empty. */
export function heartMeter(pct, count = 10) {
  const filled = Math.round((Math.max(0, Math.min(100, pct)) / 100) * count);
  let out = '<div class="row-tight">';
  for (let i = 0; i < count; i++) {
    out += `<span style="opacity:${i < filled ? 1 : 0.22}">${sprite('heart', 26)}</span>`;
  }
  return out + `<span class="mono-num" style="margin-left:8px">${Math.round(pct)}%</span></div>`;
}

/** RPG-style stat block: one labelled meter per entry. */
export function statBlock(rows) {
  return rows
    .map(
      (r) => `<div style="margin-bottom:14px">
        <div class="spread" style="margin-bottom:5px">
          <span class="mono-num">${esc(String(r.label).slice(0, 26))}</span>
          <span class="mono-num" style="color:${r.value >= 60 ? CHART_COLORS.green : r.value >= 30 ? CHART_COLORS.orange : CHART_COLORS.red}">${Math.round(r.value)}%</span>
        </div>
        ${meter(r.value)}
        ${r.sub ? `<div class="tiny muted" style="margin-top:4px">${esc(r.sub)}</div>` : ''}
      </div>`
    )
    .join('');
}

/**
 * Radar / spider chart — one spoke per entry, drawn with crisp edges and
 * square vertex markers so it sits with the rest of the pixel chart set.
 * rows: [{label, value}]
 */
export function radarChart(rows, { max = 10, color = 'purple', unit = '' } = {}) {
  const n = rows.length;
  if (n < 3) return '';

  const w = 760, h = 560;
  const cx = w / 2, cy = h / 2 + 6;
  const R = 178;
  const fill = CHART_COLORS[color] || CHART_COLORS.purple;

  const at = (i, r) => {
    const a = -Math.PI / 2 + (i * 2 * Math.PI) / n;
    return [cx + Math.cos(a) * r, cy + Math.sin(a) * r];
  };

  let out = `<svg class="chart" viewBox="0 0 ${w} ${h}" role="img" aria-label="Radar chart">`;

  // Concentric rings — polygons, not circles, so the grid stays angular.
  for (let ring = 1; ring <= 4; ring++) {
    const r = (R / 4) * ring;
    const pts = Array.from({ length: n }, (_, i) => at(i, r).join(',')).join(' ');
    out += `<polygon points="${pts}" fill="${ring === 4 ? '#FFFFFF' : 'none'}" stroke="#D9CDAF" stroke-width="${ring === 4 ? 3 : 2}"/>`;
  }

  // Spokes
  for (let i = 0; i < n; i++) {
    const [x, y] = at(i, R);
    out += `<line x1="${cx}" y1="${cy}" x2="${x}" y2="${y}" stroke="#D9CDAF" stroke-width="2"/>`;
  }

  // Scale ticks along the first spoke (pointing up)
  for (let ring = 1; ring <= 4; ring++) {
    const v = (max / 4) * ring;
    out += `<text x="${cx + 6}" y="${cy - (R / 4) * ring + 5}" font-family="VT323, monospace" font-size="16" fill="#9A9AB0">${Math.round(v)}</text>`;
  }

  // The data polygon
  const dataPts = rows.map((r, i) => at(i, (Math.max(0, Math.min(max, Number(r.value) || 0)) / max) * R));
  out += `<polygon points="${dataPts.map((p) => p.join(',')).join(' ')}" fill="${fill}" fill-opacity="0.28" stroke="${fill}" stroke-width="4" stroke-linejoin="miter"/>`;
  dataPts.forEach(([x, y]) => {
    out += `<rect x="${x - 5}" y="${y - 5}" width="10" height="10" fill="${fill}" stroke="${INK}" stroke-width="3"/>`;
  });

  // Labels, anchored so they never run back over the plot
  rows.forEach((r, i) => {
    const [x, y] = at(i, R + 22);
    const dx = x - cx;
    const anchor = Math.abs(dx) < 24 ? 'middle' : dx > 0 ? 'start' : 'end';
    out +=
      `<text x="${x}" y="${y + 5}" text-anchor="${anchor}" font-family="VT323, monospace" ` +
      `font-size="18" fill="${INK}">${esc(trunc(r.label, 18))}` +
      `<title>${esc(r.label)}: ${Math.round(r.value)}${esc(unit)}</title></text>`;
  });

  return out + '</svg>';
}

/** Step line chart with square markers, drawn blocky. */
export function lineChart(points, { label = '' } = {}) {
  if (points.length < 2) return '';
  const w = 620, h = 220, padL = 44, padB = 34, padT = 14, padR = 14;
  const plotW = w - padL - padR, plotH = h - padT - padB;
  const maxV = Math.max(100, ...points.map((p) => p.y));
  const stepX = plotW / (points.length - 1);
  const xy = points.map((p, i) => [padL + i * stepX, padT + plotH - (p.y / maxV) * plotH]);

  let out = `<svg class="chart" viewBox="0 0 ${w} ${h}" shape-rendering="crispEdges" role="img">`;
  for (let g = 0; g <= 4; g++) {
    const y = padT + (plotH / 4) * g;
    out += `<line x1="${padL}" y1="${y}" x2="${w - padR}" y2="${y}" stroke="#D9CDAF" stroke-width="2"/>`;
    out += `<text x="0" y="${y + 6}" font-family="VT323, monospace" font-size="17" fill="#5A5A72">${Math.round(maxV - (maxV / 4) * g)}</text>`;
  }
  out += `<polyline fill="none" stroke="${CHART_COLORS.blue}" stroke-width="4" points="${xy.map((p) => p.join(',')).join(' ')}"/>`;
  xy.forEach(([x, y]) => {
    out += `<rect x="${x - 6}" y="${y - 6}" width="12" height="12" fill="${CHART_COLORS.yellow}" stroke="${INK}" stroke-width="3"/>`;
  });
  points.forEach((p, i) => {
    if (points.length > 8 && i % 2) return;
    out += `<text x="${xy[i][0]}" y="${h - 10}" text-anchor="middle" font-family="VT323, monospace" font-size="16" fill="#5A5A72">${esc(p.x)}</text>`;
  });
  out += '</svg>';
  return label ? `<div class="mono-num" style="margin-bottom:8px">${esc(label)}</div>${out}` : out;
}

/* ─── Misc ───────────────────────────────────────────────────────── */
export function fmtDate(iso) {
  try {
    // Pinned to en-GB: the rest of the UI is English, so a localised date
    // string would read as a different language mid-sentence.
    const d = new Date(iso + 'T00:00:00');
    return d.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' });
  } catch { return iso; }
}

export function daysUntil(iso) {
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const target = new Date(iso + 'T00:00:00');
  return Math.round((target - today) / 86400000);
}

export const todayISO = () => new Date().toISOString().slice(0, 10);

/** Count a number up to its target, arcade score style. */
export function countUp(node, target, ms = 900) {
  const start = performance.now();
  const from = 0;
  function tick(now) {
    const t = Math.min(1, (now - start) / ms);
    node.textContent = Math.round(from + (target - from) * t).toLocaleString();
    if (t < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}
