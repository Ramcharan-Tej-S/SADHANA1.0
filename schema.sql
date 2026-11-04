-- schema.sql — ExamFlow AI Database Schema

CREATE TABLE IF NOT EXISTS subjects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    code        TEXT    DEFAULT '',
    credits     INTEGER DEFAULT 3,
    semester    INTEGER DEFAULT 1,
    self_rating REAL    DEFAULT 5.0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS topics (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id  INTEGER NOT NULL REFERENCES subjects(id),
    unit_name   TEXT    DEFAULT '',
    topic_name  TEXT    NOT NULL,
    description TEXT    DEFAULT '',
    estimated_hours REAL DEFAULT 2.0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS difficulty_scores (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id    INTEGER NOT NULL REFERENCES topics(id),
    level       TEXT    CHECK(level IN ('easy','medium','hard')) DEFAULT 'medium',
    score       REAL    DEFAULT 5.0,
    confidence  REAL    DEFAULT 0.5,
    reasoning   TEXT    DEFAULT '',
    assessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS exam_schedule (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id  INTEGER NOT NULL REFERENCES subjects(id),
    exam_date   DATE    NOT NULL,
    exam_time   TEXT    DEFAULT '09:00',
    duration_min INTEGER DEFAULT 180,
    exam_type   TEXT    DEFAULT 'final',
    is_completed INTEGER DEFAULT 0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS availability (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    day_of_week TEXT    NOT NULL,
    start_time  TEXT    NOT NULL,
    end_time    TEXT    NOT NULL,
    is_peak     INTEGER DEFAULT 0,
    energy_level TEXT   DEFAULT 'medium',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS test_scores (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id  INTEGER NOT NULL REFERENCES subjects(id),
    test_type   TEXT    DEFAULT 'cie',
    score       REAL    NOT NULL,
    max_score   REAL    DEFAULT 100.0,
    test_date   DATE    DEFAULT CURRENT_DATE,
    notes       TEXT    DEFAULT '',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS study_sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id  INTEGER REFERENCES subjects(id),
    topic_id    INTEGER REFERENCES topics(id),
    session_date DATE   NOT NULL,
    start_time  TEXT    NOT NULL,
    duration_min INTEGER DEFAULT 60,
    priority    TEXT    DEFAULT 'medium',
    status      TEXT    DEFAULT 'planned',
    session_type TEXT   DEFAULT 'study',
    study_technique TEXT DEFAULT '',
    notes       TEXT    DEFAULT '',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS performance_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id      INTEGER NOT NULL REFERENCES subjects(id),
    readiness_score REAL    DEFAULT 0.0,
    predicted_score REAL    DEFAULT 0.0,
    actual_score    REAL    DEFAULT NULL,
    coverage_pct    REAL    DEFAULT 0.0,
    reasoning       TEXT    DEFAULT '',
    logged_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS uploaded_files (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    filename    TEXT    NOT NULL,
    file_type   TEXT    DEFAULT 'syllabus',
    file_path   TEXT    NOT NULL,
    subject_id  INTEGER REFERENCES subjects(id),
    processed   INTEGER DEFAULT 0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS study_notes (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    subject_id     INTEGER NOT NULL REFERENCES subjects(id),
    filename       TEXT    NOT NULL,
    file_type      TEXT    DEFAULT 'notes',
    title          TEXT    DEFAULT '',
    summary        TEXT    DEFAULT '',
    extracted_text TEXT    DEFAULT '',
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE IF NOT EXISTS routine_logs (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    log_date           DATE    NOT NULL UNIQUE,
    energy_level       TEXT    DEFAULT 'normal',
    is_low_energy      INTEGER DEFAULT 0,
    focus_minutes      INTEGER DEFAULT 0,
    sessions_completed INTEGER DEFAULT 0,
    notes              TEXT    DEFAULT '',
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
