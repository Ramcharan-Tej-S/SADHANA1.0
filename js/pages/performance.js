// pages/performance.js — LEVEL 4: test scores + AI priority re-calibration.
import { sprite } from '../sprites.js';
import { api } from '../api.js';
import {
  esc, el, els, badge, tile, empty, panel, dialogue, pageTitle,
  tabs, mountTabs, dualBarChart, toast, withLoader, todayISO, collapsible,
} from '../ui.js';

let subjects = [];

export function renderPerformance() {
  return `<div class="page"><div class="wrap">
    ${pageTitle(4, 'PERFORMANCE', 'Log what you actually scored and let the analyzer re-weight the plan.', 'chart')}
    ${tabs('perf-tabs', ['ENTER SCORES', 'ROUTINE & ENERGY', 'AI ANALYSIS'])}
    <div id="perf-body"></div>
  </div></div>`;
}

export async function mountPerformance() {
  subjects = await api.subjects().catch(() => []);
  mountTabs('perf-tabs', show);
  show(0);
}

async function show(idx) {
  const host = el('#perf-body');
  if (!subjects.length) {
    host.innerHTML = empty('NO SUBJECTS', 'Register subjects in Data Setup first.');
    return;
  }
  host.innerHTML = '<div class="empty">LOADING...</div>';
  if (idx === 0) await tabEnter(host);
  else if (idx === 1) await tabRoutine(host);
  else await tabAnalysis(host);
}

/* ─── Tab 1: enter scores ────────────────────────────────────────── */
async function tabEnter(host) {
  const scores = await api.scores().catch(() => []);

  host.innerHTML = `<div class="stack">
    ${panel(
      'RECORD A SCORE',
      `<form id="score-form" class="stack">
        <div class="grid grid-2">
          <label class="field"><span>Subject</span>
            <select name="subject_id">${subjects.map((s) => `<option value="${s.id}">${esc(s.name)}</option>`).join('')}</select></label>
          <label class="field"><span>Test type</span>
            <select name="test_type">
              ${['cie1', 'cie2', 'cie3', 'quiz', 'assignment', 'midterm', 'mock']
                .map((t) => `<option value="${t}">${t.toUpperCase()}</option>`).join('')}
            </select></label>
          <label class="field"><span>Score obtained</span>
            <input type="number" name="score" min="0" max="500" step="0.5" value="0" required></label>
          <label class="field"><span>Maximum score</span>
            <input type="number" name="max_score" min="1" max="500" step="0.5" value="50" required></label>
          <label class="field"><span>Test date</span>
            <input type="date" name="test_date" value="${todayISO()}"></label>
          <label class="field"><span>Notes</span>
            <input type="text" name="notes" placeholder="Ran out of time on section B"></label>
        </div>
        <button class="btn primary block" type="submit">${sprite('floppy', 20)} SAVE SCORE</button>
      </form>`,
      'orange',
      'chart'
    )}

    ${
      scores.length
        ? collapsible(
            'SCORE HISTORY',
            scores
              .map((sc) => {
                const pct = sc.max_score > 0 ? (sc.score / sc.max_score) * 100 : 0;
                const kind = pct >= 70 ? 'easy' : pct >= 50 ? 'medium' : 'hard';
                const icon = pct >= 70 ? 'trophy' : pct >= 50 ? 'coin' : 'skull';
                return `<div class="list-row">
                  ${sprite(icon, 26)}
                  <div class="grow">
                    <div class="rt">${esc(sc.subject_name)}</div>
                    <div class="rs">${esc(sc.test_date || '')} ${sc.notes ? '&middot; ' + esc(sc.notes) : ''}</div>
                  </div>
                  ${badge(sc.test_type, 'blue')}
                  <span class="rs">${esc(sc.score)}/${esc(sc.max_score)}</span>
                  ${badge(pct.toFixed(0) + '%', kind)}
                </div>`;
              })
              .join(''),
            { icon: 'trophy', note: `${scores.length} RECORDED` }
          )
        : empty('NO SCORES YET', 'Record a CIE, quiz or mock result above to unlock the analysis tab.')
    }
  </div>`;

  el('#score-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const score = Number(fd.get('score'));
    const max = Number(fd.get('max_score'));
    if (!(score > 0)) return toast('err', 'INVALID', 'Enter a score greater than zero.');
    if (score > max) return toast('err', 'INVALID', 'The score cannot exceed the maximum.');
    try {
      await api.addScore({
        subject_id: Number(fd.get('subject_id')),
        score,
        max_score: max,
        test_type: fd.get('test_type'),
        test_date: fd.get('test_date') || null,
        notes: fd.get('notes') || '',
      });
      toast('ok', 'SCORE SAVED', `${((score / max) * 100).toFixed(0)}% recorded.`);
      show(0);
    } catch (err) {
      toast('err', 'FAILED', err.message);
    }
  });
}

