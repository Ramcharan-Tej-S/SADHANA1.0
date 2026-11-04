// pages/syllabus.js — LEVEL 2: topic tree + LLM-as-Judge difficulty scoring.
import { sprite, difficultySprite } from '../sprites.js';
import { api } from '../api.js';
import {
  esc, el, els, badge, tile, empty, panel, dialogue, pageTitle,
  tabs, mountTabs, meter, stackBar, toast, withLoader, trunc,
  collapsible, radarChart,
} from '../ui.js';

let subjects = [];

export function renderSyllabus() {
  return `<div class="page"><div class="wrap">
    ${pageTitle(2, 'SYLLABUS MODEL', 'Every topic scored by a three-pass LLM-as-Judge, reasoning included.', 'brain')}
    <div id="syl-overview" class="stack" style="margin-bottom:28px"></div>
    <div id="syl-tabs"></div>
    <div id="syl-body"></div>
  </div></div>`;
}

export async function mountSyllabus() {
  subjects = await api.subjects().catch(() => []);
  const overview = el('#syl-overview');

  if (!subjects.length) {
    overview.innerHTML = empty('NO SUBJECTS', 'Head to Data Setup and register a subject first.');
    return;
  }

  const [topics, diffs] = await Promise.all([
    api.topics().catch(() => []),
    api.difficulties().catch(() => []),
  ]);

  const easy = diffs.filter((d) => d.level === 'easy').length;
  const med = diffs.filter((d) => d.level === 'medium').length;
  const hard = diffs.filter((d) => d.level === 'hard').length;
  const unscored = Math.max(0, topics.length - diffs.length);

  overview.innerHTML = `
    <div class="grid grid-4">
      ${tile('Total topics', topics.length, '', 'blue', 'brain')}
      ${tile('Easy', easy, '', 'green', 'gem')}
      ${tile('Medium', med, '', 'orange', 'coin')}
      ${tile('Hard', hard, '', 'red', 'skull')}
    </div>
    ${
      diffs.length
        ? panel(
            'DIFFICULTY SPREAD',
            stackBar([
              { label: 'Easy', value: easy, color: 'green' },
              { label: 'Medium', value: med, color: 'yellow' },
              { label: 'Hard', value: hard, color: 'red' },
              { label: 'Unscored', value: unscored, color: 'purple' },
            ]),
            'purple',
            'chart'
          )
        : panel(
            'NOTHING SCORED YET',
            `<p class="muted" style="margin:0">Pick a subject below and run the AI difficulty assessment to fill this in.</p>`,
            'yellow',
            'qblock'
          )
    }`;

  el('#syl-tabs').innerHTML = tabs('syl-tabstrip', subjects.map((s) => trunc(s.name.toUpperCase(), 22)));
  mountTabs('syl-tabstrip', showSubject);
  showSubject(0);
}

