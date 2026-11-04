// pages/optimizer.js — LEVEL 5: generate the timetable, run it, track readiness.
import { sprite } from '../sprites.js';
import { api } from '../api.js';
import {
  esc, el, els, badge, tile, empty, panel, dialogue, pageTitle,
  tabs, mountTabs, statBlock, heartMeter, toast, withLoader, fmtDate,
  collapsible, radarChart, meter,
} from '../ui.js';
import { audioController, AudioMode } from '../audio.js';
import { addThought as globalParkThought, removeThought as globalRemoveThought, loadAll as loadGlobalParkingLot } from '../parkingLot.js';
import { isBlockerEnabled, showLockdownShield, renderBlockerSetup, mountBlockerSetup } from '../distractionBlocker.js';

let subjects = [];

export function renderOptimizer() {
  return `<div class="page"><div class="wrap">
    ${pageTitle(5, 'OPTIMIZER', 'The AI builds the run. You play it, one session at a time.', 'bolt')}
    <div id="opt-stats" class="grid grid-4" style="margin-bottom:26px"></div>
    ${tabs('opt-tabs', ['TIMETABLE', 'READINESS', 'GENERATE'])}
    <div id="opt-body"></div>
  </div></div>`;
}

export async function mountOptimizer() {
  subjects = await api.subjects().catch(() => []);
  if (!subjects.length) {
    el('#opt-body').innerHTML = empty('NO SUBJECTS', 'Register subjects in Data Setup first.');
    el('#opt-stats').innerHTML = '';
    return;
  }
  mountTabs('opt-tabs', show);
  show(0);
}

async function refreshStats() {
  const sessions = await api.sessions().catch(() => []);
  const studySessions = sessions.filter((s) => s.session_type !== 'break');
  const done = studySessions.filter((s) => s.status === 'completed').length;
  const planned = studySessions.filter((s) => s.status === 'planned').length;
  const skipped = studySessions.filter((s) => s.status === 'skipped').length;
  const breaks = sessions.filter((s) => s.session_type === 'break').length;
  const pct = studySessions.length ? Math.round((done / studySessions.length) * 100) : 0;
  el('#opt-stats').innerHTML =
    tile('Study Blocks', studySessions.length, breaks ? `${breaks} breaks scheduled` : '', 'blue', 'calendar') +
    tile('Completed', done, pct + '% of study work', 'green', 'trophy') +
    tile('Planned', planned, '', 'teal', 'clock') +
    tile('Skipped', skipped, '', 'red', 'ghost');
  return sessions;
}

async function show(idx) {
  const host = el('#opt-body');
  host.innerHTML = '<div class="empty">LOADING...</div>';
  const sessions = await refreshStats();
  if (idx === 0) tabTimetable(host, sessions, await api.exams(true).catch(() => []), await api.todayRoutine().catch(() => ({})));
  else if (idx === 1) await tabReadiness(host, sessions);
  else await tabGenerate(host, sessions);
}

/* ─── Tab 1: the timetable ───────────────────────────────────────── */
function tabTimetable(host, sessions, exams = [], todayRoutine = {}) {
  if (!sessions.length) {
    host.innerHTML = empty('NO PLAN YET', 'Nothing scheduled. Head to the Generate tab and let the optimizer build your run.', 'qblock');
    return;
  }

  const dates = [...new Set(sessions.map((s) => s.session_date))].sort();
  const todayStr = new Date().toISOString().slice(0, 10);
  const studySessions = sessions.filter((s) => s.session_type !== 'break');
  const skipped = studySessions.filter((s) => s.status === 'skipped').length;

  const isLowEnergy = Boolean(todayRoutine?.is_low_energy);

  host.innerHTML = `<div class="stack">
    ${
      isLowEnergy
        ? `<div class="panel" style="border:3px solid var(--orange);background:#FFFDF0;padding:14px 18px">
            <div class="spread">
              <div>
                <span class="mono-num" style="color:var(--orange);font-size:12px">🌱 ADHD LOW-ENERGY DAY ADAPTATION ACTIVE</span>
                <p class="muted tiny" style="margin:4px 0 0">
                  Executive reserves are low today. Focus Arena defaults to gentle 15m micro-sprints.
                </p>
              </div>
              <button class="btn sm" id="btn-soften-today" style="background:var(--orange);color:#fff">
                ${sprite('bolt', 16)} SOFTEN TODAY'S RUN TO 15m
              </button>
            </div>
          </div>`
        : ''
    }
    ${panel('WORLD MAP', worldMap(dates, sessions, exams), 'blue', 'flag')}

    ${
      skipped
        ? panel(
            `${skipped} SKIPPED SESSION${skipped > 1 ? 'S' : ''}`,
            `<div class="stack">
              <p class="muted" style="margin:0">Let the optimizer re-book those topics into slots you still have free.</p>
              <button class="btn go block" id="recalc-top">${sprite('bolt', 20)} RECALCULATE PLAN</button>
            </div>`,
            'yellow',
            'ghost'
          )
        : ''
    }

    <p class="muted tiny" style="margin:0">Days are collapsed by default — open the one you're working on. Study blocks and scheduled breaks are balanced for high retention.</p>

    ${dates
      .map((d) => {
        const day = sessions.filter((s) => s.session_date === d);
        const dayStudy = day.filter((s) => s.session_type !== 'break');
        const done = dayStudy.filter((s) => s.status === 'completed').length;
        return collapsible(
          fmtDate(d),
          day.map(sessionRow).join(''),
          {
            open: d === todayStr,
            icon: 'calendar',
            color: dayStudy.length && done === dayStudy.length ? 'green' : '',
            note: `${done}/${dayStudy.length} STUDY CLEARED`,
          }
        );
      })
      .join('')}
  </div>`;

  el('#recalc-top')?.addEventListener('click', runRecalculate);
  el('#btn-soften-today')?.addEventListener('click', async () => {
    try {
      const res = await api.adaptRoutine();
      toast('ok', 'SCHEDULE SOFTENED', `${res.adapted_sessions || 0} session(s) adjusted to 15m micro-sprints.`);
      show(0);
    } catch (err) {
      toast('err', 'FAILED', err.message);
    }
  });

  els('[data-mark]', host).forEach((btn) =>
    btn.addEventListener('click', async () => {
      try {
        await api.setSessionStatus(btn.dataset.mark, btn.dataset.status);
        toast('ok', btn.dataset.status === 'completed' ? 'SESSION CLEARED' : 'SESSION SKIPPED', '');
        show(0);
      } catch (err) {
        toast('err', 'FAILED', err.message);
      }
    })
  );

  els('[data-play]', host).forEach((btn) =>
    btn.addEventListener('click', () => {
      openFocusArena({
        id: btn.dataset.play,
        subject: btn.dataset.subject,
        topic: btn.dataset.topic,
        notes: btn.dataset.notes,
        duration: Number(btn.dataset.duration) || 60,
      });
    })
  );
}