/* ─── Tab 2: ADHD Routine & Low-Energy Tracker ────────────────────── */
async function tabRoutine(host) {
  const rStats = await api.routineStats().catch(() => ({
    streak: 0,
    total_focus_minutes: 0,
    total_sessions_completed: 0,
    today: { is_low_energy: 0, energy_level: 'normal', focus_minutes: 0, sessions_completed: 0 },
    last_7_days: [],
  }));

  const isLow = Boolean(rStats.today?.is_low_energy);
  const streak = rStats.streak || 0;
  const totalMins = rStats.total_focus_minutes || 0;
  const totalSess = rStats.total_sessions_completed || 0;

  host.innerHTML = `<div class="stack">
    <!-- Stat Tiles -->
    <div class="grid grid-3">
      ${tile('Active Streak', streak + ' Days', streak > 0 ? 'Consistent momentum' : 'Start today!', streak > 2 ? 'green' : 'blue', 'bolt')}
      ${tile('Total Focus Time', totalMins + ' min', `${Math.round(totalMins / 60)} hrs accumulated`, 'purple', 'clock')}
      ${tile('Study Blocks Cleared', totalSess, 'Completed runs', 'teal', 'trophy')}
    </div>

    <!-- Energy Check-in Panel -->
    ${panel(
      "TODAY'S ENERGY & ADAPTATION CHECK-IN",
      `<div class="stack">
        <p class="muted" style="margin:0">
          Executive function fluctuates naturally. Let SADHANA know how your brain feels today, and the app will gently adapt without judgment.
        </p>
        <div class="grid grid-3" id="energy-options">
          <div class="panel energy-card" data-energy="high" style="cursor:pointer;border:3px solid ${rStats.today?.energy_level === 'high' && !isLow ? 'var(--blue)' : 'var(--ink)'};background:${rStats.today?.energy_level === 'high' && !isLow ? 'var(--paper-2)' : 'var(--panel)'};padding:14px">
            <div class="mono-num" style="color:var(--blue);font-size:12px;margin-bottom:4px">⚡ HIGH ENERGY / HYPERFOCUS</div>
            <div style="font-size:18px;font-weight:bold">Deep Flow Mode</div>
            <div class="tiny muted" style="margin-top:4px">Ready for 45m deep blocks & hard concepts</div>
          </div>
          <div class="panel energy-card" data-energy="normal" style="cursor:pointer;border:3px solid ${rStats.today?.energy_level === 'normal' && !isLow ? 'var(--green)' : 'var(--ink)'};background:${rStats.today?.energy_level === 'normal' && !isLow ? 'var(--paper-2)' : 'var(--panel)'};padding:14px">
            <div class="mono-num" style="color:var(--green);font-size:12px;margin-bottom:4px">🎯 BALANCED / STEADY</div>
            <div style="font-size:18px;font-weight:bold">Standard Pomodoro</div>
            <div class="tiny muted" style="margin-top:4px">25m focus + 5m rest intervals</div>
          </div>
          <div class="panel energy-card" data-energy="low" style="cursor:pointer;border:3px solid ${isLow ? 'var(--orange)' : 'var(--ink)'};background:${isLow ? 'var(--paper-2)' : 'var(--panel)'};padding:14px">
            <div class="mono-num" style="color:var(--orange);font-size:12px;margin-bottom:4px">🌱 LOW ENERGY / BRAIN FOG</div>
            <div style="font-size:18px;font-weight:bold">ADHD Micro-Sprints</div>
            <div class="tiny muted" style="margin-top:4px">Gentle 15m micro-sprints & extra rest</div>
          </div>
        </div>

        ${
          isLow
            ? `<div class="panel" style="background:#FFFDF0;border:2px dashed var(--orange);padding:14px">
                <div class="spread">
                  <div>
                    <span class="mono-num" style="color:var(--orange);font-size:12px">🌱 LOW-ENERGY ADAPTATION ACTIVE</span>
                    <p class="tiny muted" style="margin:4px 0 0">Sessions default to 15m micro-sprints in Focus Arena.</p>
                  </div>
                  <button class="btn sm" id="routine-soften-btn" style="background:var(--orange);color:#fff">
                    ${sprite('bolt', 16)} SOFTEN TIMETABLE SESSIONS
                  </button>
                </div>
              </div>`
            : ''
        }
      </div>`,
      'yellow',
      'heart'
    )}

    <!-- 7-Day Activity & Energy Calendar -->
    ${panel(
      'PAST 7 DAYS ACTIVITY & ENERGY',
      `<div class="grid" style="grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 10px;">
        ${(rStats.last_7_days || [])
          .map((d) => {
            const dt = new Date(d.log_date + 'T00:00:00');
            const dayName = dt.toLocaleDateString('en-GB', { weekday: 'short' }).toUpperCase();
            const dateNum = dt.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
            const hasActivity = (d.sessions_completed > 0) || (d.focus_minutes > 0);
            const isLowD = Boolean(d.is_low_energy);

            return `
              <div class="panel center" style="padding:12px 6px;border:2px solid var(--ink);background:${hasActivity ? '#E8F8EE' : 'var(--panel)'}">
                <div class="mono-num" style="font-size:9px;color:var(--ink-soft)">${esc(dayName)}</div>
                <div class="mono-num" style="font-size:11px;margin:2px 0 6px">${esc(dateNum)}</div>
                <div style="font-size:22px;margin-bottom:4px">
                  ${hasActivity ? sprite('trophy', 24, 'bob') : sprite('clock', 20)}
                </div>
                <div class="mono-num" style="font-size:9px;color:${hasActivity ? 'var(--green)' : 'var(--ink-soft)'}">
                  ${d.sessions_completed || 0} run${d.sessions_completed === 1 ? '' : 's'}
                </div>
                <div class="tiny muted" style="font-size:13px">${d.focus_minutes || 0}m</div>
                ${isLowD ? '<span class="badge" style="background:var(--orange);color:#fff;font-size:6px;margin-top:4px">LOW ENERGY</span>' : ''}
              </div>
            `;
          })
          .join('')}
      </div>`,
      'teal',
      'calendar'
    )}
  </div>`;

  // Wire energy cards
  els('.energy-card', host).forEach((card) => {
    card.addEventListener('click', async () => {
      const mode = card.dataset.energy;
      const isL = mode === 'low';
      try {
        await api.setEnergyMode(isL, mode);
        toast(
          'ok',
          isL ? 'LOW-ENERGY MODE SET' : 'ENERGY LEVEL SET',
          isL
            ? 'ADHD Micro-Sprints active for today. Be gentle with yourself.'
            : `Set to ${mode.toUpperCase()} mode.`
        );
        window.dispatchEvent(new Event('examflow:refresh'));
        tabRoutine(host);
      } catch (e) {
        toast('err', 'FAILED', e.message);
      }
    });
  });

  el('#routine-soften-btn')?.addEventListener('click', async () => {
    try {
      const res = await api.adaptRoutine();
      toast('ok', 'TIMETABLE ADAPTED', `${res.adapted_sessions || 0} session(s) adjusted to 15m micro-sprints.`);
    } catch (e) {
      toast('err', 'FAILED', e.message);
    }
  });
}

