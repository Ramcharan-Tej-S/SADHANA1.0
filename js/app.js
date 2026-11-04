// app.js — hash router, HUD, and the parallax sprite layer.
// SADHANA: Floating background sprites are disabled for a distraction-free environment.
import { sprite } from './sprites.js';
import { api } from './api.js';
import { el, els, esc, toast } from './ui.js';

import { renderHome, mountHome } from './pages/home.js';
import { renderSetup, mountSetup } from './pages/setup.js';
import { renderSyllabus, mountSyllabus } from './pages/syllabus.js';
import { renderSchedule, mountSchedule } from './pages/schedule.js';
import { renderPerformance, mountPerformance } from './pages/performance.js';
import { renderOptimizer, mountOptimizer } from './pages/optimizer.js';
import { renderFeedback, mountFeedback } from './pages/feedback.js';
import { initParkingLotHUD } from './parkingLot.js';

const ROUTES = {
  '#/':            { title: 'HOME',        render: renderHome,        mount: mountHome },
  '#/setup':       { title: 'SETUP',       render: renderSetup,       mount: mountSetup },
  '#/syllabus':    { title: 'SYLLABUS',    render: renderSyllabus,    mount: mountSyllabus },
  '#/schedule':    { title: 'SCHEDULE',    render: renderSchedule,    mount: mountSchedule },
  '#/performance': { title: 'PERFORMANCE', render: renderPerformance, mount: mountPerformance },
  '#/optimizer':   { title: 'OPTIMIZER',   render: renderOptimizer,   mount: mountOptimizer },
  '#/feedback':    { title: 'FEEDBACK',    render: renderFeedback,    mount: mountFeedback },
};

const NAV = [
  ['#/', 'HOME'],
  ['#/setup', '1-SETUP'],
  ['#/syllabus', '2-SYLLABUS'],
  ['#/schedule', '3-SCHEDULE'],
  ['#/performance', '4-SCORES'],
  ['#/optimizer', '5-OPTIMIZER'],
  ['#/feedback', '6-FEEDBACK'],
];

/* ─── HUD ─────────────────────────────────────────────────────────── */
function renderHud() {
  el('#hud').innerHTML = `
    <div class="hud-inner">
      <a class="hud-logo" href="#/">${sprite('controller', 30)}<span>SADHANA</span></a>
      <nav class="hud-nav">
        ${NAV.map(([href, label]) => `<a class="hud-link" href="${href}" data-route="${href}">${esc(label)}</a>`).join('')}
      </nav>
      <div class="hud-tools" id="hud-tools">
        <button class="hud-fx" id="low-energy-toggle" aria-pressed="false"
                title="ADHD Low-Energy Day Adaptation">⚡ ENERGY: NORMAL</button>
      </div>
    </div>
    <div class="hud-progress"><i id="scroll-bar"></i></div>`;
}

async function refreshHudCount() {
  try {
    const rStats = await api.routineStats().catch(() => ({ streak: 0, today: { is_low_energy: 0 } }));
    const eBtn = el('#low-energy-toggle');
    if (eBtn) {
      const isLow = Boolean(rStats.today?.is_low_energy);
      eBtn.setAttribute('aria-pressed', String(isLow));
      eBtn.textContent = isLow ? '🌱 LOW ENERGY: ON' : '⚡ ENERGY: NORMAL';
      eBtn.style.color = isLow ? 'var(--orange)' : '';
      eBtn.style.borderColor = isLow ? 'var(--orange)' : '';
    }
  } catch {
    // Keep UI stable if request fails
  }
}


/* ─── Low-energy toggle ───────────────────────────────────────────── */
function mountLowEnergyToggle() {
  const btn = el('#low-energy-toggle');
  if (!btn) return;
  btn.addEventListener('click', async () => {
    try {
      const cur = await api.todayRoutine().catch(() => ({ is_low_energy: 0 }));
      const newLow = !cur.is_low_energy;
      await api.setEnergyMode(newLow, newLow ? 'low' : 'normal');
      toast(
        'info',
        newLow ? 'LOW-ENERGY MODE ACTIVE' : 'NORMAL ENERGY RESTORED',
        newLow
          ? 'Focus Arena and timetable will soften to 15m micro-sprints. Be kind to your brain today.'
          : 'Pacing returned to standard Pomodoro.',
        5000
      );
      window.dispatchEvent(new Event('examflow:refresh'));
    } catch (e) {
      toast('err', 'FAILED', e.message);
    }
  });
}

