// pages/schedule.js — LEVEL 3: exam countdowns + the weekly availability grid.
import { sprite } from '../sprites.js';
import { api } from '../api.js';
import {
  esc, el, els, badge, tile, empty, panel, pageTitle,
  tabs, mountTabs, toast, fmtDate, daysUntil, todayISO,
} from '../ui.js';

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

let subjects = [];

export function renderSchedule() {
  return `<div class="page"><div class="wrap">
    ${pageTitle(3, 'SCHEDULE', 'Set the boss timers and the hours you can actually show up.', 'calendar')}
    ${tabs('sch-tabs', ['EXAM DATES', 'AVAILABILITY', 'OVERVIEW'])}
    <div id="sch-body"></div>
  </div></div>`;
}

export async function mountSchedule() {
  subjects = await api.subjects().catch(() => []);
  mountTabs('sch-tabs', show);
  show(0);
}

async function show(idx) {
  const host = el('#sch-body');
  if (!subjects.length) {
    host.innerHTML = empty('NO SUBJECTS', 'Register subjects in Data Setup before scheduling anything.');
    return;
  }
  host.innerHTML = '<div class="empty">LOADING...</div>';
  if (idx === 0) await tabExams(host);
  else if (idx === 1) await tabAvailability(host);
  else await tabOverview(host);
}

/* ─── Tab 1: exam dates ──────────────────────────────────────────── */
async function tabExams(host) {
  const exams = await api.exams(false).catch(() => []);
  const byId = {};
  exams.forEach((e) => { byId[e.subject_id] = e; });

  const defaultDate = new Date(Date.now() + 14 * 86400000).toISOString().slice(0, 10);

  host.innerHTML = panel(
    'SET EXAM DATES',
    `<div class="stack">
      ${subjects
        .map((s) => {
          const ex = byId[s.id];
          const d = ex?.exam_date || defaultDate;
          const t = ex?.exam_time || '09:00';
          const past = ex && daysUntil(ex.exam_date) < 0;
          return `<div class="list-row" style="align-items:flex-end">
            ${sprite('cartridge', 26)}
            <div class="grow">
              <div class="rt">${esc(s.name)}</div>
              <div class="rs">${
                ex ? (past ? `past: ${esc(ex.exam_date)}` : `scheduled: ${esc(ex.exam_date)}`) : 'not scheduled'
              }</div>
            </div>
            <label class="field" style="width:180px"><span>Date</span>
              <input type="date" data-date="${s.id}" value="${esc(d)}"></label>
            <label class="field" style="width:130px"><span>Time</span>
              <select data-time="${s.id}">
                <option value="09:00" ${t === '09:00' ? 'selected' : ''}>09:00</option>
                <option value="14:00" ${t === '14:00' ? 'selected' : ''}>14:00</option>
              </select></label>
          </div>`;
        })
        .join('')}
      <button class="btn primary block" id="save-exams">${sprite('floppy', 20)} SAVE EXAM SCHEDULE</button>
    </div>`,
    'red',
    'calendar'
  );

  el('#save-exams').addEventListener('click', async () => {
    const btn = el('#save-exams');
    btn.disabled = true;
    try {
      for (const s of subjects) {
        const date = el(`[data-date="${s.id}"]`).value;
        const time = el(`[data-time="${s.id}"]`).value;
        if (date) await api.saveExam({ subject_id: s.id, exam_date: date, exam_time: time });
      }
      toast('ok', 'TIMERS SET', 'Exam schedule saved.');
      window.dispatchEvent(new Event('examflow:refresh'));
      show(0);
    } catch (err) {
      toast('err', 'FAILED', err.message);
    } finally {
      btn.disabled = false;
    }
  });
}

