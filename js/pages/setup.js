// pages/setup.js — LEVEL 1: subjects, uploads, current save data.
import { sprite } from '../sprites.js';
import { api } from '../api.js';
import {
  esc, el, els, badge, tile, empty, panel, dialogue, pageTitle, collapsible,
  tabs, mountTabs, toast, withLoader,
} from '../ui.js';

export function renderSetup() {
  return `<div class="page"><div class="wrap">
    ${pageTitle(1, 'DATA SETUP', 'Register your subjects, upload syllabi, and rate your own comfort level.', 'book')}
    ${tabs('setup-tabs', ['NEW SUBJECT', 'UPLOAD SCROLL', 'SAVE FILE'])}
    <div id="setup-body"></div>
  </div></div>`;
}

export function mountSetup() {
  mountTabs('setup-tabs', show);
  show(0);
}

async function show(idx) {
  const host = el('#setup-body');
  host.innerHTML = '<div class="empty">LOADING...</div>';
  const subjects = await api.subjects().catch(() => []);
  if (idx === 0) tabNewSubject(host);
  else if (idx === 1) tabUpload(host, subjects);
  else tabSaveFile(host, subjects);
}

/* ─── Tab 1: add a subject ───────────────────────────────────────── */
function tabNewSubject(host) {
  host.innerHTML = panel(
    'REGISTER A NEW SUBJECT',
    `<form id="subject-form" class="stack">
      <div class="grid grid-2">
        <label class="field"><span>Subject name *</span>
          <input type="text" name="name" placeholder="Data Structures &amp; Algorithms" required></label>
        <label class="field"><span>Subject code</span>
          <input type="text" name="code" placeholder="CS301"></label>
        <label class="field"><span>Credits</span>
          <input type="number" name="credits" value="3" min="1" max="6"></label>
        <label class="field"><span>Semester</span>
          <input type="number" name="semester" value="3" min="1" max="8"></label>
      </div>
      <label class="field">
        <span>Self-assessment — how comfortable are you? (1 = brutal, 10 = easy)</span>
        <div class="row">
          <input type="range" name="self_rating" min="1" max="10" step="0.5" value="5" class="grow">
          <span class="mono-num" id="rating-out" style="min-width:44px">5.0</span>
          <span id="rating-face">${sprite('coin', 30)}</span>
        </div>
      </label>
      <button class="btn primary block" type="submit">${sprite('star', 20)} ADD SUBJECT</button>
    </form>`,
    'blue',
    'book'
  );

  const range = el('[name=self_rating]');
  const out = el('#rating-out');
  const face = el('#rating-face');
  const paint = () => {
    const v = Number(range.value);
    out.textContent = v.toFixed(1);
    face.innerHTML = sprite(v >= 7 ? 'gem' : v >= 4 ? 'coin' : 'skull', 30);
  };
  range.addEventListener('input', paint);
  paint();

  el('#subject-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const body = {
      name: fd.get('name').trim(),
      code: fd.get('code').trim(),
      credits: Number(fd.get('credits')),
      semester: Number(fd.get('semester')),
      self_rating: Number(fd.get('self_rating')),
    };
    if (!body.name) return toast('err', 'NO NAME', 'Give the subject a name first.');
    try {
      const s = await api.addSubject(body);
      toast('ok', 'SUBJECT ADDED', `${s.name} joined the party.`);
      e.target.reset();
      paint();
      window.dispatchEvent(new Event('examflow:refresh'));
    } catch (err) {
      toast('err', 'FAILED', err.message);
    }
  });
}