/* ─── Routing ─────────────────────────────────────────────────────── */
async function route() {
  const hash = window.location.hash || '#/';
  const r = ROUTES[hash] || ROUTES['#/'];

  els('.hud-link').forEach((a) => a.classList.toggle('active', a.dataset.route === hash));
  document.title = `SADHANA - ${r.title}`;

  el('#view').innerHTML = r.render();
  window.scrollTo({ top: 0, behavior: 'auto' });

  try {
    await r.mount();
  } catch (err) {
    console.error(err);
    toast('err', 'SCREEN CRASHED', err.message);
  }

  // SADHANA: Sprite layer is disabled. Only scroll bar is updated.
  const bar = el('#scroll-bar');
  if (bar) {
    const updateScrollBar = () => {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.width = `${max > 0 ? Math.min(100, (window.scrollY / max) * 100) : 0}%`;
    };
    window.addEventListener('scroll', updateScrollBar, { passive: true });
    updateScrollBar();
  }
  refreshHudCount();
}

/* ─── Parallax sprite layer (DISABLED for SADHANA — distraction-free) ── */
// The FLOATERS array and mountSprites() are preserved here for reference
// but the function is NOT called on boot so no floating icons appear.
const FLOATERS = [
  { name: 'coin',       x: 2.5, y: 12, size: 34, depth: 0.16, cls: 'spin-y' },
  { name: 'star',       x: 95,  y: 20, size: 30, depth: 0.28, cls: 'bob' },
  { name: 'mushroom',   x: 4,   y: 58, size: 38, depth: 0.10, cls: 'bob' },
  { name: 'gem',        x: 96,  y: 66, size: 28, depth: 0.34, cls: 'bob' },
  { name: 'invader',    x: 1.5, y: 36, size: 32, depth: 0.22, cls: 'bob' },
  { name: 'ghost',      x: 94,  y: 44, size: 30, depth: 0.13, cls: 'bob' },
  { name: 'heart',      x: 3,   y: 84, size: 26, depth: 0.30, cls: 'bob' },
  { name: 'qblock',     x: 96,  y: 8,  size: 30, depth: 0.19, cls: 'bob' },
  { name: 'cartridge',  x: 1.5, y: 26, size: 26, depth: 0.36, cls: '' },
  { name: 'bolt',       x: 95,  y: 86, size: 30, depth: 0.24, cls: 'bob' },
  { name: 'potion',     x: 4,   y: 70, size: 26, depth: 0.12, cls: 'bob' },
  { name: 'key',        x: 96,  y: 30, size: 26, depth: 0.27, cls: 'bob' },
];

function mountSprites() {
  // Intentionally not called — sprites disabled for SADHANA's distraction-free environment.
}

/* ─── Konami code easter egg ──────────────────────────────────────── */
const KONAMI = ['ArrowUp','ArrowUp','ArrowDown','ArrowDown','ArrowLeft','ArrowRight','ArrowLeft','ArrowRight','b','a'];
let konamiPos = 0;

function mountKonami() {
  window.addEventListener('keydown', (e) => {
    if (e.key.toLowerCase() === KONAMI[konamiPos].toLowerCase()) {
      konamiPos++;
      if (konamiPos === KONAMI.length) {
        konamiPos = 0;
        document.body.style.setProperty('--paper', '#EAF3FF');
        toast('ok', 'CHEAT ACCEPTED', 'Up up down down left right left right B A. Have some confetti.');
        confettiRain();
      }
    } else {
      konamiPos = e.key === KONAMI[0] ? 1 : 0;
    }
  });
}

function confettiRain() {
  const names = ['coin', 'star', 'heart', 'gem', 'mushroom'];
  for (let i = 0; i < 40; i++) {
    const d = document.createElement('div');
    d.style.cssText = `position:fixed;z-index:9997;pointer-events:none;left:${Math.random() * 100}vw;top:-60px;`;
    d.innerHTML = sprite(names[i % names.length], 26);
    document.body.appendChild(d);
    d.animate(
      [{ transform: 'translateY(0) rotate(0deg)' }, { transform: `translateY(110vh) rotate(${Math.random() * 720 - 360}deg)` }],
      { duration: 2200 + Math.random() * 2200, easing: 'linear' }
    ).onfinish = () => d.remove();
  }
}

/* ─── Boot ────────────────────────────────────────────────────────── */
async function boot() {
  renderHud();
  mountLowEnergyToggle();
  initParkingLotHUD();   // Global Thought Parking Lot HUD button + drawer
  // mountSprites(); — SADHANA: disabled, no floating background sprites
  mountKonami();

  window.addEventListener('hashchange', route);
  window.addEventListener('examflow:refresh', refreshHudCount);
  await route();

  // Warn once if the LLM key is missing — the AI buttons will fail without it.
  try {
    const h = await api.health();
    if (!h.llm_configured) {
      toast(
        'info',
        'NO API KEY',
        'OPENROUTER_API_KEY is not set, so the AI agents are offline. Everything else works — put the key in .env and restart to enable them.',
        11000
      );
    }
  } catch {
    toast('err', 'BACKEND OFFLINE', 'Could not reach the API. Is the server running?');
  }
}

boot();