async function showSubject(idx) {
  const host = el('#syl-body');
  const subject = subjects[idx];
  if (!subject) return;
  host.innerHTML = '<div class="empty">LOADING...</div>';

  const topics = await api.subjectTopics(subject.id).catch(() => []);

  if (!topics.length) {
    host.innerHTML = `<div class="stack">
      ${empty('NO TOPICS', `Nothing parsed for ${subject.name} yet. Upload a syllabus, or add topics by hand below.`, 'scroll')}
      ${collapsible('ADD A TOPIC BY HAND', manualTopicFields(), { open: true, icon: 'scroll' })}
    </div>`;
    wireManualForm(subject, idx);
    return;
  }

  // Group topics by unit, preserving order of first appearance.
  const units = new Map();
  topics.forEach((t) => {
    const u = t.unit_name || 'General';
    if (!units.has(u)) units.set(u, []);
    units.get(u).push(t);
  });

  const scored = topics.filter((t) => t.difficulty);
  const avg = scored.length
    ? scored.reduce((s, t) => s + t.difficulty.score, 0) / scored.length
    : 0;

  host.innerHTML = `<div class="stack">
    <div class="grid grid-3">
      ${tile('Topics', topics.length, `${scored.length} scored`, 'blue', 'brain')}
      ${tile('Avg difficulty', avg ? avg.toFixed(1) + '/10' : '—', '', 'orange', 'target')}
      ${tile('Est. hours', topics.reduce((s, t) => s + (t.estimated_hours || 0), 0).toFixed(1) + 'h', '', 'teal', 'clock')}
    </div>

    <button class="btn primary block" id="run-assess">
      ${sprite('brain', 22)} RUN 3-PASS DIFFICULTY ASSESSMENT
    </button>

    ${
      scored.length >= 3
        ? panel(
            'DIFFICULTY RADAR',
            (() => {
              // Beyond ~16 spokes the labels collide, so show the hardest ones.
              const CAP = 16;
              const all = scored
                .map((t) => ({ label: t.topic_name, value: t.difficulty.score }))
                .sort((a, b) => b.value - a.value);
              const shown = all.slice(0, CAP);
              return `<div class="scroll-x">${radarChart(shown, { max: 10, color: 'purple', unit: '/10' })}</div>
                <p class="muted tiny" style="margin:10px 0 0">
                  Each spoke is one topic, scored 0-10 by the judge. Spikes are where the work is.${
                    all.length > CAP ? ` Showing the ${CAP} hardest of ${all.length} scored topics.` : ''
                  }
                </p>`;
            })(),
            'purple',
            'target'
          )
        : ''
    }

    ${[...units.entries()]
      .map(([unitName, list], i) =>
        collapsible(unitName, list.map(topicRow).join(''), {
          open: i === 0, // first unit open, the rest on demand
          icon: 'brick',
          note: `${list.length} TOPICS`,
        })
      )
      .join('')}

    ${collapsible(`ADD A TOPIC TO ${trunc(subject.name.toUpperCase(), 22)}`, manualTopicFields(), {
      icon: 'scroll',
    })}
  </div>`;

  // Expand/collapse reasoning
  els('[data-reason]', host).forEach((btn) =>
    btn.addEventListener('click', () => {
      const box = el(`#reason-${btn.dataset.reason}`);
      box.hidden = !box.hidden;
      btn.textContent = box.hidden ? 'WHY?' : 'HIDE';
    })
  );

  el('#run-assess').addEventListener('click', async () => {
    const res = await withLoader('JUDGING TOPICS', () => api.assess(subject.id));
    if (!res) return;
    if (res.saved > 0) {
      toast('ok', 'ASSESSMENT COMPLETE', `${res.saved} topics scored across three passes.`);
      mountSyllabus();
    } else {
      toast('err', 'NO MATCHES', 'The judge returned results but none could be matched to your topics.');
    }
  });

  wireManualForm(subject, idx);
}

function topicRow(t) {
  const d = t.difficulty;
  if (!d) {
    return `<div class="list-row">
      ${sprite('qblock', 24)}
      <div class="grow">
        <div class="rt">${esc(t.topic_name)}</div>
        <div class="rs">${esc(t.estimated_hours ?? 2)}h estimated</div>
      </div>
      ${badge('not scored', '')}
    </div>`;
  }
  const conf = Math.round((d.confidence || 0) * 100);
  return `<div style="margin-bottom:10px">
    <div class="list-row" style="margin-bottom:0">
      ${difficultySprite(d.level, 24)}
      <div class="grow">
        <div class="rt">${esc(t.topic_name)}</div>
        <div class="rs">${esc(t.estimated_hours ?? 2)}h &middot; confidence ${conf}%</div>
      </div>
      <span class="mono-num" style="color:#2A6FDB">${esc(d.score)}/10</span>
      ${badge(d.level, d.level)}
      ${d.reasoning ? `<button class="btn sm ghost" data-reason="${t.id}">WHY?</button>` : ''}
    </div>
    ${
      d.reasoning
        ? `<div id="reason-${t.id}" hidden style="margin:8px 0 0 22px">
             ${dialogue('JUDGE VERDICT', d.reasoning)}
             <div style="margin-top:10px;max-width:320px">
               <div class="tiny muted">CONFIDENCE</div>${meter(conf)}
             </div>
           </div>`
        : ''
    }
  </div>`;
}

function manualTopicFields() {
  return `<form id="topic-form" class="stack">
      <div class="grid grid-3">
        <label class="field"><span>Topic name *</span><input type="text" name="topic_name" required></label>
        <label class="field"><span>Unit</span><input type="text" name="unit_name" placeholder="Unit 1"></label>
        <label class="field"><span>Estimated hours</span>
          <input type="number" name="estimated_hours" value="2" min="0.5" max="20" step="0.5"></label>
      </div>
      <button class="btn block" type="submit">${sprite('star', 20)} ADD TOPIC</button>
    </form>`;
}

function wireManualForm(subject, idx) {
  el('#topic-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await api.addTopic({
        subject_id: subject.id,
        topic_name: fd.get('topic_name').trim(),
        unit_name: fd.get('unit_name').trim(),
        estimated_hours: Number(fd.get('estimated_hours')),
      });
      toast('ok', 'TOPIC ADDED', fd.get('topic_name'));
      showSubject(idx);
    } catch (err) {
      toast('err', 'FAILED', err.message);
    }
  });
}
