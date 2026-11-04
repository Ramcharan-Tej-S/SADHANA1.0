// audio.js — ADHD Sensory Audio Engine for SADHANA
// Generates ambient sound using only the Web Audio API — no external assets.
// Modes: Brown Noise (deep focus), Rain (texture), Binaural Pulse (40 Hz beat).
// Persists mode + volume in localStorage so settings survive page reloads.

const ACtor = window.AudioContext || window.webkitAudioContext;

let ctx = null;
let masterGain = null;
let activeSource = null;   // the node currently connected
let activeExtra = null;    // extra nodes to stop (oscillators etc.)

export const AudioMode = Object.freeze({
  OFF:      'off',
  BROWN:    'brown',
  RAIN:     'rain',
  BINAURAL: 'binaural',
});

const STORAGE_MODE = 'sadhana:audioMode';
const STORAGE_VOL  = 'sadhana:audioVol';

/* ─── lazy-init AudioContext (must be after a user gesture) ──────── */
function ensureCtx() {
  if (!ctx) ctx = new ACtor();
  if (ctx.state === 'suspended') ctx.resume();
  if (!masterGain) {
    masterGain = ctx.createGain();
    masterGain.gain.value = _savedVolume();
    masterGain.connect(ctx.destination);
  }
}

function _savedVolume() {
  const v = parseFloat(localStorage.getItem(STORAGE_VOL));
  return Number.isFinite(v) ? Math.max(0, Math.min(1, v)) : 0.25;
}

/* ─── generators ─────────────────────────────────────────────────── */

/** Brown noise via AudioWorklet-fallback (ScriptProcessor). */
function makeBrown() {
  const bufSize = 4096;
  const proc = ctx.createScriptProcessor(bufSize, 1, 1);
  let last = 0;
  proc.onaudioprocess = (e) => {
    const out = e.outputBuffer.getChannelData(0);
    for (let i = 0; i < bufSize; i++) {
      const white = Math.random() * 2 - 1;
      out[i] = (last + 0.02 * white) / 1.02;
      last = out[i];
      out[i] *= 3.5;
    }
  };
  return { node: proc, extras: [] };
}

/** Rain-like low-pass filtered white noise. */
function makeRain() {
  const buf = ctx.createBuffer(2, ctx.sampleRate * 2, ctx.sampleRate);
  for (let ch = 0; ch < 2; ch++) {
    const data = buf.getChannelData(ch);
    for (let i = 0; i < data.length; i++) data[i] = Math.random() * 2 - 1;
  }
  const src = ctx.createBufferSource();
  src.buffer = buf;
  src.loop = true;

  const lp = ctx.createBiquadFilter();
  lp.type = 'lowpass';
  lp.frequency.value = 7200;

  const hp = ctx.createBiquadFilter();
  hp.type = 'highpass';
  hp.frequency.value = 400;

  src.connect(lp);
  lp.connect(hp);
  src.start();
  return { node: hp, extras: [src] };
}

/** 40 Hz binaural beat (200 Hz left, 240 Hz right). */
function makeBinaural() {
  const left  = ctx.createOscillator();
  const right = ctx.createOscillator();
  left.type = right.type = 'sine';
  left.frequency.value  = 200;
  right.frequency.value = 240;

  const merger = ctx.createChannelMerger(2);
  const leftGain  = ctx.createGain();
  const rightGain = ctx.createGain();
  leftGain.gain.value  = 0.5;
  rightGain.gain.value = 0.5;

  left.connect(leftGain);
  leftGain.connect(merger, 0, 0);
  right.connect(rightGain);
  rightGain.connect(merger, 0, 1);

  left.start();
  right.start();
  return { node: merger, extras: [left, right] };
}

/* ─── teardown helper ────────────────────────────────────────────── */
function killActive() {
  if (activeSource) {
    try { activeSource.disconnect(); } catch { /* ok */ }
    activeSource = null;
  }
  if (activeExtra) {
    activeExtra.forEach((n) => { try { n.stop?.(); n.disconnect?.(); } catch { /* ok */ } });
    activeExtra = null;
  }
}

/* ─── public controller ──────────────────────────────────────────── */
export const audioController = {
  /** Switch to a mode (off / brown / rain / binaural). */
  setMode(mode) {
    ensureCtx();
    killActive();

    if (mode === AudioMode.OFF || !mode) {
      localStorage.setItem(STORAGE_MODE, AudioMode.OFF);
      return;
    }

    let gen;
    switch (mode) {
      case AudioMode.BROWN:    gen = makeBrown();    break;
      case AudioMode.RAIN:     gen = makeRain();     break;
      case AudioMode.BINAURAL: gen = makeBinaural(); break;
      default:
        console.warn('[audio] unknown mode:', mode);
        return;
    }

    gen.node.connect(masterGain);
    activeSource = gen.node;
    activeExtra  = gen.extras;
    localStorage.setItem(STORAGE_MODE, mode);
  },

  /** Get the current stored mode. */
  getMode() {
    return localStorage.getItem(STORAGE_MODE) || AudioMode.OFF;
  },

  /** Toggle between the last active mode and OFF. */
  toggle() {
    const cur = this.getMode();
    this.setMode(cur === AudioMode.OFF ? AudioMode.BROWN : AudioMode.OFF);
    return this.getMode();
  },

  /** Set volume (0–1). */
  setVolume(v) {
    ensureCtx();
    const clamped = Math.max(0, Math.min(1, v));
    masterGain.gain.setTargetAtTime(clamped, ctx.currentTime, 0.05);
    localStorage.setItem(STORAGE_VOL, clamped);
  },

  /** Get the current stored volume. */
  getVolume() {
    return _savedVolume();
  },

  /** Restore the last-saved mode + volume (call after a user gesture). */
  restore() {
    const mode = this.getMode();
    if (mode !== AudioMode.OFF) this.setMode(mode);
  },

  /** Completely tear down — e.g. when leaving the arena. */
  stop() {
    killActive();
  },
};
