// distractionBlocker.js — SADHANA Focus Shield
// Manages distraction app blocking preferences and triggers Android Focus Mode.
// Falls back gracefully on desktop browsers.

const BLOCKER_KEY     = 'sadhana:blocker:apps';
const BLOCKER_ON_KEY  = 'sadhana:blocker:enabled';

/* ─── Curated list of common distracting apps ─────────────────────── */
export const DISTRACTION_APPS = [
  { id: 'instagram', name: 'Instagram',       emoji: '📷' },
  { id: 'snapchat',  name: 'Snapchat',        emoji: '👻' },
  { id: 'youtube',   name: 'YouTube',          emoji: '▶️' },
  { id: 'tiktok',    name: 'TikTok',           emoji: '🎵' },
  { id: 'twitter',   name: 'X / Twitter',      emoji: '🐦' },
  { id: 'facebook',  name: 'Facebook',         emoji: '👍' },
  { id: 'whatsapp',  name: 'WhatsApp',         emoji: '💬' },
  { id: 'telegram',  name: 'Telegram',         emoji: '✈️' },
  { id: 'discord',   name: 'Discord',          emoji: '🎮' },
  { id: 'reddit',    name: 'Reddit',           emoji: '🤖' },
  { id: 'netflix',   name: 'Netflix',          emoji: '🎬' },
  { id: 'games',     name: 'Mobile Games',     emoji: '🕹️' },
];

/* ─── Preference helpers ───────────────────────────────────────────── */
export function getBlockedApps() {
  try { return JSON.parse(localStorage.getItem(BLOCKER_KEY) || '[]'); }
  catch { return []; }
}
export function setBlockedApps(ids) {
  try { localStorage.setItem(BLOCKER_KEY, JSON.stringify(ids)); } catch {}
}
export function isBlockerEnabled() {
  try { return localStorage.getItem(BLOCKER_ON_KEY) === '1'; } catch { return false; }
}
export function setBlockerEnabled(val) {
  try { localStorage.setItem(BLOCKER_ON_KEY, val ? '1' : '0'); } catch {}
}

/* ─── Platform detection ───────────────────────────────────────────── */
export function isAndroid() {
  return /Android/i.test(navigator.userAgent);
}
function isMIUI() {
  return /XiaoMi|MI |Redmi|POCO|miui/i.test(navigator.userAgent);
}

/* ─── Trigger Android Focus / DND mode ────────────────────────────── */
export function triggerAndroidFocusMode() {
  let intentUrl;

  if (isMIUI()) {
    // Xiaomi / Redmi / POCO — MIUI Focus Mode deep link
    intentUrl = 'intent:#Intent;action=android.intent.action.MAIN;category=android.intent.category.DEFAULT;component=com.miui.powerkeeper/.ui.HardwareControlActivity;end';
  } else {
    // Stock Android — Digital Wellbeing Focus Mode
    intentUrl = 'intent:#Intent;action=android.settings.ZEN_MODE_SETTINGS;end';
  }

  try {
    window.location.href = intentUrl;
  } catch {
    // fallback: open generic settings
    window.open('https://support.google.com/android/answer/9654720', '_blank', 'noopener');
  }
}

/* ─── Render the blocker app-picker (used in setup screen) ────────── */
export function renderBlockerSetup() {
  const selected = getBlockedApps();
  const enabled  = isBlockerEnabled();

  return `
    <div id="blocker-setup-section">
      <div class="spread" style="margin-bottom:10px">
        <div>
          <div class="mono-num" style="font-size:13px;color:var(--ink-soft)">
            3. FOCUS SHIELD — DISTRACTION BLOCKER
          </div>
          <p class="muted tiny" style="margin:4px 0 0">
            When you enter the arena, SADHANA will prompt you to activate your phone's
            built-in <b>Focus Mode / Digital Wellbeing</b> to block the apps you select below.
          </p>
        </div>
        <label class="blocker-toggle" title="Enable distraction blocker on arena entry">
          <input type="checkbox" id="blocker-master-toggle" ${enabled ? 'checked' : ''}>
          <span class="blocker-slider"></span>
          <span class="mono-num" style="font-size:10px">${enabled ? 'ON' : 'OFF'}</span>
        </label>
      </div>

      <div id="blocker-app-grid" style="${enabled ? '' : 'opacity:.4;pointer-events:none'}">
        <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:8px">
          ${DISTRACTION_APPS.map(a => `
            <button class="blocker-app-chip ${selected.includes(a.id) ? 'selected' : ''}"
                    data-app-id="${a.id}"
                    title="${a.name}">
              ${a.emoji} ${a.name}
            </button>`).join('')}
        </div>
        <p class="muted tiny" style="margin:0">
          Tap to toggle. Selected apps will appear on the Lockdown Shield when you start a session.
        </p>
      </div>
    </div>`;
}