/** Ask the optimizer to re-book skipped topics into remaining free slots. */
async function runRecalculate() {
  const res = await withLoader('REDISTRIBUTING SKIPPED WORK', () => api.recalculatePlan());
  if (!res) return;
  if (res.added > 0) {
    const tail = res.unplaced ? ` ${res.unplaced} could not fit — your grid is full.` : '';
    toast('ok', 'PLAN RECALCULATED', `${res.added} of ${res.skipped} skipped topic${res.skipped > 1 ? 's' : ''} re-booked.${tail}`);
  } else {
    toast(
      'info',
      'NO ROOM LEFT',
      'Every slot in your availability grid is already booked, so there is nowhere to move the skipped work. Add hours in Schedule → Availability, or push an exam date.'
    );
  }
  show(0);
}

function sessionRow(s) {
  const status = s.status || 'planned';
  const isBreak = s.session_type === 'break';
  const prio = s.priority || 'medium';

  if (isBreak) {
    const breakName = (s.topic_name || s.subject_name || 'Break').toLowerCase();
    let breakIcon = 'coffee';
    if (breakName.includes('lunch') || breakName.includes('dinner') || breakName.includes('breakfast') || breakName.includes('meal')) {
      breakIcon = 'food';
    } else if (breakName.includes('refresh') || breakName.includes('tea') || breakName.includes('coffee')) {
      breakIcon = 'coffee';
    }

    return `<div class="list-row break-row" style="${status !== 'planned' ? 'opacity:.72' : ''}">
      ${sprite(breakIcon, 26, 'bob')}
      <span class="rk">${esc(s.start_time || '--:--')}</span>
      <div class="grow">
        <div class="rt">${esc(s.topic_name || s.subject_name || 'Break & Refreshment')}</div>
        <div class="rs" style="font-size:16px;color:#8A4B08">${esc(s.notes || 'Recharge, hydrate, and relax your mind')}</div>
      </div>
      <span class="rs">${esc(s.duration_min ?? 30)} min</span>
      ${badge('Break', 'break')}
      ${badge(status, status)}
      ${
        status === 'planned'
          ? `<button class="ibtn ok" data-mark="${s.id}" data-status="completed" title="Mark done">✓</button>`
          : ''
      }
    </div>`;
  }

  const icon = status === 'completed' ? 'trophy' : status === 'skipped' ? 'ghost' : 'qblock';
  const technique = s.study_technique ? `<span class="badge technique">${esc(s.study_technique)}</span>` : '';
  const notesHtml = s.notes ? `<div class="rs" style="font-size:15px;color:var(--ink-soft);margin-top:4px">${esc(s.notes)}</div>` : '';

  return `<div class="list-row" style="${status !== 'planned' ? 'opacity:.72' : ''}">
    ${sprite(icon, 26, status === 'planned' ? 'bob' : '')}
    <span class="rk">${esc(s.start_time || '--:--')}</span>
    <div class="grow">
      <div class="rt" style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
        <span>${esc(s.subject_name || '')}</span>
        ${technique}
      </div>
      <div class="rs">${esc(s.topic_name || 'General review')}</div>
      ${notesHtml}
    </div>
    <span class="rs">${esc(s.duration_min ?? 60)} min</span>
    ${badge(prio, prio === 'high' ? 'hard' : prio === 'low' ? 'easy' : 'medium')}
    ${badge(status, status)}
    ${
      status === 'planned'
        ? `<button class="ibtn play" data-play="${s.id}" data-subject="${esc(s.subject_name)}" data-topic="${esc(s.topic_name)}" data-notes="${esc(s.notes)}" data-duration="${s.duration_min ?? 60}" title="Start Focus Session">▶</button>
           <button class="ibtn ok" data-mark="${s.id}" data-status="completed" title="Mark complete">✓</button>
           <button class="ibtn skip" data-mark="${s.id}" data-status="skipped" title="Skip">»</button>`
        : `<button class="ibtn play" data-play="${s.id}" data-subject="${esc(s.subject_name)}" data-topic="${esc(s.topic_name)}" data-notes="${esc(s.notes)}" data-duration="${s.duration_min ?? 60}" title="Review Study Material">▶</button>`
    }
  </div>`;
}

/**
 * The world map: one tile per day on a dashed road, with exam days as castles.
 * Tile state tells you at a glance what's cleared, what you missed, and where
 * you are right now.
 */
function worldMap(dates, sessions, exams) {
  const today = new Date().toISOString().slice(0, 10);

  // Exam days become boss nodes even if nothing is scheduled on them.
  const examByDate = {};
  exams.forEach((e) => {
    (examByDate[e.exam_date] ||= []).push(e.subject_name);
  });

  const allDates = [...new Set([...dates, ...Object.keys(examByDate)])].sort();

  const nodes = allDates
    .map((d) => {
      const day = sessions.filter((s) => s.session_date === d);
      const done = day.filter((s) => s.status === 'completed').length;
      const isToday = d === today;
      const isPast = d < today;
      const boss = examByDate[d];

      let state, icon, anim = '';
      if (boss) {
        state = 'boss';
        icon = 'castle';
        anim = isPast ? '' : 'bob';
      } else if (day.length && done === day.length) {
        state = 'done';
        icon = 'flag';
      } else if (done > 0) {
        state = 'part';
        icon = 'coin';
      } else if (isPast) {
        state = 'miss';
        icon = 'ghost';
      } else {
        state = 'todo';
        icon = 'qblock';
        anim = isToday ? 'bob' : '';
      }

      const dt = new Date(d + 'T00:00:00');
      const weekday = dt.toLocaleDateString('en-GB', { weekday: 'short' }).toUpperCase();
      const label = dt.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });

      const title = boss
        ? `${boss.join(', ')} exam on ${label}`
        : `${label}: ${done} of ${day.length} sessions cleared`;

      return `<div class="wm-node ${state} ${isToday ? 'today' : ''}" title="${esc(title)}">
        ${isToday ? '<div class="wm-marker">YOU ARE HERE</div>' : ''}
        <div class="wm-tile">${sprite(icon, 40, anim)}</div>
        <div class="wm-day">${esc(weekday)}</div>
        <div class="wm-date">${esc(label)}</div>
        ${
          boss
            ? `<div class="wm-boss-name">${esc(boss.map((b) => b.slice(0, 18)).join(' + '))}</div>`
            : `<div class="wm-count">${done}/${day.length}</div>`
        }
      </div>`;
    })
    .join('');

  const total = sessions.length;
  const cleared = sessions.filter((s) => s.status === 'completed').length;

  return `<div class="worldmap">
    <div class="scroll-x"><div class="wm-track">${nodes}</div></div>
    <div class="wm-ground"></div>
    <div class="wm-legend">
      <span>${sprite('qblock', 18)} to do</span>
      <span>${sprite('coin', 18)} started</span>
      <span>${sprite('flag', 18)} cleared</span>
      <span>${sprite('ghost', 18)} missed</span>
      <span>${sprite('castle', 18)} exam</span>
    </div>
    <div style="margin-top:14px">
      <div class="spread" style="margin-bottom:5px">
        <span class="mono-num" style="font-size:10px">RUN PROGRESS</span>
        <span class="mono-num" style="font-size:10px">${cleared}/${total}</span>
      </div>
      ${meter(total ? (cleared / total) * 100 : 0)}
    </div>
  </div>`;
}