/* ─── Tab 2: availability grid ───────────────────────────────────── */
async function tabAvailability(host) {
  const saved = await api.availability().catch(() => []);
  const byDay = {};
  saved.forEach((a) => { byDay[a.day_of_week] = a; });

  host.innerHTML = panel(
    'WEEKLY AVAILABILITY',
    `<div class="stack">
      <p class="muted" style="margin:0">
        The optimizer will never schedule a session outside these windows. Mark your sharpest hours
        as peak focus and hard topics get pushed into them.
      </p>
      ${DAYS.map((day) => {
        const a = byDay[day];
        return `<div class="list-row" style="align-items:flex-end;flex-wrap:wrap">
          ${sprite(day === 'Saturday' || day === 'Sunday' ? 'star' : 'clock', 24)}
          <div class="rt" style="width:120px">${day.toUpperCase().slice(0, 3)}</div>
          <label class="field" style="width:130px"><span>From</span>
            <input type="time" data-start="${day}" value="${esc(a?.start_time || '06:00')}"></label>
          <label class="field" style="width:130px"><span>To</span>
            <input type="time" data-end="${day}" value="${esc(a?.end_time || '20:00')}"></label>
          <label class="field" style="width:150px"><span>Energy</span>
            <select data-energy="${day}">
              ${['low', 'medium', 'high']
                .map((lv) => `<option value="${lv}" ${(a?.energy_level || 'medium') === lv ? 'selected' : ''}>${lv}</option>`)
                .join('')}
            </select></label>
          <label class="check" style="padding-bottom:8px">
            <input type="checkbox" data-peak="${day}" ${a?.is_peak ? 'checked' : ''}>
            <span class="box">✓</span><span>Peak focus</span>
          </label>
        </div>`;
      }).join('')}
      <button class="btn primary block" id="save-avail">${sprite('floppy', 20)} SAVE AVAILABILITY</button>
    </div>`,
    'teal',
    'clock'
  );

  el('#save-avail').addEventListener('click', async () => {
    const rows = [];
    for (const day of DAYS) {
      const start = el(`[data-start="${day}"]`).value;
      const end = el(`[data-end="${day}"]`).value;
      if (!start || !end) continue;
      if (end <= start) {
        return toast('err', 'BAD WINDOW', `${day}: the end time must be after the start time.`);
      }
      rows.push({
        day_of_week: day,
        start_time: start,
        end_time: end,
        is_peak: el(`[data-peak="${day}"]`).checked,
        energy_level: el(`[data-energy="${day}"]`).value,
      });
    }
    try {
      await api.saveAvailability(rows);
      toast('ok', 'SAVED', `${rows.length} day windows locked in.`);
    } catch (err) {
      toast('err', 'FAILED', err.message);
    }
  });
}

/* ─── Tab 3: overview ────────────────────────────────────────────── */
async function tabOverview(host) {
  const [exams, avail] = await Promise.all([
    api.exams(true).catch(() => []),
    api.availability().catch(() => []),
  ]);

  let totalH = 0, peakH = 0;
  avail.forEach((a) => {
    const h = hoursBetween(a.start_time, a.end_time);
    totalH += h;
    if (a.is_peak) peakH += h;
  });

  host.innerHTML = `<div class="stack">
    ${
      exams.length
        ? panel(
            'BOSS TIMERS',
            exams
              .map((e) => {
                const d = daysUntil(e.exam_date);
                const kind = d <= 0 ? 'danger' : d <= 3 ? 'danger' : d <= 7 ? 'warning' : 'info';
                const icon = d <= 3 ? 'skull' : d <= 7 ? 'bolt' : 'flag';
                return `<div class="list-row">
                  ${sprite(icon, 28, d <= 3 ? 'bob' : '')}
                  <div class="grow">
                    <div class="rt">${esc(e.subject_name)}</div>
                    <div class="rs">${esc(fmtDate(e.exam_date))} at ${esc(e.exam_time || '09:00')}</div>
                  </div>
                  <span class="mono-num" style="font-size:16px">${d <= 0 ? 'TODAY' : d + 'd'}</span>
                  ${badge(d <= 0 ? 'now' : d <= 3 ? 'critical' : d <= 7 ? 'soon' : 'on track', kind)}
                  <button class="btn sm go" data-done="${e.id}">DONE</button>
                </div>`;
              })
              .join(''),
            'red',
            'target'
          )
        : empty('NO UPCOMING EXAMS', 'Past and completed exams drop off this list automatically. Set new dates on the first tab.', 'flag')
    }

    ${
      avail.length
        ? `<div class="grid grid-3">
             ${tile('Weekly hours', totalH.toFixed(0) + 'h', '', 'blue', 'clock')}
             ${tile('Peak focus', peakH.toFixed(0) + 'h', '', 'purple', 'bolt')}
             ${tile('Active days', `${new Set(avail.map((a) => a.day_of_week)).size}/7`, '', 'green', 'calendar')}
           </div>`
        : ''
    }

    ${exams.length ? `<button class="btn danger" id="purge">${sprite('skull', 20)} PURGE PAST &amp; COMPLETED EXAMS</button>` : ''}
  </div>`;

  els('[data-done]', host).forEach((b) =>
    b.addEventListener('click', async () => {
      await api.completeExam(b.dataset.done).catch((e) => toast('err', 'FAILED', e.message));
      toast('ok', 'BOSS DOWN', 'Exam marked complete.');
      show(2);
      window.dispatchEvent(new Event('examflow:refresh'));
    })
  );

  el('#purge')?.addEventListener('click', async () => {
    if (!confirm('Permanently delete every past and completed exam record?')) return;
    const res = await api.purgeExams().catch((e) => { toast('err', 'FAILED', e.message); return null; });
    if (res) {
      toast('ok', 'CLEARED', `${res.removed} old exam records deleted.`);
      show(2);
    }
  });
}

function hoursBetween(a, b) {
  const [ah, am] = String(a).split(':').map(Number);
  const [bh, bm] = String(b).split(':').map(Number);
  if ([ah, am, bh, bm].some(Number.isNaN)) return 0;
  return Math.max(0, (bh * 60 + bm - (ah * 60 + am)) / 60);
}

export { todayISO };
