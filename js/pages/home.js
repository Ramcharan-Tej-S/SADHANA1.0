// pages/home.js — the scrollytelling landing "attract mode".
import { sprite } from '../sprites.js';
import { api } from '../api.js';
import { esc, el, els, countUp, toast, withLoader } from '../ui.js';

const STEPS = [
  {
    n: '01',
    icon: 'scroll',
    title: 'FEED IT YOUR SYLLABUS',
    body: 'Drop in a PDF, a photo of the notice board, or plain text. The parser agent reads it and breaks the whole course into units and topics, with an hour estimate on each one.',
  },
  {
    n: '02',
    icon: 'brain',
    title: 'THE JUDGE SCORES EVERY TOPIC',
    body: 'Three passes: assess, critique, then calibrate. Each topic walks out with a difficulty level, a 0-10 score, a confidence value, and the reasoning behind it.',
  },
  {
    n: '03',
    icon: 'calendar',
    title: 'YOU SET THE CLOCK',
    body: 'Exam dates, the hours you are actually free each day, and which of those hours are your peak-focus windows. Hard topics get the good slots.',
  },
  {
    n: '04',
    icon: 'chart',
    title: 'SCORES RE-WEIGHT THE PLAN',
    body: 'Enter your CIE and quiz results. The analyzer finds where you are quietly behind and pushes those subjects up the priority queue.',
  },
  {
    n: '05',
    icon: 'bolt',
    title: 'THE OPTIMIZER BUILDS THE RUN',
    body: 'A full timetable, constrained to your real availability, ordered by difficulty and deadline, with spaced repetition built in so it actually sticks.',
  },
  {
    n: '06',
    icon: 'trophy',
    title: 'IT LEARNS FROM THE RESULT',
    body: 'Predicted readiness against what actually happened. The loop closes, the model recalibrates, and next week\'s plan is sharper than this one\'s.',
  },
];

const LEVELS = [
  { href: '#/setup',       icon: 'book',       title: 'DATA SETUP',     desc: 'Register subjects, upload syllabi, rate your own comfort per subject.', color: 'blue' },
  { href: '#/syllabus',    icon: 'brain',      title: 'SYLLABUS MODEL', desc: 'Every topic scored by a three-pass LLM-as-Judge, with its reasoning shown.', color: 'purple' },
  { href: '#/schedule',    icon: 'calendar',   title: 'SCHEDULE',       desc: 'Exam countdowns and the weekly availability grid that constrains the plan.', color: 'teal' },
  { href: '#/performance', icon: 'chart',      title: 'PERFORMANCE',    desc: 'Log test scores and let the analyzer re-calibrate what matters most.', color: 'orange' },
  { href: '#/optimizer',   icon: 'bolt',       title: 'OPTIMIZER',      desc: 'Generate the timetable, tick sessions off, watch readiness climb.', color: 'green' },
  { href: '#/feedback',    icon: 'trophy',     title: 'FEEDBACK LOOP',  desc: 'Prediction accuracy, coverage trends, and personalised study tips.', color: 'red' },
];