/* ─── Tab 2: readiness ───────────────────────────────────────────── */
async function tabReadiness(host, sessions) {
  if (!sessions.length) {
    host.innerHTML = empty('NO PLAN YET', 'Generate a study plan to unlock readiness tracking.');
    return;
  }

  const rows = [];
  for (const s of subjects) {
    const mine = sessions.filter((x) => x.subject_name === s.name);
    const done = mine.filter((x) => x.status === 'completed');
    const completion = mine.length ? (done.length / mine.length) * 100 : 0;

    const topics = await api.subjectTopics(s.id).catch(() => []);
    const covered = new Set(done.map((x) => x.topic_name).filter(Boolean)).size;
    const coverage = topics.length ? (covered / topics.length) * 100 : 0;

    rows.push({
      label: s.name,
      value: completion * 0.6 + coverage * 0.4,
      sub: `${done.length}/${mine.length} sessions · ${covered}/${topics.length} topics covered`,
    });
  }

  const overall = rows.length ? rows.reduce((t, r) => t + r.value, 0) / rows.length : 0;

  host.innerHTML = `<div class="stack">
    ${panel(
      'OVERALL READINESS',
      `<div class="stack">${heartMeter(overall)}
        <p class="muted" style="margin:0">Weighted 60% session completion, 40% topic coverage.</p></div>`,
      overall >= 60 ? 'green' : overall >= 30 ? 'yellow' : 'red',
      'heart'
    )}
    ${
      rows.length >= 3
        ? panel(
            'READINESS RADAR',
            `<div class="scroll-x">${radarChart(rows, { max: 100, color: 'blue', unit: '%' })}</div>`,
            'blue',
            'target'
          )
        : ''
    }
    ${panel('PER-SUBJECT STATS', statBlock(rows), 'blue', 'chart')}
    <button class="btn primary block" id="run-predict">${sprite('brain', 22)} RUN AI READINESS PREDICTION</button>
    <div id="predict-out"></div>
  </div>`;

  el('#run-predict').addEventListener('click', async () => {
    const preds = await withLoader('PREDICTING READINESS', () => api.predictReadiness());
    if (!preds) return;
    toast('ok', 'PREDICTION LOGGED', 'Results saved to the feedback loop.');
    el('#predict-out').innerHTML = preds
      .map((p) => {
        const score = Math.round(p.readiness_score || 0);
        return panel(
          p.subject || 'Subject',
          `<div class="stack">
            ${heartMeter(score)}
            <div class="row-tight">
              ${badge(`readiness ${score}%`, score >= 60 ? 'easy' : score >= 30 ? 'medium' : 'hard')}
              ${badge(`coverage ${Math.round(p.coverage_pct || 0)}%`, 'info')}
              ${badge(`confidence ${Math.round((p.confidence || 0) * 100)}%`, 'purple')}
            </div>
            ${p.reasoning ? dialogue('AI REASONING', p.reasoning) : ''}
            ${chipList('Critical gaps', p.critical_gaps, 'hard')}
            ${chipList('Strengths', p.strengths, 'easy')}
            ${p.prediction ? `<p class="muted" style="margin:0">${esc(p.prediction)}</p>` : ''}
          </div>`,
          score >= 60 ? 'green' : score >= 30 ? 'yellow' : 'red',
          'target'
        );
      })
      .join('');
  });
}

function chipList(title, items, kind) {
  if (!items || !items.length) return '';
  return `<div>
    <div class="tiny muted" style="margin-bottom:6px">${esc(title.toUpperCase())}</div>
    <div class="row-tight">${items.map((i) => badge(i, kind)).join('')}</div>
  </div>`;
}

/* ─── Tab 3: generate ────────────────────────────────────────────── */
async function tabGenerate(host, sessions) {
  const [avail, exams] = await Promise.all([
    api.availability().catch(() => []),
    api.exams(true).catch(() => []),
  ]);

  const skippedCount = sessions.filter((s) => s.status === 'skipped').length;

  const blockers = [];
  if (!avail.length) blockers.push('Set your weekly availability in Schedule → Availability.');
  if (!exams.length) blockers.push('Schedule at least one upcoming exam in Schedule → Exam Dates.');

  host.innerHTML = `<div class="stack">
    ${panel(
      'WHAT THE OPTIMIZER CONSIDERS',
      `<div class="grid grid-2">
        ${[
          ['skull', 'Topic difficulty from the LLM-as-Judge scores'],
          ['bolt', 'Your peak focus windows for the hardest material'],
          ['calendar', 'Exam dates and how little time is left'],
          ['brain', 'Spaced repetition so it actually sticks'],
          ['chart', 'Test scores, to push weak subjects up the queue'],
          ['clock', 'Hard limits — nothing lands outside your free hours'],
        ]
          .map(([icon, text]) => `<div class="row-tight">${sprite(icon, 26)}<span class="grow">${esc(text)}</span></div>`)
          .join('')}
      </div>`,
      'purple',
      'bolt'
    )}

    ${
      blockers.length
        ? panel(
            'MISSING PREREQUISITES',
            blockers.map((b) => `<div class="list-row">${sprite('skull', 22)}<span class="grow">${esc(b)}</span></div>`).join(''),
            'red',
            'skull'
          )
        : ''
    }

    <button class="btn go block" id="gen-plan" ${blockers.length ? 'disabled' : ''} style="font-size:13px;padding:18px">
      ${sprite('bolt', 24)} GENERATE OPTIMIZED PLAN
    </button>

    ${panel(
      'KEEP IT DYNAMIC',
      `<div class="stack">
        <p class="muted" style="margin:0">
          Generating replaces the whole plan. Recalculating keeps what you've done and only
          re-books the topics from sessions you skipped, into slots you still have free.
        </p>
        <button class="btn block" id="recalc-plan" ${skippedCount ? '' : 'disabled'}>
          ${sprite('ghost', 20)} RECALCULATE ${skippedCount ? `(${skippedCount} SKIPPED)` : '— NOTHING SKIPPED'}
        </button>
      </div>`,
      'teal',
      'bolt'
    )}

    ${sessions.length ? `<button class="btn danger block" id="clear-plan">${sprite('skull', 20)} CLEAR CURRENT PLAN (${sessions.length} SESSIONS)</button>` : ''}
    <div id="gen-out"></div>
  </div>`;

  el('#recalc-plan')?.addEventListener('click', runRecalculate);

  el('#gen-plan')?.addEventListener('click', async () => {
    const res = await withLoader('BUILDING YOUR RUN', () => api.generatePlan());
    if (!res) return;
    toast('ok', 'PLAN GENERATED', `${res.saved} study sessions scheduled.`);
    el('#gen-out').innerHTML = `<div class="stack">
      ${panel(`${res.saved} SESSIONS SCHEDULED`, `<p class="muted" style="margin:0">Switch to the Timetable tab to play through them.</p>`, 'green', 'trophy')}
      ${res.strategy ? dialogue('STRATEGY', res.strategy, 'target') : ''}
      ${res.reasoning ? dialogue('AI REASONING', res.reasoning) : ''}
    </div>`;
    refreshStats();
  });

  el('#clear-plan')?.addEventListener('click', async () => {
    if (!confirm(`Delete all ${sessions.length} scheduled sessions? This cannot be undone.`)) return;
    try {
      await api.clearSessions();
      toast('ok', 'PLAN CLEARED', 'Generate a fresh one whenever you are ready.');
      show(2);
    } catch (err) {
      toast('err', 'FAILED', err.message);
    }
  });
}