/* ─── Mount blocker setup interactions ────────────────────────────── */
export function mountBlockerSetup(container) {
  const masterToggle = container.querySelector('#blocker-master-toggle');
  const appGrid      = container.querySelector('#blocker-app-grid');
  const chips        = container.querySelectorAll('.blocker-app-chip');
  const masterLabel  = masterToggle?.parentElement?.querySelector('.mono-num');

  masterToggle?.addEventListener('change', () => {
    const on = masterToggle.checked;
    setBlockerEnabled(on);
    if (appGrid) {
      appGrid.style.opacity      = on ? '1' : '.4';
      appGrid.style.pointerEvents = on ? '' : 'none';
    }
    if (masterLabel) masterLabel.textContent = on ? 'ON' : 'OFF';
  });

  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      chip.classList.toggle('selected');
      const selected = [...container.querySelectorAll('.blocker-app-chip.selected')]
        .map(c => c.dataset.appId);
      setBlockedApps(selected);
    });
  });
}

/* ─── Show the Lockdown Shield overlay before entering arena ─────── */
export function showLockdownShield(onProceed, onSkip) {
  const blocked  = getBlockedApps();
  const appNames = DISTRACTION_APPS.filter(a => blocked.includes(a.id));
  const android  = isAndroid();

  // Remove any existing shield
  document.getElementById('lockdown-shield')?.remove();

  const shield = document.createElement('div');
  shield.id        = 'lockdown-shield';
  shield.className = 'focus-overlay lockdown-shield-overlay';

  shield.innerHTML = `
    <div class="lockdown-inner">
      <div style="text-align:center;margin-bottom:24px">
        <div style="font-size:48px;margin-bottom:12px">🛡️</div>
        <div class="mono-num" style="font-size:18px;color:var(--blue)">FOCUS SHIELD ACTIVATING</div>
        <p class="muted" style="margin:8px 0 0;max-width:420px">
          Lock down your distractions before entering the study arena.
          Your brain will thank you.
        </p>
      </div>

      ${appNames.length ? `
        <div class="lockdown-app-list">
          <div class="mono-num" style="font-size:10px;color:var(--ink-soft);margin-bottom:10px">
            APPS TO BLOCK:
          </div>
          <div style="display:flex;flex-wrap:wrap;gap:8px;justify-content:center">
            ${appNames.map(a => `
              <div class="lockdown-chip">
                <span>${a.emoji}</span>
                <span>${a.name}</span>
              </div>`).join('')}
          </div>
        </div>` : `
        <div class="panel" style="text-align:center;padding:18px;margin-bottom:20px">
          <p class="muted" style="margin:0">No apps selected to block.<br>
          <a href="#" id="lockdown-no-apps-link" style="color:var(--blue)">Add apps in Arena Setup ↗</a></p>
        </div>`}

      ${android ? `
        <div class="panel" style="background:var(--paper-2);border:3px solid var(--teal);padding:16px;margin:20px 0">
          <div class="mono-num" style="font-size:11px;color:var(--teal);margin-bottom:8px">
            📱 ANDROID FOCUS MODE DETECTED
          </div>
          <p class="muted tiny" style="margin:0 0 12px">
            Tap below to open your phone's built-in <b>Focus Mode / Digital Wellbeing</b> settings.
            Enable it, then come back and tap <b>"I'VE LOCKED DOWN"</b>.
          </p>
          <button class="btn primary block" id="btn-open-focus-mode">
            ⚡ OPEN FOCUS MODE / DIGITAL WELLBEING
          </button>
        </div>` : `
        <div class="panel" style="background:var(--paper-2);border:3px dashed var(--teal);padding:16px;margin:20px 0">
          <div class="mono-num" style="font-size:11px;color:var(--teal);margin-bottom:8px">
            💻 DESKTOP / BROWSER MODE
          </div>
          <p class="muted tiny" style="margin:0">
            Close or minimize distracting tabs now. Consider using browser extensions like
            <b>Cold Turkey</b> or <b>Freedom</b> for automated blocking.
            When you're ready, proceed below.
          </p>
        </div>`}

      <div class="row" style="justify-content:center;gap:12px;margin-top:8px">
        <button class="btn primary" id="btn-lockdown-proceed" style="font-size:13px;padding:14px 24px">
          ✅ ${android ? "I'VE LOCKED DOWN — ENTER ARENA" : 'ALL CLEAR — ENTER ARENA'}
        </button>
        <button class="btn ghost sm" id="btn-lockdown-skip">
          SKIP BLOCKING
        </button>
      </div>
    </div>`;

  document.body.appendChild(shield);

  shield.querySelector('#btn-open-focus-mode')?.addEventListener('click', () => {
    triggerAndroidFocusMode();
  });

  shield.querySelector('#btn-lockdown-proceed')?.addEventListener('click', () => {
    shield.remove();
    onProceed();
  });

  shield.querySelector('#btn-lockdown-skip')?.addEventListener('click', () => {
    shield.remove();
    onSkip();
  });

  shield.querySelector('#lockdown-no-apps-link')?.addEventListener('click', (e) => {
    e.preventDefault();
    shield.remove();
    onSkip();
  });
}
