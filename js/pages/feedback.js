// pages/feedback.js — LEVEL 6: trends, prediction accuracy, personalised tips.
import { sprite } from '../sprites.js';
import { api } from '../api.js';
import {
  esc, el, badge, tile, empty, panel, dialogue, pageTitle,
  tabs, mountTabs, lineChart, heartMeter, barChart, toast, withLoader,
} from '../ui.js';

let subjects = [];

export function renderFeedback() {
  return `<div class="page"><div class="wrap">
    ${pageTitle(6, 'FEEDBACK LOOP', 'What the model predicted, what actually happened, and what to change.', 'trophy')}
    ${tabs('fb-tabs', ['TRENDS', 'AI INSIGHTS', 'SUMMARY'])}
    <div id="fb-body"></div>
  </div></div>`;
}

export async function mountFeedback() {
  subjects = await api.subjects().catch(() => []);
  mountTabs('fb-tabs', show);
  show(0);
}

async function show(idx) {
  const host = el('#fb-body');
  if (!subjects.length) {
    host.innerHTML = empty('NO SUBJECTS', 'Register subjects in Data Setup first.');
    return;
  }
  host.innerHTML = '<div class="empty">LOADING...</div>';
  if (idx === 0) await tabTrends(host);
  else if (idx === 1) tabInsights(host);
  else await tabSummary(host);
}

/* ─── Tab 1: trends ──────────────────────────────────────────────── */
async function tabTrends(host) {
  const [scores, sessions, topics] = await Promise.all([
    api.scores().catch(() => []),
    api.sessions().catch(() => []),
    api.topics().catch(() => []),
  ]);

  if (!scores.length && !sessions.length) {
    host.innerHTML = empty('NO DATA YET', 'Record some test scores and generate a study plan to unlock trends.');
    return;
  }

  const doneSessions = sessions.filter((s) => s.status === 'completed');
  const studyHrs = doneSessions.reduce((t, s) => t + (s.duration_min || 0), 0) / 60;
  const avgScore = scores.length
    ? scores.reduce((t, s) => t + (s.score / s.max_score) * 100, 0) / scores.length
    : 0;
  const covered = new Set(doneSessions.map((s) => s.topic_name).filter(Boolean)).size;
  const completion = sessions.length ? (doneSessions.length / sessions.length) * 100 : 0;
  const coverage = topics.length ? (covered / topics.length) * 100 : 0;

  // Per-subject readiness history charts
  const histories = await Promise.all(
    subjects.map(async (s) => ({ subject: s, history: await api.subjectPerformance(s.id).catch(() => []) }))
  );
  const charted = histories.filter((h) => h.history.length >= 2);

  host.innerHTML = `<div class="stack">
    <div class="grid grid-4">
      ${tile('Study time', studyHrs.toFixed(1) + 'h', '', 'purple', 'clock')}
      ${tile('Avg score', Math.round(avgScore) + '%', `${scores.length} tests`, 'orange', 'chart')}
      ${tile('Topic coverage', `${covered}/${topics.length}`, '', 'teal', 'brain')}
      ${tile('Completion', Math.round(completion) + '%', '', 'green', 'trophy')}
    </div>

    ${panel('SYLLABUS COVERAGE', `<div class="stack">${heartMeter(coverage)}
      <p class="muted" style="margin:0">${covered} of ${topics.length} topics touched by a completed session.</p></div>`,
      'teal', 'heart')}

    ${
      scores.length
        ? panel(
            'AVERAGE SCORE BY SUBJECT',
            `<div class="scroll-x">${barChart(
              subjects
                .map((s) => {
                  const mine = scores.filter((x) => x.subject_name === s.name);
                  if (!mine.length) return null;
                  return {
                    label: s.name,
                    value: mine.reduce((t, x) => t + (x.score / x.max_score) * 100, 0) / mine.length,
                  };
                })
                .filter(Boolean)
            )}</div>`,
            'orange',
            'chart'
          )
        : ''
    }

    ${
      charted.length
        ? charted
            .map(({ subject, history }) =>
              panel(
                `${subject.name} — READINESS TREND`,
                `<div class="scroll-x">${lineChart(
                  history.map((h) => ({ x: String(h.logged_at).slice(5, 10), y: h.readiness_score || 0 }))
                )}</div>`,
                'blue',
                'chart'
              )
            )
            .join('')
        : panel(
            'NO READINESS HISTORY YET',
            `<p class="muted" style="margin:0">Run the AI readiness prediction on the Optimizer page a couple of times and the trend lines will appear here.</p>`,
            'yellow',
            'qblock'
          )
    }
  </div>`;
}