/* ─── Tab 2: upload a syllabus / question paper ──────────────────── */
function tabUpload(host, subjects) {
  if (!subjects.length) {
    host.innerHTML = empty('NO SUBJECTS YET', 'Register a subject on the first tab before uploading anything.');
    return;
  }

  host.innerHTML = `<div class="stack">
    ${panel(
      'UPLOAD SYLLABUS OR QUESTION PAPER',
      `<div class="stack">
        <div class="grid grid-2">
          <label class="field"><span>Subject</span>
            <select id="up-subject">${subjects.map((s) => `<option value="${s.id}">${esc(s.name)}</option>`).join('')}</select>
          </label>
          <label class="field"><span>Document type</span>
            <select id="up-type">
              <option value="syllabus">Syllabus — extract units &amp; topics</option>
              <option value="notes">Study Notes / Slides / Handwritten Photos — for AI Tutor</option>
              <option value="question_paper">Question paper — find hot topics</option>
            </select>
          </label>
        </div>
        <div class="panel" id="type-hint-box" style="padding:10px 14px;background:var(--paper-2);border:2px dashed var(--blue);font-size:18px">
          📋 <b>Syllabus mode:</b> Extracts course modules and topics into your timetable.
        </div>
        <div>
        <div class="dropzone" id="dropzone">
          ${sprite('scroll', 54, 'bob')}
          <div class="zone-title" style="margin-top:12px">DROP A FILE HERE</div>
          <div class="muted" style="margin-top:6px">PDF, TXT, PNG or JPG &mdash; or click to browse</div>
          <div class="mono-num" id="picked" style="margin-top:12px;color:#2A6FDB"></div>
          <input type="file" id="file-input" accept=".pdf,.txt,.png,.jpg,.jpeg" hidden>
        </div>
        <button class="btn go block" id="do-upload" disabled>${sprite('bolt', 20)} PROCESS WITH AI</button>
      </div>`,
      'purple',
      'scroll'
    )}
    <div id="upload-result"></div>
    <div id="upload-history"></div>
  </div>`;

  const input = el('#file-input');
  const zone = el('#dropzone');
  const go = el('#do-upload');

  const pick = (file) => {
    if (!file) return;
    input.files = fileList(file);
    el('#picked').textContent = file.name;
    go.disabled = false;
  };

  const typeSelect = el('#up-type');
  const typeHint = el('#type-hint-box');
  if (typeSelect && typeHint) {
    typeSelect.addEventListener('change', () => {
      if (typeSelect.value === 'notes') {
        typeHint.style.borderColor = 'var(--green)';
        typeHint.innerHTML = '📚 <b>Study Notes &amp; Handwritten mode:</b> Upload college lecture slides, textbook PDFs, or photos of handwritten notes (PNG/JPG). Upload anytime as you receive materials! The AI Tutor in the Focus Arena will directly reference these notes when compressing your study material.';
      } else if (typeSelect.value === 'syllabus') {
        typeHint.style.borderColor = 'var(--blue)';
        typeHint.innerHTML = '📋 <b>Syllabus mode:</b> Extracts course modules and topics into your timetable.';
      } else {
        typeHint.style.borderColor = 'var(--orange)';
        typeHint.innerHTML = '🎯 <b>Question paper mode:</b> Analyzes previous exam papers to find high-weightage topics.';
      }
    });
  }

  zone.addEventListener('click', () => input.click());
  input.addEventListener('change', () => pick(input.files[0]));
  ['dragenter', 'dragover'].forEach((ev) =>
    zone.addEventListener(ev, (e) => { e.preventDefault(); zone.classList.add('over'); })
  );
  ['dragleave', 'drop'].forEach((ev) =>
    zone.addEventListener(ev, (e) => { e.preventDefault(); zone.classList.remove('over'); })
  );
  zone.addEventListener('drop', (e) => pick(e.dataTransfer.files[0]));

  go.addEventListener('click', async () => {
    const file = input.files[0];
    if (!file) return;
    const fd = new FormData();
    fd.append('file', file);
    fd.append('subject_id', el('#up-subject').value);
    fd.append('file_type', el('#up-type').value);

    const isImage = /\.(png|jpe?g|webp)$/i.test(file.name);
    const label = isImage ? 'READING THE IMAGE' : 'PARSING DOCUMENT';
    const res = await withLoader(label, () => api.upload(fd));
    if (!res) return;
    renderUploadResult(res);
    loadHistory();
    window.dispatchEvent(new Event('examflow:refresh'));
  });

  loadHistory();
}

function fileList(file) {
  const dt = new DataTransfer();
  dt.items.add(file);
  return dt.files;
}