export function renderHome() {
  return `
  <!-- ═══ HERO ═══ -->
  <section class="hero">
    <div class="sprite-row">
      ${sprite('coin', 40, 'bob bd1')}${sprite('star', 40, 'bob bd2')}${sprite('mushroom', 40, 'bob bd3')}
      ${sprite('gem', 40, 'bob bd4')}${sprite('heart', 40, 'bob bd5')}
    </div>
    <h1 class="title-shadow">SADHANA</h1>
    <p class="sub">Your learning path, built around how your mind actually works.<br>
       AI-powered academic support, designed for focus and clarity.</p>
    <div class="row" style="justify-content:center">
      <a class="btn primary" href="#/setup">${sprite('controller', 20)} START GAME</a>
      <button class="btn ghost" id="demo-seed">${sprite('floppy', 20)} LOAD DEMO SAVE</button>
    </div>
    <div class="press-start">▼ SCROLL TO CONTINUE ▼</div>
  </section>

  <div class="ground"></div>

  <!-- ═══ SCOREBOARD ═══ -->
  <section class="scene">
    <div class="wrap">
      <div class="reveal center" style="margin-bottom:34px">
        <h2>HIGH SCORE TABLE</h2>
        <p class="muted">What is loaded into your save file right now.</p>
      </div>
      <div class="grid grid-4 reveal d1" id="home-stats">
        ${statSkeleton()}
      </div>
    </div>
  </section>

  <div class="marquee"><span>
    ★ CHAIN-OF-THOUGHT REASONING ★ LLM-AS-JUDGE DIFFICULTY SCORING ★ CONSTRAINT-AWARE SCHEDULING ★
    SPACED REPETITION ★ ADAPTIVE RE-PLANNING ★ READINESS PREDICTION ★ CHAIN-OF-THOUGHT REASONING ★
    LLM-AS-JUDGE DIFFICULTY SCORING ★ CONSTRAINT-AWARE SCHEDULING ★
  </span></div>

  <!-- ═══ PINNED SCROLLYTELLING ═══ -->
  <section class="scene">
    <div class="wrap">
      <div class="reveal" style="margin-bottom:20px">
        <h2>HOW THE RUN WORKS</h2>
        <p class="muted">Six stages, six agents. Keep scrolling.</p>
      </div>
      <div class="pinned">
        <div class="pinned-stage" id="stage">
          ${STEPS.map((s, i) => `
            <div class="stage-slide ${i === 0 ? 'on' : ''}" data-slide="${i}">
              <div class="center">
                <div>${sprite(s.icon, 132, 'bob')}</div>
                <div class="mono-num" style="margin-top:22px;font-size:15px">${s.n}</div>
                <div class="mono-num" style="margin-top:10px;color:#5A5A72;font-size:10px">${esc(s.title)}</div>
              </div>
            </div>`).join('')}
        </div>
        <div class="pinned-steps" id="steps">
          ${STEPS.map((s, i) => `
            <div class="step ${i === 0 ? 'active' : ''}" data-step="${i}">
              <span class="step-n">STAGE ${s.n}</span>
              <h3>${esc(s.title)}</h3>
              <p>${esc(s.body)}</p>
            </div>`).join('')}
        </div>
      </div>
    </div>
  </section>

  <div class="ground"></div>

  <!-- ═══ LEVEL SELECT ═══ -->
  <section class="scene">
    <div class="wrap">
      <div class="reveal center" style="margin-bottom:34px">
        <h2>LEVEL SELECT</h2>
        <p class="muted">Six screens. Play them in order the first time through.</p>
      </div>
      <div class="grid grid-3">
        ${LEVELS.map((l, i) => `
          <a class="card-link reveal d${(i % 4) + 1}" href="${l.href}">
            <div class="row-tight">
              ${sprite(l.icon, 44, 'bob')}
              <span class="badge ${l.color}">LV ${i + 1}</span>
            </div>
            <div class="cl-title">${esc(l.title)}</div>
            <div class="cl-desc">${esc(l.desc)}</div>
          </a>`).join('')}
      </div>
    </div>
  </section>

  <!-- ═══ AI PATTERNS ═══ -->
  <section class="scene">
    <div class="wrap">
      <div class="reveal center" style="margin-bottom:34px">
        <h2>POWER-UPS EQUIPPED</h2>
        <p class="muted">The AI patterns doing the work under the hood.</p>
      </div>
      <div class="grid grid-3">
        ${[
          ['brain', 'CHAIN-OF-THOUGHT', 'Agents reason step by step before answering — parsing syllabi and predicting readiness out loud, so you can read why.', 'purple'],
          ['target', 'LLM-AS-JUDGE', 'Difficulty gets three passes: an initial score, a critique of that score, then a calibrated final verdict with a confidence value.', 'red'],
          ['bolt',  'ADAPTIVE PLANNING', 'Skip a session or bomb a test and the schedule redistributes itself around what actually happened.', 'green'],
        ].map(([icon, title, body, color], i) => `
          <div class="panel reveal d${i + 1}">
            <div class="panel-head ${color}">${sprite(icon, 22)}<span>${esc(title)}</span></div>
            <p class="muted" style="margin:0">${esc(body)}</p>
          </div>`).join('')}
      </div>
    </div>
  </section>

  <div class="ground"></div>

  <!-- ═══ CTA ═══ -->
  <section class="scene center">
    <div class="wrap reveal">
      <div class="sprite-row" style="margin-bottom:22px">
        ${sprite('qblock', 46, 'bob bd1')}${sprite('flag', 46, 'bob bd3')}${sprite('qblock', 46, 'bob bd5')}
      </div>
      <h2>READY PLAYER ONE?</h2>
      <p class="muted" style="max-width:520px;margin:14px auto 28px">
        Add your subjects, point it at a syllabus, and let the agents build the timetable.
      </p>
      <a class="btn primary" href="#/setup" style="font-size:14px;padding:18px 26px">
        ${sprite('controller', 24)} INSERT COIN
      </a>
    </div>
  </section>

  <footer class="wrap center muted" style="padding:40px 24px 60px;font-size:17px">
    SADHANA &middot; BUILT WITH FASTAPI + OPENROUTER &middot; STUDY YOUR WAY
  </footer>`;
}

