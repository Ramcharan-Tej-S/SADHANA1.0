// parkingLot.js — Global Thought Parking Lot for SADHANA
// Persists parked thoughts in localStorage so they survive page reloads
// and are accessible from every screen, not just the Focus Arena.

const STORAGE_KEY = 'sadhana:parkingLot';

/* ─── Data helpers ───────────────────────────────────────────────── */

/** @returns {{ id:number, text:string, ts:string }[]} */
export function loadAll() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch { return []; }
}

function _save(items) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  _notifyBadge();
}

/** Add a new thought and return its id. */
export function addThought(text) {
  const items = loadAll();
  const entry = { id: Date.now(), text, ts: new Date().toISOString() };
  items.unshift(entry);           // newest first
  _save(items);
  return entry.id;
}

/** Remove a thought by id. */
export function removeThought(id) {
  _save(loadAll().filter((t) => t.id !== id));
}

/** Clear every thought. */
export function clearAll() {
  _save([]);
}

/** How many thoughts are currently parked? */
export function count() {
  return loadAll().length;
}

/* ─── HUD badge ──────────────────────────────────────────────────── */

function _notifyBadge() {
  const btn = document.getElementById('global-parking-btn');
  if (btn) {
    const n = count();
    btn.querySelector('.parking-count').textContent = n;
    btn.classList.toggle('has-items', n > 0);
  }
}

/* ─── Drawer UI ──────────────────────────────────────────────────── */

function _renderDrawer() {
  const drawer = document.getElementById('parking-drawer');
  if (!drawer) return;

  const items = loadAll();

  drawer.querySelector('.parking-drawer-body').innerHTML = items.length
    ? items
        .map(
          (t) => `<div class="parking-row">
            <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1">${_esc(t.text)}</span>
            <button class="ibtn sm" data-park-rm="${t.id}" title="Dismiss" style="width:28px;height:28px;font-size:14px">✕</button>
          </div>`
        )
        .join('')
    : '<div class="tiny muted center" style="padding:18px 0">No thoughts parked. Focus is steady. 🧘</div>';

  // wire dismiss buttons
  drawer.querySelectorAll('[data-park-rm]').forEach((b) => {
    b.addEventListener('click', () => {
      removeThought(Number(b.dataset.parkRm));
      _renderDrawer();
    });
  });
}

/** Minimal HTML escaper (same as ui.js esc but we avoid the import to keep this standalone). */
function _esc(v) {
  if (v == null) return '';
  return String(v).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

/* ─── Init (call once on app boot) ───────────────────────────────── */

export function initParkingLotHUD() {
  // ── Button in HUD bar ──
  const hudTools = document.getElementById('hud-tools') || document.querySelector('.hud-inner');
  if (!hudTools) return;

  const btn = document.createElement('button');
  btn.id = 'global-parking-btn';
  btn.className = 'hud-fx';
  btn.title = 'Open Thought Parking Lot';
  btn.innerHTML = `🅿 <span class="parking-count">${count()}</span>`;
  btn.classList.toggle('has-items', count() > 0);
  btn.addEventListener('click', _toggleDrawer);
  hudTools.prepend(btn);

  // ── Drawer (slides in from the right) ──
  const drawer = document.createElement('div');
  drawer.id = 'parking-drawer';
  drawer.className = 'parking-drawer hidden';
  drawer.innerHTML = `
    <div class="parking-drawer-head">
      <span>THOUGHT PARKING LOT</span>
      <button class="ibtn sm" id="parking-close" title="Close" style="width:28px;height:28px;font-size:14px">✕</button>
    </div>
    <div class="parking-drawer-add">
      <input type="text" id="global-park-input" placeholder="Park a thought…" style="flex:1;font-size:18px;padding:7px 10px">
      <button class="btn sm go" id="global-park-btn">PARK</button>
    </div>
    <div class="parking-drawer-body"></div>
    <button class="btn sm danger block" id="parking-clear-all" style="margin-top:12px">CLEAR ALL</button>
  `;
  document.body.appendChild(drawer);

  // wire inner controls
  drawer.querySelector('#parking-close').addEventListener('click', _toggleDrawer);
  drawer.querySelector('#global-park-btn').addEventListener('click', _handleAdd);
  drawer.querySelector('#global-park-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter') _handleAdd();
  });
  drawer.querySelector('#parking-clear-all').addEventListener('click', () => {
    clearAll();
    _renderDrawer();
  });

  _renderDrawer();
}

function _handleAdd() {
  const inp = document.getElementById('global-park-input');
  const val = inp?.value.trim();
  if (!val) return;
  addThought(val);
  inp.value = '';
  _renderDrawer();
}

function _toggleDrawer() {
  const drawer = document.getElementById('parking-drawer');
  if (!drawer) return;
  drawer.classList.toggle('hidden');
  if (!drawer.classList.contains('hidden')) {
    _renderDrawer();
    document.getElementById('global-park-input')?.focus();
  }
}