/* ═══════════════════════════════════════════════════════════════════════
   SADHANA ACTIVE STUDY ARENA (ADHD-Inclusive Focus Space)
   ═══════════════════════════════════════════════════════════════════════ */

function playChime(kind = 'ping') {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    if (kind === 'ping') {
      osc.type = 'sine';
      osc.frequency.setValueAtTime(587.33, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.15);
      gain.gain.setValueAtTime(0.2, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.4);
      osc.start();
      osc.stop(ctx.currentTime + 0.45);
    } else if (kind === 'rest') {
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(440, ctx.currentTime);
      gain.gain.setValueAtTime(0.2, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.5);
      osc.start();
      osc.stop(ctx.currentTime + 0.55);
    }
  } catch (e) {
    /* audio context not permitted or unsupported */
  }
}

export function openFocusArena(session) {
  // Remove any existing overlay
  el('#focus-arena')?.remove();

  // ── Focus Shield (Distraction Blocker) ──
  if (isBlockerEnabled()) {
    showLockdownShield(
      () => _launchMeditationLoader(session),   // proceed
      () => _launchMeditationLoader(session)    // skip blocking
    );
    return;
  }
  _launchMeditationLoader(session);
}

function _launchMeditationLoader(session) {
  // ── 10-second Meditation Loading Screen ──
  const loaderDiv = document.createElement('div');
  loaderDiv.className = 'focus-overlay meditation-loader';
  loaderDiv.id = 'focus-arena';
  loaderDiv.innerHTML = `
    <div class="meditation-loader-inner">
      <div class="breath-circle inhale" id="med-breath-visual">
        <span class="mono-num" id="med-breath-label" style="font-size:16px;color:var(--teal)">BREATHE IN</span>
        <span class="focus-clock" id="med-breath-timer" style="font-size:28px;padding:4px 12px;margin-top:6px;border-color:var(--teal);color:var(--teal)">10</span>
      </div>
      <div class="mono-num" style="font-size:14px;margin-top:18px;color:var(--ink-soft)">ENTERING FOCUS MODE</div>
      <p class="muted tiny" style="margin-top:8px;max-width:420px;text-align:center">
        Sync your breathing with the circle. We're preparing your study arena…
      </p>
      <button class="btn ghost sm" id="med-skip-btn" style="margin-top:20px">SKIP → ENTER NOW</button>
      <button class="focus-back-btn" id="med-back-btn" title="Return to timetable">
        ◀ BACK
      </button>
    </div>
  `;
  document.body.appendChild(loaderDiv);

  // Breathing cycle: In(3s) → Hold(2s) → Out(3s) → Hold(2s)
  const breathPhases = [
    { label: 'BREATHE IN',  cls: 'inhale',  dur: 3 },
    { label: 'HOLD',        cls: 'inhale',  dur: 2 },
    { label: 'BREATHE OUT', cls: 'exhale',  dur: 3 },
    { label: 'HOLD',        cls: 'exhale',  dur: 2 },
  ];
  let phaseIdx = 0, phaseCountdown = breathPhases[0].dur, totalCountdown = 10;
  const bLabel  = loaderDiv.querySelector('#med-breath-label');
  const bTimer  = loaderDiv.querySelector('#med-breath-timer');
  const bVisual = loaderDiv.querySelector('#med-breath-visual');

  const medTick = setInterval(() => {
    totalCountdown--;
    phaseCountdown--;
    if (bTimer) bTimer.textContent = totalCountdown;
    if (phaseCountdown <= 0) {
      phaseIdx = (phaseIdx + 1) % breathPhases.length;
      phaseCountdown = breathPhases[phaseIdx].dur;
      if (bLabel)  bLabel.textContent = breathPhases[phaseIdx].label;
      if (bVisual) bVisual.className = 'breath-circle ' + breathPhases[phaseIdx].cls;
    }
    if (totalCountdown <= 0) {
      clearInterval(medTick);
      _bootArena();
    }
  }, 1000);

  loaderDiv.querySelector('#med-skip-btn')?.addEventListener('click', () => {
    clearInterval(medTick);
    _bootArena();
  });

  loaderDiv.querySelector('#med-back-btn')?.addEventListener('click', () => {
    clearInterval(medTick);
    loaderDiv.remove();
  });

  function _bootArena() {
    loaderDiv.remove();
    _startFocusArena(session);
  }
}