function statSkeleton() {
  return ['SUBJECTS', 'TOPICS', 'EXAMS', 'SESSIONS']
    .map(
      (l, i) => `<div class="tile ${['blue', 'purple', 'red', 'green'][i]}">
        ${sprite(['book', 'brain', 'calendar', 'clock'][i], 36, 'bob')}
        <div class="tile-body">
          <div class="tile-label">${l}</div>
          <div class="tile-value" data-stat="${l.toLowerCase()}">0</div>
        </div>
      </div>`
    )
    .join('');
}

/** Wire up everything the landing page needs after it is in the DOM. */
export function mountHome() {
  loadStats();

  el('#demo-seed')?.addEventListener('click', async () => {
    const res = await withLoader('LOADING SAVE FILE', () => api.seed());
    if (!res) return;
    if (res.subjects > 0) {
      toast('ok', 'SAVE LOADED', `${res.subjects} subjects, ${res.topics} topics, ${res.difficulties} difficulty scores.`);
    } else {
      toast('info', 'ALREADY LOADED', 'Demo data is already in the save file.');
    }
    loadStats();
    window.dispatchEvent(new Event('examflow:refresh'));
  });

  mountReveals();
  mountScrolly();
}

async function loadStats() {
  try {
    const s = await api.stats();
    const map = { subjects: s.subjects, topics: s.topics, exams: s.exams, sessions: s.sessions };
    els('[data-stat]').forEach((node) => countUp(node, map[node.dataset.stat] ?? 0));
  } catch {
    /* the scoreboard is decorative — a failed stats call should not break the page */
  }
}

/** Fade-and-rise sections in as they enter the viewport. */
function mountReveals() {
  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          e.target.classList.add('in');
          io.unobserve(e.target);
        }
      });
    },
    { threshold: 0.15, rootMargin: '0px 0px -60px 0px' }
  );
  els('.reveal').forEach((n) => io.observe(n));
}

/** Drive the pinned stage from whichever caption is centred in the viewport. */
function mountScrolly() {
  const steps = els('#steps .step');
  const slides = els('#stage .stage-slide');
  if (!steps.length) return;

  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (!e.isIntersecting) return;
        const i = Number(e.target.dataset.step);
        steps.forEach((s) => s.classList.toggle('active', s === e.target));
        slides.forEach((s) => s.classList.toggle('on', Number(s.dataset.slide) === i));
      });
    },
    { threshold: 0.55 }
  );
  steps.forEach((s) => io.observe(s));
}
