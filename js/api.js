// api.js — thin fetch wrapper around the FastAPI backend.

async function request(method, path, body, isForm = false) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    if (isForm) {
      opts.body = body; // FormData sets its own content-type boundary
    } else {
      opts.headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(body);
    }
  }
  const res = await fetch(path, opts);
  const text = await res.text();
  let data = null;
  try { data = text ? JSON.parse(text) : null; } catch { data = { error: text }; }
  if (!res.ok) {
    const msg = (data && (data.error || data.detail)) || `Request failed (${res.status})`;
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
  }
  return data;
}

export const api = {
  health:        ()            => request('GET', '/api/health'),
  stats:         ()            => request('GET', '/api/stats'),
  seed:          ()            => request('POST', '/api/seed'),

  subjects:      ()            => request('GET', '/api/subjects'),
  addSubject:    (b)           => request('POST', '/api/subjects', b),
  deleteSubject: (id)          => request('DELETE', `/api/subjects/${id}`),

  topics:        ()            => request('GET', '/api/topics'),
  subjectTopics: (id)          => request('GET', `/api/subjects/${id}/topics`),
  addTopic:      (b)           => request('POST', '/api/topics', b),
  difficulties:  ()            => request('GET', '/api/difficulties'),
  assess:        (subject_id)  => request('POST', '/api/agent/assess-difficulty', { subject_id }),

  files:         ()            => request('GET', '/api/files'),
  upload:        (fd)          => request('POST', '/api/upload', fd, true),
  subjectNotes:  (id)          => request('GET', `/api/subjects/${id}/notes`),

  exams:         (upcoming)    => request('GET', `/api/exams${upcoming ? '?upcoming=true' : ''}`),
  saveExam:      (b)           => request('POST', '/api/exams', b),
  completeExam:  (id)          => request('POST', `/api/exams/${id}/complete`),
  deleteExam:    (id)          => request('DELETE', `/api/exams/${id}`),
  purgeExams:    ()            => request('POST', '/api/exams/purge'),

  availability:  ()            => request('GET', '/api/availability'),
  saveAvailability: (rows)     => request('PUT', '/api/availability', rows),

  scores:        ()            => request('GET', '/api/scores'),
  addScore:      (b)           => request('POST', '/api/scores', b),
  analyzePerformance: ()       => request('POST', '/api/agent/analyze-performance'),
  latestPerformance:  ()       => request('GET', '/api/performance/latest'),
  subjectPerformance: (id)     => request('GET', `/api/subjects/${id}/performance`),

  sessions:      ()            => request('GET', '/api/sessions'),
  setSessionStatus: (id, status) => request('POST', `/api/sessions/${id}/status`, { status }),
  clearSessions: ()            => request('DELETE', '/api/sessions'),
  generatePlan:  ()            => request('POST', '/api/agent/generate-plan'),
  recalculatePlan: ()          => request('POST', '/api/agent/recalculate-plan'),
  predictReadiness: ()         => request('POST', '/api/agent/predict-readiness'),

  insights:      ()            => request('POST', '/api/agent/insights'),

  compressTopic: (subject_name, topic_name, notes = '') =>
    request('POST', '/api/tutor/compress', { subject_name, topic_name, notes }),
  askTutor:      (subject_name, topic_name, question) =>
    request('POST', '/api/tutor/ask', { subject_name, topic_name, question }),

  todayRoutine:  ()            => request('GET', '/api/routine/today'),
  setEnergyMode: (is_low_energy, energy_level = 'low') =>
    request('POST', '/api/routine/energy', { is_low_energy, energy_level }),
  logFocusTime:  (duration_min) =>
    request('POST', '/api/routine/focus', { duration_min }),
  adaptRoutine:  (date_str)    =>
    request('POST', '/api/routine/adapt', { date_str }),
  routineStats:  ()            => request('GET', '/api/routine/stats'),
};