async function _startFocusArena(session) {

  const overlay = document.createElement('div');
  overlay.className = 'focus-overlay';
  overlay.id = 'focus-arena';
  document.body.appendChild(overlay);

  const todayR = await api.todayRoutine().catch(() => ({ is_low_energy: 0 }));
  const isLow = Boolean(todayR.is_low_energy);

  let workMin = isLow ? 15 : 25;
  let restMin = isLow ? 3 : 5;
  let totalCycles = Math.max(1, Math.round((session.duration || 60) / (workMin + restMin)));
  let currentCycle = 1;
  let isRest = false;
  let timeRemaining = workMin * 60;
  let isRunning = false;
  let timerId = null;
  let parkedThoughts = [];
  let compressedData = null;
  let breathInterval = null;

  function renderSetup() {
    overlay.innerHTML = `
      <div class="focus-wrap">
        <div class="panel">
          <div class="panel-head blue">
            ${sprite('controller', 22)}<span>SADHANA FOCUS ARENA</span>
          </div>
          <div style="padding:14px 4px 6px">
            <div class="level-tag">${esc(session.subject || 'GENERAL')}</div>
            <h2 style="margin:8px 0 14px">${esc(session.topic || 'Focused Study Session')}</h2>
            <p class="muted" style="margin:0 0 20px">
              Scheduled length: ${session.duration || 60} minutes &bull; Step inside to eliminate all distractions.
            </p>

            <div style="margin:20px 0">
              <div class="mono-num" style="font-size:13px;margin-bottom:10px;color:var(--ink-soft)">
                1. CHOOSE HOW YOU WANT TO PACE THIS RUN:
              </div>
              <div class="grid grid-3" id="pacing-options">
                <div class="panel pacing-card" data-work="25" data-rest="5" style="cursor:pointer;border:3px solid ${isLow ? 'var(--ink)' : 'var(--blue)'};background:${isLow ? 'var(--panel)' : 'var(--paper-2)'};padding:14px">
                  <div class="mono-num" style="color:var(--blue);font-size:13px;margin-bottom:4px">★ STANDARD POMODORO</div>
                  <div style="font-size:22px;font-weight:bold">25m Work + 5m Rest</div>
                  <div class="tiny muted" style="margin-top:4px">High retention & balanced recovery</div>
                </div>
                <div class="panel pacing-card" data-work="15" data-rest="3" style="cursor:pointer;border:3px solid ${isLow ? 'var(--orange)' : 'var(--ink)'};background:${isLow ? 'var(--paper-2)' : 'var(--panel)'};padding:14px">
                  <div class="spread">
                    <span class="mono-num" style="color:var(--orange);font-size:13px;margin-bottom:4px">⚡ ADHD MICRO-SPRINT</span>
                    ${isLow ? '<span class="badge" style="background:var(--orange);color:#fff;font-size:7px">LOW-ENERGY CHOICE</span>' : ''}
                  </div>
                  <div style="font-size:22px;font-weight:bold">15m Work + 3m Rest</div>
                  <div class="tiny muted" style="margin-top:4px">Gentle on executive fatigue & resistance</div>
                </div>
                <div class="panel pacing-card" data-work="45" data-rest="10" style="cursor:pointer;border:3px solid var(--ink);padding:14px">
                  <div class="mono-num" style="color:var(--purple);font-size:13px;margin-bottom:4px">🌊 DEEP FLOW BLOCK</div>
                  <div style="font-size:22px;font-weight:bold">45m Deep Focus</div>
                  <div class="tiny muted" style="margin-top:4px">Long immersion for high-energy days</div>
                </div>
              </div>
            </div>

            <!-- Distraction Blocker Setup -->
            <div style="margin:20px 0" id="blocker-section">
              ${renderBlockerSetup()}
            </div>

            <!-- Optional 60s Breathing Exercise -->
            <div style="margin:20px 0" id="breath-section">
              <button class="btn ghost sm" id="btn-toggle-breath" style="border:2px dashed var(--teal)">
                ${sprite('star', 18)} TAKE A 60-SEC GROUNDING BREATH FIRST (OPTIONAL)
              </button>
              <div id="breath-container" style="display:none;margin-top:14px;text-align:center;background:var(--panel);border:var(--edge);padding:18px">
                <div class="mono-num" style="color:var(--teal);margin-bottom:6px">BOX BREATHING (4-4-4-4)</div>
                <div class="breath-circle" id="breath-visual">
                  <span class="mono-num" id="breath-label" style="font-size:13px">INHALE</span>
                  <span class="focus-clock" id="breath-digits" style="font-size:20px;padding:2px 8px;margin-top:4px">4</span>
                </div>
                <p class="muted tiny">Breathe in sync with the circle. Quiets autonomic pre-study anxiety.</p>
              </div>
            </div>

            <div class="row" style="margin-top:28px">
              <button class="btn primary" id="btn-enter-arena" style="font-size:15px;padding:16px 28px">
                ${sprite('bolt', 24)} ENTER ACTIVE STUDY
              </button>
              <button class="btn ghost" id="btn-cancel-arena">
                RETURN TO TIMETABLE
              </button>
            </div>
          </div>
        </div>
      </div>
    `;

    // Pacing selector clicks
    els('.pacing-card', overlay).forEach((card) => {
      card.addEventListener('click', () => {
        els('.pacing-card', overlay).forEach((c) => {
          c.style.borderColor = 'var(--ink)';
          c.style.background = 'var(--panel)';
        });
        card.style.borderColor = 'var(--blue)';
        card.style.background = 'var(--paper-2)';
        workMin = Number(card.dataset.work) || 25;
        restMin = Number(card.dataset.rest) || 5;
        timeRemaining = workMin * 60;
        totalCycles = Math.max(1, Math.round((session.duration || 60) / (workMin + restMin)));
      });
    });

    // Breathing toggle
    overlay.querySelector('#btn-toggle-breath')?.addEventListener('click', () => {
      const box = overlay.querySelector('#breath-container');
      const isVisible = box.style.display !== 'none';
      box.style.display = isVisible ? 'none' : 'block';
      if (!isVisible) startBreathingGuide();
      else stopBreathingGuide();
    });

    overlay.querySelector('#btn-enter-arena')?.addEventListener('click', () => {
      stopBreathingGuide();
      startActiveStudy();
    });

    overlay.querySelector('#btn-cancel-arena')?.addEventListener('click', () => {
      stopBreathingGuide();
      overlay.remove();
    });

    // Mount distraction blocker app picker
    mountBlockerSetup(overlay);
  }

  function startBreathingGuide() {
    stopBreathingGuide();
    const phases = [
      { name: 'INHALE', cls: 'inhale', count: 4 },
      { name: 'HOLD', cls: 'inhale', count: 4 },
      { name: 'EXHALE', cls: 'exhale', count: 4 },
      { name: 'HOLD', cls: 'exhale', count: 4 },
    ];
    let pIdx = 0;
    let count = 4;
    const visual = overlay.querySelector('#breath-visual');
    const label = overlay.querySelector('#breath-label');
    const digits = overlay.querySelector('#breath-digits');

    breathInterval = setInterval(() => {
      count--;
      if (count <= 0) {
        pIdx = (pIdx + 1) % phases.length;
        count = phases[pIdx].count;
        if (visual) {
          visual.className = `breath-circle ${phases[pIdx].cls}`;
        }
        if (label) label.textContent = phases[pIdx].name;
      }
      if (digits) digits.textContent = count;
    }, 1000);
  }

  function stopBreathingGuide() {
    if (breathInterval) {
      clearInterval(breathInterval);
      breathInterval = null;
    }
  }

  function formatTime(secs) {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  }

  function startActiveStudy() {
    isRunning = true;
    overlay.innerHTML = `
      <button class="focus-back-btn" id="btn-back-arena" title="Return to timetable">
        ◀ BACK
      </button>
      <div class="focus-wrap">
        <!-- Top Focus HUD -->
        <div class="focus-hud">
          <div>
            <div class="row-tight">
              <span class="badge blue">${esc(session.subject || 'STUDY')}</span>
              <span class="badge ${isRest ? 'green' : 'teal'}" id="arena-phase-badge">
                ${isRest ? 'REST RECOVERY' : `SPRINT ${currentCycle} OF ${totalCycles}`}
              </span>
            </div>
            <div style="font-size:22px;font-weight:bold;margin-top:6px">${esc(session.topic)}</div>
          </div>
          <div class="row" style="gap:10px">
            <span class="focus-clock ${isRest ? 'rest' : ''}" id="arena-clock">${formatTime(timeRemaining)}</span>
            <button class="btn sm" id="btn-toggle-pause">PAUSE</button>
            <button class="btn sm ghost" id="btn-add-buffer" title="Extend hyperfocus with +5m buffer">+5m</button>
            <button class="btn sm ghost" id="btn-skip-phase" title="Skip to next interval">&raquo;</button>
            <button class="btn sm go" id="btn-finish-now" title="Complete session">✓ COMPLETE</button>
            <button class="btn sm danger" id="btn-quit-arena" title="Exit focus space">&times;</button>
          </div>
          <!-- Audio Controls -->
          <div class="audio-controls">
            <select id="arena-audio-mode" title="Ambient Sound">
              <option value="off"${audioController.getMode() === 'off' ? ' selected' : ''}>🔇 OFF</option>
              <option value="brown"${audioController.getMode() === 'brown' ? ' selected' : ''}>🟤 BROWN</option>
              <option value="rain"${audioController.getMode() === 'rain' ? ' selected' : ''}>🌧 RAIN</option>
              <option value="binaural"${audioController.getMode() === 'binaural' ? ' selected' : ''}>🧠 BINAURAL</option>
            </select>
            <input type="range" id="arena-audio-vol" min="0" max="1" step="0.01" value="${audioController.getVolume()}" title="Volume" style="width:80px">
          </div>
        </div>

        <!-- Main Workspace (Compressed Study Card + Thought Parking Lot) -->
        <div class="grid" style="grid-template-columns: minmax(0, 1.8fr) minmax(0, 1.2fr); gap: 20px;">
          <!-- Left: Compressed Learning Material -->
          <div id="arena-content">
            <div class="panel center" style="padding:48px 24px">
              <div class="sprite-row" style="margin-bottom:14px">
                ${sprite('brain', 36, 'bob bd1')}${sprite('bolt', 36, 'bob bd2')}${sprite('coin', 36, 'bob bd3')}
              </div>
              <div class="mono-num" style="font-size:16px">COMPRESSING KNOWLEDGE SCROLLS...</div>
              <p class="muted tiny" style="margin-top:8px">Synthesizing core intuition, everyday analogy &amp; visual schematic</p>
            </div>
          </div>

          <!-- Right: Thought Parking Lot -->
          <div>
            <div class="panel" style="position:sticky;top:20px">
              <div class="panel-head yellow">
                ${sprite('coin', 22)}<span>THOUGHT PARKING LOT</span>
              </div>
              <p class="muted tiny" style="margin:0 0 12px">
                Intrusive thought pop up? Offload it here so your brain can let it go and return to study.
              </p>
              <div class="row" style="margin-bottom:12px">
                <input type="text" id="park-input" placeholder="e.g. check train tickets, email..." style="flex:1;font-size:18px;padding:8px 10px">
                <button class="btn sm go" id="btn-park-add">PARK</button>
              </div>
              <div id="park-items-list" style="max-height:360px;overflow-y:auto"></div>
              <div class="tiny muted center" id="park-empty-msg" style="padding:14px 0">
                No thoughts parked yet. Focus is steady.
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    // Start tick
    startTimer();

    // Wire HUD controls
    overlay.querySelector('#btn-toggle-pause')?.addEventListener('click', togglePause);

    // Wire Audio Controls
    overlay.querySelector('#arena-audio-mode')?.addEventListener('change', (e) => {
      audioController.setMode(e.target.value);
    });
    overlay.querySelector('#arena-audio-vol')?.addEventListener('input', (e) => {
      audioController.setVolume(parseFloat(e.target.value));
    });
    // Restore audio on arena entry
    audioController.restore();
    overlay.querySelector('#btn-add-buffer')?.addEventListener('click', addBuffer);
    overlay.querySelector('#btn-skip-phase')?.addEventListener('click', skipPhase);
    overlay.querySelector('#btn-finish-now')?.addEventListener('click', finishSession);
    overlay.querySelector('#btn-quit-arena')?.addEventListener('click', () => {
      if (confirm('Leave the focus arena? Your session will stay as planned.')) {
        stopTimer();
        audioController.stop();
        overlay.remove();
      }
    });

    // Back button (fixed top-left)
    overlay.querySelector('#btn-back-arena')?.addEventListener('click', () => {
      if (confirm('Leave the focus arena? Your session will stay as planned.')) {
        stopTimer();
        audioController.stop();
        overlay.remove();
      }
    });

    // Wire Parking Lot
    const parkInput = overlay.querySelector('#park-input');
    const parkAddBtn = overlay.querySelector('#btn-park-add');

    const handleAddThought = () => {
      const val = parkInput.value.trim();
      if (!val) return;
      globalParkThought(val);
      parkInput.value = '';
      renderParkedThoughts();
    };

    parkAddBtn?.addEventListener('click', handleAddThought);
    parkInput?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleAddThought();
    });

    renderParkedThoughts();

    // Fetch compressed study material
    fetchCompressedContent();
  }

  function renderParkedThoughts() {
    const list = overlay.querySelector('#park-items-list');
    const emptyMsg = overlay.querySelector('#park-empty-msg');
    if (!list) return;

    const items = loadGlobalParkingLot();

    if (emptyMsg) {
      emptyMsg.style.display = items.length ? 'none' : 'block';
    }

    list.innerHTML = items
      .map(
        (t) => `
        <div class="parking-row">
          <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;padding-right:8px">${esc(t.text)}</span>
          <button class="ibtn sm" data-dismiss="${t.id}" style="width:28px;height:28px;font-size:14px" title="Dismiss">✕</button>
        </div>
      `
      )
      .join('');

    els('[data-dismiss]', list).forEach((b) => {
      b.addEventListener('click', () => {
        globalRemoveThought(Number(b.dataset.dismiss));
        renderParkedThoughts();
      });
    });
  }

  async function fetchCompressedContent() {
    const contentHost = overlay.querySelector('#arena-content');
    if (!contentHost) return;

    try {
      compressedData = await api.compressTopic(session.subject, session.topic, session.notes);
    } catch (err) {
      compressedData = null;
    }

    renderCompressedContent();
  }

  function renderCompressedContent() {
    const host = overlay.querySelector('#arena-content');
    if (!host) return;

    if (!compressedData) {
      host.innerHTML = `
        <div class="panel">
          <div class="panel-head teal">
            ${sprite('book', 22)}<span>${esc(session.topic)}</span>
          </div>
          <p>Read through your lecture notes or textbook for <b>${esc(session.topic)}</b>.</p>
          <p class="muted">Tip: Look for the core inputs, transformations, and outputs.</p>
        </div>
      `;
      return;
    }

    const d = compressedData;
    host.innerHTML = `
      <div class="stack">
        ${d.has_uploaded_notes ? `
          <div class="panel" style="background:#E8F8EE;border-left:8px solid var(--green);padding:10px 14px">
            <div class="spread">
              <span class="mono-num" style="color:var(--green);font-size:12px">✓ GROUNDED IN YOUR UPLOADED NOTES &amp; SLIDES</span>
              <span class="badge green">PROFESSOR SYNCED</span>
            </div>
          </div>
        ` : `
          <div class="panel" style="background:var(--paper-2);border-left:8px solid var(--blue);padding:10px 14px">
            <div class="spread">
              <span class="mono-num" style="color:var(--ink-soft);font-size:11px">ACADEMIC KNOWLEDGE BASE (TIP: Upload your college slides / handwritten notes in Data Setup anytime!)</span>
              <span class="badge blue">CURRICULUM</span>
            </div>
          </div>
        `}
        <!-- 1. Intuition Anchor -->
        <div class="panel" style="border-left:8px solid var(--blue)">
          <div class="mono-num" style="color:var(--blue);font-size:12px;margin-bottom:6px">💡 CORE INTUITION (WHY THIS EXISTS)</div>
          <div style="font-size:22px;line-height:1.4">${esc(d.intuition || '')}</div>
        </div>

        <!-- 2. Everyday Analogy -->
        <div class="panel" style="border-left:8px solid var(--orange)">
          <div class="mono-num" style="color:var(--orange);font-size:12px;margin-bottom:6px">🌍 REAL-WORLD EVERYDAY ANALOGY</div>
          <div style="font-size:21px;line-height:1.45">${esc(d.analogy || '')}</div>
        </div>

        <!-- 3. Visual Mental Model / Diagram -->
        <div class="panel" style="border-left:8px solid var(--green)">
          <div class="spread">
            <span class="mono-num" style="color:var(--green);font-size:12px">📊 VISUAL MENTAL MODEL / FLOWCHART</span>
            <span class="badge green">INSTANT SCHEMATIC</span>
          </div>
          <div class="diagram-box">${esc(d.visual_diagram || '')}</div>
        </div>

        <!-- 4. Key Takeaways -->
        <div class="panel" style="border-left:8px solid var(--purple)">
          <div class="mono-num" style="color:var(--purple);font-size:12px;margin-bottom:8px">⚡ RAZOR-SHARP TAKEAWAYS</div>
          <ul style="margin:0;padding-left:22px;line-height:1.6">
            ${(d.key_takeaways || []).map((t) => `<li style="margin-bottom:6px">${esc(t)}</li>`).join('')}
          </ul>
        </div>

        <!-- 5. Low-Stakes Intuition Checkpoint -->
        ${
          d.checkpoint
            ? `
          <div class="panel" style="border-left:8px solid var(--yellow)">
            <div class="mono-num" style="color:var(--ink);font-size:12px;margin-bottom:8px">🎯 INTUITION CHECKPOINT</div>
            <div style="font-size:20px;font-weight:bold;margin-bottom:12px">${esc(d.checkpoint.question)}</div>
            <div id="quiz-options-list">
              ${(d.checkpoint.options || [])
                .map(
                  (opt, i) => `
                <div class="quiz-opt" data-opt-idx="${i}">
                  <span>${esc(opt)}</span>
                  <span class="badge">${['A', 'B', 'C', 'D'][i]}</span>
                </div>
              `
                )
                .join('')}
            </div>
            <div id="quiz-explanation" style="display:none;margin-top:12px;padding:12px;border:2px solid var(--ink);font-size:19px"></div>
          </div>
        `
            : ''
        }

        <!-- 6. Ask the Tutor Bar -->
        <div class="panel" style="background:var(--paper-2)">
          <div class="spread" style="margin-bottom:8px">
            <span class="mono-num" style="font-size:12px">${sprite('brain', 18)} ASK ADAPTIVE TUTOR</span>
            <span class="tiny muted">Quick answers under 70 words</span>
          </div>
          <div class="row-tight" style="margin-bottom:8px">
            <button class="badge chip" data-quick="Explain this simply like I am 10 years old">Like I'm 10</button>
            <button class="badge chip" data-quick="Give me another real-world everyday analogy">Another analogy</button>
            <button class="badge chip" data-quick="What is the most common exam trap or mistake on this topic?">Common pitfalls</button>
          </div>
          <div class="row">
            <input type="text" id="tutor-question" placeholder="Ask a quick question about this topic..." style="flex:1;font-size:18px;padding:8px 12px">
            <button class="btn primary sm" id="btn-submit-question">ASK</button>
          </div>
          <div id="tutor-reply-card" style="display:none;margin-top:10px;padding:12px;background:var(--panel);border:2px solid var(--ink);font-size:19px"></div>
        </div>
      </div>
    `;

    // Quiz options click
    if (d.checkpoint) {
      els('[data-opt-idx]', host).forEach((btn) => {
        btn.addEventListener('click', () => {
          const selIdx = Number(btn.dataset.opt-idx || btn.getAttribute('data-opt-idx'));
          const correct = selIdx === d.checkpoint.correct_index;
          els('[data-opt-idx]', host).forEach((opt) => {
            const idx = Number(opt.dataset.opt-idx || opt.getAttribute('data-opt-idx'));
            if (idx === d.checkpoint.correct_index) opt.classList.add('correct');
            else opt.style.opacity = '0.5';
          });
          if (!correct) btn.classList.add('wrong');

          const explBox = host.querySelector('#quiz-explanation');
          if (explBox) {
            explBox.style.display = 'block';
            explBox.style.background = correct ? '#E8F8EE' : '#FFF9E6';
            explBox.style.borderColor = correct ? 'var(--green)' : 'var(--orange)';
            explBox.innerHTML = `<b>${correct ? '✨ EXACT INTUITION!' : '🌱 CLOSE!'}</b> ${esc(d.checkpoint.explanation)}`;
          }
        });
      });
    }

    // Ask tutor
    const qInput = host.querySelector('#tutor-question');
    const qBtn = host.querySelector('#btn-submit-question');
    const replyCard = host.querySelector('#tutor-reply-card');

    const handleAsk = async (text) => {
      const q = text || qInput.value.trim();
      if (!q) return;
      if (replyCard) {
        replyCard.style.display = 'block';
        replyCard.textContent = 'Thinking...';
      }
      try {
        const res = await api.askTutor(session.subject, session.topic, q);
        if (replyCard) replyCard.textContent = res.reply || 'You got this!';
      } catch (err) {
        if (replyCard) replyCard.textContent = 'Focus on the core takeaways above!';
      }
    };

    qBtn?.addEventListener('click', () => handleAsk());
    qInput?.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') handleAsk();
    });

    els('[data-quick]', host).forEach((chip) => {
      chip.addEventListener('click', () => handleAsk(chip.dataset.quick));
    });
  }

  function startTimer() {
    stopTimer();
    isRunning = true;
    timerId = setInterval(() => {
      if (timeRemaining > 0) {
        timeRemaining--;
        updateClockDisplay();
      } else {
        handleIntervalEnd();
      }
    }, 1000);
  }

  function stopTimer() {
    if (timerId) {
      clearInterval(timerId);
      timerId = null;
    }
  }

  function togglePause() {
    const btn = overlay.querySelector('#btn-toggle-pause');
    if (isRunning) {
      stopTimer();
      isRunning = false;
      if (btn) btn.textContent = 'RESUME';
    } else {
      startTimer();
      isRunning = true;
      if (btn) btn.textContent = 'PAUSE';
    }
  }

  function addBuffer() {
    timeRemaining += 5 * 60;
    updateClockDisplay();
    toast('info', '+5 MIN BUFFER', 'Flow state extended. Keep momentum.');
  }

  function skipPhase() {
    handleIntervalEnd();
  }

  function updateClockDisplay() {
    const clock = overlay.querySelector('#arena-clock');
    if (clock) clock.textContent = formatTime(timeRemaining);
  }

  function handleIntervalEnd() {
    stopTimer();

    if (!isRest) {
      // Focus sprint finished -> start Rest interval
      playChime('rest');
      isRest = true;
      timeRemaining = restMin * 60;
      updatePhaseBadge();
      updateClockDisplay();
      renderRestScreen();
    } else {
      // Rest interval finished -> start next Focus sprint or complete
      playChime('ping');
      isRest = false;
      currentCycle++;
      if (currentCycle > totalCycles) {
        finishSession();
      } else {
        timeRemaining = workMin * 60;
        updatePhaseBadge();
        updateClockDisplay();
        startActiveStudy();
      }
    }
  }

  function updatePhaseBadge() {
    const badge = overlay.querySelector('#arena-phase-badge');
    const clock = overlay.querySelector('#arena-clock');
    if (badge) {
      badge.className = `badge ${isRest ? 'green' : 'teal'}`;
      badge.textContent = isRest ? 'REST RECOVERY' : `SPRINT ${currentCycle} OF ${totalCycles}`;
    }
    if (clock) {
      if (isRest) clock.classList.add('rest');
      else clock.classList.remove('rest');
    }
  }

  function renderRestScreen() {
    const host = overlay.querySelector('#arena-content');
    if (!host) return;

    host.innerHTML = `
      <div class="panel center" style="padding:48px 24px;border:4px solid var(--green);background:var(--paper-2)">
        <div style="font-size:48px;margin-bottom:12px">🧘</div>
        <h2 style="color:var(--green);margin-bottom:8px">REST INTERVAL — RESET YOUR MIND</h2>
        <p style="font-size:20px;max-width:540px;margin:0 auto 18px">
          Great focus! Try a quick guided meditation to reset, or step away for a stretch.
        </p>

        <!-- Meditation Prompt -->
        <div class="panel" style="border:3px dashed var(--teal);background:rgba(42,183,176,0.08);padding:18px;margin:18px auto;max-width:480px">
          <div class="mono-num" style="color:var(--teal);font-size:12px;margin-bottom:8px">✨ RECOMMENDED: 10-SECOND GUIDED BREATH</div>
          <p class="muted tiny" style="margin:0 0 12px">A quick reset between sprints boosts retention and calms executive fatigue.</p>
          <div id="rest-breath-zone" style="display:none;margin:14px 0">
            <div class="breath-circle inhale" id="rest-breath-visual">
              <span class="mono-num" id="rest-breath-label" style="font-size:13px;color:var(--teal)">BREATHE IN</span>
              <span class="focus-clock" id="rest-breath-timer" style="font-size:20px;padding:2px 8px;margin-top:4px;border-color:var(--teal);color:var(--teal)">10</span>
            </div>
          </div>
          <button class="btn go sm" id="btn-start-rest-meditation">
            ${sprite('star', 16)} START MEDITATION
          </button>
        </div>

        <div class="row" style="justify-content:center;gap:12px;margin-top:24px">
          <button class="btn primary sm" id="btn-skip-rest-btn">
            ${sprite('bolt', 18)} SKIP REST &amp; START SPRINT ${currentCycle + 1}
          </button>
        </div>
      </div>
    `;

    // Wire meditation button
    host.querySelector('#btn-start-rest-meditation')?.addEventListener('click', () => {
      const zone   = host.querySelector('#rest-breath-zone');
      const medBtn = host.querySelector('#btn-start-rest-meditation');
      if (zone) zone.style.display = 'block';
      if (medBtn) medBtn.disabled = true;

      const phases = [
        { label: 'BREATHE IN',  cls: 'inhale',  dur: 3 },
        { label: 'HOLD',        cls: 'inhale',  dur: 2 },
        { label: 'BREATHE OUT', cls: 'exhale',  dur: 3 },
        { label: 'HOLD',        cls: 'exhale',  dur: 2 },
      ];
      let pi = 0, pc = phases[0].dur, tc = 10;
      const rl = host.querySelector('#rest-breath-label');
      const rt = host.querySelector('#rest-breath-timer');
      const rv = host.querySelector('#rest-breath-visual');

      const tick = setInterval(() => {
        tc--; pc--;
        if (rt) rt.textContent = tc;
        if (pc <= 0) {
          pi = (pi + 1) % phases.length;
          pc = phases[pi].dur;
          if (rl) rl.textContent = phases[pi].label;
          if (rv) rv.className = 'breath-circle ' + phases[pi].cls;
        }
        if (tc <= 0) {
          clearInterval(tick);
          if (medBtn) { medBtn.textContent = '✨ MEDITATION DONE'; medBtn.disabled = true; }
          toast('ok', 'MIND RESET', 'Feeling centered. Ready for the next sprint.');
        }
      }, 1000);
    });

    host.querySelector('#btn-skip-rest-btn')?.addEventListener('click', () => {
      handleIntervalEnd();
    });

    startTimer();
  }

  async function finishSession() {
    stopTimer();
    stopBreathingGuide();
    audioController.stop();
    playChime('ping');

    try {
      await Promise.all([
        api.setSessionStatus(session.id, 'completed'),
        api.logFocusTime(session.duration || workMin),
      ]);
      window.dispatchEvent(new Event('examflow:refresh'));
    } catch (e) {
      /* ignore */
    }

    overlay.innerHTML = `
      <div class="focus-wrap" style="padding-top:40px">
        <div class="panel center" style="padding:48px 24px;border:4px solid var(--green)">
          <div class="sprite-row" style="margin-bottom:16px">
            ${sprite('trophy', 52, 'bob bd1')}${sprite('star', 46, 'bob bd2')}${sprite('trophy', 52, 'bob bd3')}
          </div>
          <h1 style="color:var(--green);margin-bottom:8px">FOCUS RUN CLEARED!</h1>
          <p style="font-size:24px;margin-bottom:12px">Topic Completed: <b>${esc(session.topic)}</b></p>
          <p class="muted" style="max-width:560px;margin:0 auto 24px">
            Zero pressure, steady progress. Your timetable and progress records have been updated.
          </p>
          <button class="btn primary" id="btn-exit-celebration" style="font-size:16px;padding:16px 32px">
            ${sprite('controller', 20)} RETURN TO TIMETABLE
          </button>
        </div>
      </div>
    `;

    overlay.querySelector('#btn-exit-celebration')?.addEventListener('click', () => {
      overlay.remove();
      show(0);
    });
  }

  // Initial boot into Setup
  renderSetup();
}