/* ─── Tab 3: AI analysis ─────────────────────────────────────────── */
async function tabAnalysis(host) {
  const scores = await api.scores().catch(() => []);
  if (!scores.length) {
    host.innerHTML = empty('NOTHING TO ANALYSE', 'Record at least one test score first.');
    return;
  }

  // Expected (from self-rating) vs actual average, per subject.
  const rows = [];
  new Set(scores.map((s) => s.subject_name)).forEach((name) => {
    const mine = scores.filter((s) => s.subject_name === name);
    const actual = mine.reduce((t, s) => t + (s.score / s.max_score) * 100, 0) / mine.length;
    const subj = subjects.find((s) => s.name === name);
    rows.push({ label: name, a: subj ? subj.self_rating * 10 : 50, b: actual });
  });

  host.innerHTML = `<div class="stack">
    ${panel('EXPECTED VS ACTUAL', `<div class="scroll-x">${dualBarChart(rows, 'You predicted (self-rating)', 'You actually scored')}</div>`, 'purple', 'target')}
    <button class="btn primary block" id="run-analysis">${sprite('brain', 22)} RUN AI PERFORMANCE ANALYSIS</button>
    <div id="analysis-out"></div>
  </div>`;

  el('#run-analysis').addEventListener('click', async () => {
    const a = await withLoader('ANALYSING PATTERNS', () => api.analyzePerformance());
    if (!a) return;
    toast('ok', 'ANALYSIS DONE', 'Priorities re-calibrated and logged.');
    el('#analysis-out').innerHTML = `<div class="stack">
      ${a.reasoning ? dialogue('AI REASONING', a.reasoning) : ''}
      ${(a.subject_analysis || [])
        .map((sa) => {
          const shift = sa.priority_shift || 'maintain';
          const kind = shift === 'increase' ? 'hard' : shift === 'decrease' ? 'easy' : 'info';
          return panel(
            sa.subject || 'Subject',
            `<div class="stack">
              <div class="row">
                ${badge(`${Math.round(sa.score_pct || 0)}%`, (sa.score_pct || 0) >= 70 ? 'easy' : (sa.score_pct || 0) >= 50 ? 'medium' : 'hard')}
                ${badge(`priority ${shift}`, kind)}
                ${badge(String(sa.performance_level || '').replace(/_/g, ' ') || 'unrated', 'blue')}
              </div>
              ${sa.focus_recommendation ? `<p class="muted" style="margin:0">${esc(sa.focus_recommendation)}</p>` : ''}
              ${listBlock('Weak areas', sa.weak_areas, 'hard')}
              ${listBlock('Strong areas', sa.strong_areas, 'easy')}
            </div>`,
            kind === 'hard' ? 'red' : kind === 'easy' ? 'green' : 'teal',
            'cartridge'
          );
        })
        .join('')}
      ${
        (a.recommendations || []).length
          ? panel(
              'RECOMMENDATIONS',
              a.recommendations
                .map((r) => `<div class="list-row">${sprite('star', 22)}<span class="grow">${esc(r)}</span></div>`)
                .join(''),
              'yellow',
              'scroll'
            )
          : ''
      }
    </div>`;
  });
}

function listBlock(title, items, kind = '') {
  if (!items || !items.length) return '';
  return `<div>
    <div class="tiny muted" style="margin-bottom:6px">${esc(title.toUpperCase())}</div>
    <div class="row-tight">${items.map((i) => badge(i, kind)).join('')}</div>
  </div>`;
}