/* ─── Tab 2: AI insights ─────────────────────────────────────────── */
function tabInsights(host) {
  host.innerHTML = `<div class="stack">
    ${panel(
      'CLOSE THE LOOP',
      `<p class="muted" style="margin:0">
        This compares every readiness prediction against what you actually scored, works out
        whether the model runs optimistic or pessimistic per subject, and turns that into
        study tips aimed at your specific pattern.
      </p>`,
      'purple',
      'brain'
    )}
    <button class="btn primary block" id="run-insights" style="font-size:13px;padding:18px">
      ${sprite('brain', 24)} GENERATE AI INSIGHTS
    </button>
    <div id="insight-out"></div>
  </div>`;

  el('#run-insights').addEventListener('click', async () => {
    const res = await withLoader('READING THE TEA LEAVES', () => api.insights());
    if (!res) return;
    toast('ok', 'INSIGHTS READY', '');
    const { accuracy, suggestions } = res;

    el('#insight-out').innerHTML = `<div class="stack">
      ${panel(
        'PREDICTION ACCURACY',
        `<div class="stack">
          <p class="muted" style="margin:0">${esc(accuracy.accuracy_summary || 'No paired predictions yet.')}</p>
          ${accuracy.reasoning ? dialogue('AI REASONING', accuracy.reasoning) : ''}
        </div>`,
        'blue',
        'target'
      )}

      ${
        (accuracy.subject_accuracy || []).length
          ? panel(
              'BY SUBJECT',
              accuracy.subject_accuracy
                .map((sa) => {
                  const bias = sa.bias || 'unknown';
                  const kind = bias === 'over-predicted' ? 'hard' : bias === 'under-predicted' ? 'medium' : 'easy';
                  return `<div class="list-row">
                    ${sprite('target', 24)}
                    <div class="grow">
                      <div class="rt">${esc(sa.subject || '')}</div>
                      <div class="rs">avg error ${Number(sa.avg_error || 0).toFixed(1)}% ${sa.trend ? '&middot; ' + esc(sa.trend) : ''}</div>
                    </div>
                    ${badge(bias.replace(/-/g, ' '), kind)}
                  </div>`;
                })
                .join(''),
              '',
              'chart'
            )
          : ''
      }

      ${
        (accuracy.model_adjustments || []).length
          ? panel(
              'MODEL ADJUSTMENTS',
              accuracy.model_adjustments
                .map((m) => `<div class="list-row">${sprite('bolt', 22)}<span class="grow">${esc(m)}</span></div>`)
                .join(''),
              'teal',
              'bolt'
            )
          : ''
      }

      ${panel(
        'PERSONALISED STUDY TIPS',
        (suggestions.suggestions || [])
          .map((t) => {
            const impact = t.impact || 'medium';
            return `<div class="list-row">
              ${sprite(impact === 'high' ? 'star' : impact === 'low' ? 'coin' : 'gem', 26)}
              <span class="grow">${esc(t.tip || '')}</span>
              ${badge(String(t.category || '').replace(/_/g, ' '), 'blue')}
              ${badge(impact, impact === 'high' ? 'hard' : impact === 'low' ? 'easy' : 'medium')}
            </div>`;
          })
          .join('') || '<p class="muted" style="margin:0">No tips returned.</p>',
        'yellow',
        'scroll'
      )}

      ${suggestions.overall_assessment ? dialogue('OVERALL ASSESSMENT', suggestions.overall_assessment, 'trophy') : ''}
    </div>`;
  });
}

/* ─── Tab 3: summary ─────────────────────────────────────────────── */
async function tabSummary(host) {
  const [scores, sessions] = await Promise.all([
    api.scores().catch(() => []),
    api.sessions().catch(() => []),
  ]);

  if (!scores.length && !sessions.length) {
    host.innerHTML = empty('NOTHING TO SUM UP', 'Play through a few levels first.');
    return;
  }

  const cards = [];
  for (const s of subjects) {
    const mineScores = scores.filter((x) => x.subject_name === s.name);
    const mineSessions = sessions.filter((x) => x.subject_name === s.name);
    const topics = await api.subjectTopics(s.id).catch(() => []);
    const done = mineSessions.filter((x) => x.status === 'completed');
    const mins = done.reduce((t, x) => t + (x.duration_min || 0), 0);
    const avg = mineScores.length
      ? mineScores.reduce((t, x) => t + (x.score / x.max_score) * 100, 0) / mineScores.length
      : null;

    cards.push(
      panel(
        `${s.name}${s.code ? ` (${s.code})` : ''}`,
        `<div class="grid grid-4">
          ${tile('Avg score', avg === null ? '—' : Math.round(avg) + '%', '', avg === null ? 'blue' : avg >= 70 ? 'green' : avg >= 50 ? 'orange' : 'red', 'chart')}
          ${tile('Sessions', `${done.length}/${mineSessions.length}`, '', 'teal', 'calendar')}
          ${tile('Study time', (mins / 60).toFixed(1) + 'h', '', 'purple', 'clock')}
          ${tile('Topics', topics.length, '', 'blue', 'brain')}
        </div>`,
        avg === null ? '' : avg >= 70 ? 'green' : avg >= 50 ? 'yellow' : 'red',
        'cartridge'
      )
    );
  }

  host.innerHTML = `<div class="stack">${cards.join('')}</div>`;
}