function renderUploadResult(res) {
  const host = el('#upload-result');
  const how = res.cached
    ? 'Served from cache — identical file already parsed.'
    : res.route === 'vision'
      ? 'Read directly by the vision model.'
      : res.route === 'ocr'
        ? 'Read with on-device OCR.'
        : '';

  if (res.kind === 'notes') {
    toast('ok', res.cached ? 'LOADED FROM CACHE' : 'STUDY NOTES ATTACHED', `${res.title || 'Study material'} linked to subject. ${how}`);
    host.innerHTML = panel(
      'STUDY NOTES ATTACHED TO SUBJECT',
      `<div class="stack">
        <div class="row-tight">
          <span class="badge green">✓ AI TUTOR SYNCED</span>
          <span class="badge blue">${esc(res.title || 'Class Material')}</span>
        </div>
        ${res.summary ? dialogue('NOTES SUMMARY', res.summary, 'brain') : ''}
        ${res.concepts && res.concepts.length ? `
          <div>
            <div class="mono-num" style="font-size:12px;margin-bottom:6px">KEY CONCEPTS DETECTED:</div>
            <div class="row-tight">
              ${res.concepts.map(c => `<span class="badge">${esc(c)}</span>`).join('')}
            </div>
          </div>
        ` : ''}
        <p class="muted tiny" style="margin:0">
          ★ The AI Adaptive Tutor in the Focus Arena will now reference these class notes when generating your compressed study cards for this subject! You can upload notes for other modules anytime as college provides them.
        </p>
      </div>`,
      'green',
      'book'
    );
  } else if (res.kind === 'syllabus') {
    toast('ok', res.cached ? 'LOADED FROM CACHE' : 'SYLLABUS PARSED', `${res.topic_count} topics extracted. ${how}`);
    host.innerHTML = panel(
      `EXTRACTED ${res.topic_count} TOPICS`,
      `<div class="stack">
        ${res.reasoning ? dialogue('AI REASONING', res.reasoning) : ''}
        ${res.units
          .map(
            (u) => `<div>
              <div class="unit-bar">${sprite('brick', 18)}<span>${esc(u.unit_name || 'General')}</span></div>
              ${(u.topics || [])
                .map(
                  (t) => `<div class="list-row">
                    ${sprite('star', 22)}
                    <span class="grow rt">${esc(t.topic_name)}</span>
                    <span class="rs">${esc(t.estimated_hours ?? 2)}h</span>
                  </div>`
                )
                .join('')}
            </div>`
          )
          .join('')}
      </div>`,
      'green',
      'trophy'
    );
  } else {
    const topics = res.important_topics || [];
    toast('ok', res.cached ? 'LOADED FROM CACHE' : 'PAPER ANALYSED', `${topics.length} high-value topics found. ${how}`);
    host.innerHTML = panel(
      'HIGH-VALUE TOPICS',
      topics.length
        ? topics
            .map(
              (t) => `<div class="list-row">
                ${sprite('target', 22)}
                <span class="grow rt">${esc(t.topic)}</span>
                ${badge(t.frequency || 'medium', freqKind(t.frequency))}
                <span class="rs">${esc(t.marks_weight || '')}</span>
              </div>`
            )
            .join('')
        : empty('NOTHING FOUND', 'The parser could not pull topics out of that paper.'),
      'orange',
      'target'
    );
  }
}

const freqKind = (f) => (f === 'high' ? 'hard' : f === 'low' ? 'easy' : 'medium');

async function loadHistory() {
  const host = el('#upload-history');
  if (!host) return;
  const files = await api.files().catch(() => []);
  if (!files.length) { host.innerHTML = ''; return; }
  host.innerHTML = collapsible(
    'UPLOAD LOG',
    files
      .map(
        (f) => `<div class="list-row">
          ${sprite(f.processed ? 'floppy' : 'clock', 22)}
          <span class="grow rt">${esc(f.filename)}</span>
          <span class="rs">${esc(f.file_type || '')}</span>
          ${badge(f.processed ? 'processed' : 'pending', f.processed ? 'success' : 'warning')}
        </div>`
      )
      .join(''),
    { icon: 'floppy', note: `${files.length} FILES` }
  );
}

/* ─── Tab 3: the save file ───────────────────────────────────────── */
async function tabSaveFile(host, subjects) {
  const stats = await api.stats().catch(() => ({ subjects: 0, topics: 0, files: 0, exams: 0 }));

  host.innerHTML = `<div class="stack">
    <div class="grid grid-4">
      ${tile('Subjects', stats.subjects, '', 'blue', 'book')}
      ${tile('Topics', stats.topics, '', 'purple', 'brain')}
      ${tile('Files', stats.files, '', 'orange', 'floppy')}
      ${tile('Exams', stats.exams, '', 'red', 'calendar')}
    </div>
    ${
      subjects.length
        ? panel(
            'REGISTERED SUBJECTS',
            subjects
              .map((s) => {
                const r = s.self_rating;
                const kind = r >= 7 ? 'easy' : r >= 4 ? 'medium' : 'hard';
                return `<div class="list-row">
                  ${sprite('cartridge', 26)}
                  <div class="grow">
                    <div class="rt">${esc(s.name)}</div>
                    <div class="rs">${esc(s.code || 'no code')} &middot; ${esc(s.credits)} credits &middot; sem ${esc(s.semester)}</div>
                  </div>
                  ${badge(`self ${r}/10`, kind)}
                  <button class="ibtn no" data-del="${s.id}" title="Delete ${esc(s.name)}">&times;</button>
                </div>`;
              })
              .join(''),
            'teal',
            'cartridge'
          )
        : empty('EMPTY SAVE FILE', 'No subjects registered yet. Add one, or load the demo save from the home screen.')
    }
  </div>`;

  els('[data-del]', host).forEach((btn) =>
    btn.addEventListener('click', async () => {
      const id = btn.dataset.del;
      const name = subjects.find((s) => String(s.id) === id)?.name || 'this subject';
      if (!confirm(`Delete "${name}" and everything attached to it (topics, sessions, scores, exams)?\n\nThis cannot be undone.`)) return;
      try {
        await api.deleteSubject(id);
        toast('ok', 'DELETED', `${name} removed from the save file.`);
        show(2);
        window.dispatchEvent(new Event('examflow:refresh'));
      } catch (err) {
        toast('err', 'FAILED', err.message);
      }
    })
  );
}
