# backend/main.py — ExamFlow AI REST API + static frontend host
"""
FastAPI backend for ExamFlow AI.

Reuses the existing `db/` layer and `agents/` package unchanged; this module only
exposes them over HTTP and serves the arcade frontend from `frontend/`.
"""
import hashlib
import json
import os
import sys
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import (
    BASE_DIR,
    CACHE_DIR,
    ENABLE_PARSE_CACHE,
    FOCUS_SLOTS,
    LLM_MODEL,
    OPENROUTER_API_KEY,
    UPLOAD_DIR,
    USE_VISION,
)
from db import database as dbx

FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

app = FastAPI(title="SADHANA", version="2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def _startup():
    dbx.init_db()


# ─── Helpers ──────────────────────────────────────────────────────────
def agent_call(fn, *args, **kwargs):
    """Run an agent function, converting failures into a clean 502 payload."""
    try:
        return fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001 — surfaced verbatim to the UI
        detail = str(exc) or exc.__class__.__name__
        if not OPENROUTER_API_KEY:
            detail = "OPENROUTER_API_KEY is not set — the AI agents cannot run. " + detail
        raise HTTPException(status_code=502, detail=detail) from exc


def difficulty_lookup() -> dict:
    return {
        d["topic_name"]: {"level": d["level"], "score": d["score"]}
        for d in dbx.get_all_difficulties()
    }


def topics_by_subject_name(subjects: list) -> dict:
    return {s["name"]: dbx.get_topics_by_subject(s["id"]) for s in subjects}


# ─── Schemas ──────────────────────────────────────────────────────────
class SubjectIn(BaseModel):
    name: str
    code: str = ""
    credits: int = 3
    semester: int = 1
    self_rating: float = 5.0


class TopicIn(BaseModel):
    subject_id: int
    topic_name: str
    unit_name: str = ""
    description: str = ""
    estimated_hours: float = 2.0


class ExamIn(BaseModel):
    subject_id: int
    exam_date: str
    exam_time: str = "09:00"
    duration_min: int = 180
    exam_type: str = "final"


class AvailabilityIn(BaseModel):
    day_of_week: str
    start_time: str
    end_time: str
    is_peak: bool = False
    energy_level: str = "medium"


class ScoreIn(BaseModel):
    subject_id: int
    score: float
    max_score: float = 100.0
    test_type: str = "cie1"
    test_date: Optional[str] = None
    notes: str = ""


class StatusIn(BaseModel):
    status: str = Field(pattern="^(planned|completed|skipped)$")


class SubjectRef(BaseModel):
    subject_id: int


class TutorCompressIn(BaseModel):
    subject_name: str
    topic_name: str
    notes: Optional[str] = ""


class RoutineEnergyIn(BaseModel):
    is_low_energy: bool
    energy_level: str = "low"


class RoutineFocusIn(BaseModel):
    duration_min: int = 15


class RoutineAdaptIn(BaseModel):
    date_str: Optional[str] = None


class TutorAskIn(BaseModel):
    subject_name: str
    topic_name: str
    question: str


# ─── Meta ─────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {
        "ok": True,
        "llm_configured": bool(OPENROUTER_API_KEY),
        "model": LLM_MODEL,
        "vision": USE_VISION,
        "parse_cache": ENABLE_PARSE_CACHE,
        "focus_slots": FOCUS_SLOTS,
    }


@app.get("/api/stats")
def stats():
    s = dbx.get_stats()
    s["files"] = len(dbx.get_uploaded_files())
    return s


@app.post("/api/seed")
def seed():
    from utils.seed_data import seed_all

    subjects, topics, diffs = seed_all()
    return {"subjects": subjects, "topics": topics, "difficulties": diffs}


# ─── Subjects ─────────────────────────────────────────────────────────
@app.get("/api/subjects")
def list_subjects():
    return dbx.get_all_subjects()


@app.post("/api/subjects", status_code=201)
def create_subject(body: SubjectIn):
    if not body.name.strip():
        raise HTTPException(400, "Subject name is required")
    sid = dbx.add_subject(
        body.name.strip(), body.code.strip(), body.credits, body.semester, body.self_rating
    )
    return dbx.get_subject(sid)


@app.delete("/api/subjects/{subject_id}")
def remove_subject(subject_id: int):
    if not dbx.get_subject(subject_id):
        raise HTTPException(404, "Subject not found")
    dbx.delete_subject(subject_id)
    return {"deleted": subject_id}


# ─── Topics & difficulty ──────────────────────────────────────────────
@app.get("/api/topics")
def list_topics():
    return dbx.get_all_topics()


@app.get("/api/subjects/{subject_id}/topics")
def list_subject_topics(subject_id: int):
    topics = dbx.get_topics_by_subject(subject_id)
    for t in topics:
        t["difficulty"] = dbx.get_difficulty_by_topic(t["id"])
    return topics


@app.post("/api/topics", status_code=201)
def create_topic(body: TopicIn):
    if not body.topic_name.strip():
        raise HTTPException(400, "Topic name is required")
    tid = dbx.add_topic(
        body.subject_id,
        body.topic_name.strip(),
        body.unit_name.strip(),
        body.description,
        body.estimated_hours,
    )
    return {"id": tid}


@app.get("/api/difficulties")
def list_difficulties():
    return dbx.get_all_difficulties()


@app.post("/api/agent/assess-difficulty")
def agent_assess_difficulty(body: SubjectRef):
    """LLM-as-Judge 3-pass difficulty scoring for every topic in a subject."""
    from agents.difficulty_assessor_agent import assess_difficulty, save_difficulty_results

    subject = dbx.get_subject(body.subject_id)
    if not subject:
        raise HTTPException(404, "Subject not found")
    topics = dbx.get_topics_by_subject(body.subject_id)
    if not topics:
        raise HTTPException(400, "This subject has no topics to assess yet")

    payload = [
        {
            "topic_id": t["id"],
            "topic_name": t["topic_name"],
            "unit_name": t.get("unit_name", ""),
            "description": t.get("description", ""),
        }
        for t in topics
    ]
    results = agent_call(assess_difficulty, payload, subject["name"])
    topic_map = {t["topic_name"]: t["id"] for t in topics}
    saved = save_difficulty_results(results, topic_map, topic_list=topics)
    return {"saved": saved, "results": results}


# ─── Uploads ──────────────────────────────────────────────────────────
@app.get("/api/files")
def list_files():
    return dbx.get_uploaded_files()


def _is_valid_parse(data: dict, kind: str) -> bool:
    if not isinstance(data, dict):
        return False
    if kind == "syllabus":
        units = data.get("units")
        if not units or not isinstance(units, list) or len(units) == 0:
            return False
    elif kind == "question_paper":
        topics = data.get("important_topics")
        if not topics or not isinstance(topics, list) or len(topics) == 0:
            return False
    reasoning = str(data.get("reasoning", ""))
    if "Failed to parse" in reasoning or "Error:" in reasoning:
        return False
    return True


def _cache_load(digest: str, kind: str):
    """Return a previously parsed result for identical file bytes, if any."""
    if not ENABLE_PARSE_CACHE:
        return None
    path = os.path.join(CACHE_DIR, f"{kind}-{digest}.json")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            if not _is_valid_parse(data, kind):
                return None
            return data
    except (OSError, ValueError):
        return None


def _cache_store(digest: str, kind: str, data: dict):
    if not ENABLE_PARSE_CACHE or not _is_valid_parse(data, kind):
        return
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(os.path.join(CACHE_DIR, f"{kind}-{digest}.json"), "w", encoding="utf-8") as f:
            json.dump(data, f)
    except OSError:
        pass  # caching is an optimisation, never a hard requirement


@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    subject_id: int = Form(...),
    file_type: str = Form("syllabus"),
):
    """Save an uploaded syllabus/question paper and run the parser agent on it.

    Identical file bytes are served from the parse cache, so re-uploading the
    same document is instant instead of a fresh OCR + LLM round trip.
    """
    from agents.syllabus_parser_agent import parse_document, save_parsed_syllabus

    subject = dbx.get_subject(subject_id)
    if not subject:
        raise HTTPException(404, "Subject not found")

    raw = await file.read()
    if not raw:
        raise HTTPException(400, "The uploaded file is empty")
    digest = hashlib.sha256(raw).hexdigest()[:32]

    safe_name = os.path.basename(file.filename or "upload.bin")
    dest = os.path.join(UPLOAD_DIR, safe_name)
    with open(dest, "wb") as out:
        out.write(raw)

    file_id = dbx.add_uploaded_file(safe_name, dest, file_type, subject_id)

    parsed = _cache_load(digest, file_type)
    cached = parsed is not None
    if not cached:
        try:
            parsed = agent_call(parse_document, dest, subject["name"], file_type)
        except HTTPException:
            raise
        except ValueError as exc:
            raise HTTPException(422, f"{safe_name}: {exc}") from exc
        _cache_store(digest, file_type, parsed)

    meta = {"filename": safe_name, "cached": cached, "route": parsed.get("_route", "cache")}

    if file_type == "syllabus":
        _, topic_count = save_parsed_syllabus(parsed, subject_id)
        dbx.mark_file_processed(file_id)
        return {
            **meta,
            "kind": "syllabus",
            "topic_count": topic_count,
            "reasoning": parsed.get("reasoning", ""),
            "units": parsed.get("units", []),
        }

    if file_type in ("notes", "handwritten", "lecture_notes"):
        dbx.add_study_note(
            subject_id=subject_id,
            filename=safe_name,
            file_type=file_type,
            title=parsed.get("title", safe_name),
            summary=parsed.get("summary", ""),
            extracted_text=parsed.get("extracted_text", ""),
        )
        dbx.mark_file_processed(file_id)
        return {
            **meta,
            "kind": "notes",
            "title": parsed.get("title", safe_name),
            "summary": parsed.get("summary", ""),
            "concepts": parsed.get("concepts_covered", []),
        }

    dbx.mark_file_processed(file_id)
    return {**meta, "kind": "question_paper", "important_topics": parsed.get("important_topics", [])}


# ─── Exams ────────────────────────────────────────────────────────────
@app.get("/api/exams")
def list_exams(upcoming: bool = False):
    return dbx.get_upcoming_exams() if upcoming else dbx.get_all_exams()


@app.post("/api/exams")
def upsert_exam(body: ExamIn):
    if not dbx.get_subject(body.subject_id):
        raise HTTPException(404, "Subject not found")
    try:
        datetime.strptime(body.exam_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(400, "exam_date must be YYYY-MM-DD")
    eid = dbx.add_exam(
        body.subject_id, body.exam_date, body.exam_time, body.duration_min, body.exam_type
    )
    return {"id": eid}


@app.post("/api/exams/{exam_id}/complete")
def complete_exam(exam_id: int):
    dbx.mark_exam_completed(exam_id)
    return {"completed": exam_id}


@app.delete("/api/exams/{exam_id}")
def remove_exam(exam_id: int):
    dbx.delete_exam(exam_id)
    return {"deleted": exam_id}


@app.post("/api/exams/purge")
def purge_exams():
    before = len(dbx.get_all_exams())
    dbx.delete_past_exams(date.today().strftime("%Y-%m-%d"))
    return {"removed": before - len(dbx.get_all_exams())}


# ─── Availability ─────────────────────────────────────────────────────
@app.get("/api/availability")
def list_availability():
    return dbx.get_all_availability()


@app.put("/api/availability")
def replace_availability(body: List[AvailabilityIn]):
    """Replace the whole weekly availability grid in one shot."""
    dbx.clear_availability()
    for slot in body:
        dbx.add_availability(
            slot.day_of_week,
            slot.start_time,
            slot.end_time,
            1 if slot.is_peak else 0,
            slot.energy_level,
        )
    return {"saved": len(body)}


# ─── Scores & performance ─────────────────────────────────────────────
@app.get("/api/scores")
def list_scores():
    return dbx.get_all_scores()


@app.post("/api/scores", status_code=201)
def create_score(body: ScoreIn):
    if not dbx.get_subject(body.subject_id):
        raise HTTPException(404, "Subject not found")
    if body.score <= 0 or body.max_score <= 0:
        raise HTTPException(400, "Score and max score must be greater than zero")
    sid = dbx.add_test_score(
        body.subject_id, body.score, body.max_score, body.test_type, body.test_date, body.notes
    )
    return {"id": sid}


@app.post("/api/agent/analyze-performance")
def agent_analyze_performance():
    from agents.performance_analyzer_agent import (
        analyze_performance,
        update_priorities_from_analysis,
    )

    scores = dbx.get_all_scores()
    if not scores:
        raise HTTPException(400, "No test scores recorded yet")
    subjects = dbx.get_all_subjects()
    analysis = agent_call(analyze_performance, scores, subjects, difficulty_lookup())
    update_priorities_from_analysis(analysis, {s["name"]: s["id"] for s in subjects})
    return analysis


@app.get("/api/performance/latest")
def latest_performance():
    return dbx.get_latest_performance()


@app.get("/api/subjects/{subject_id}/performance")
def subject_performance(subject_id: int):
    return dbx.get_performance_history(subject_id)


# ─── Study sessions & the optimizer ───────────────────────────────────
@app.get("/api/sessions")
def list_sessions():
    return dbx.get_all_sessions()


@app.post("/api/sessions/{session_id}/status")
def set_session_status(session_id: int, body: StatusIn):
    dbx.update_session_status(session_id, body.status)
    return {"id": session_id, "status": body.status}


@app.delete("/api/sessions")
def wipe_sessions():
    dbx.clear_sessions()
    return {"cleared": True}


@app.post("/api/agent/generate-plan")
def agent_generate_plan():
    from agents.schedule_optimizer_agent import generate_study_plan, save_study_plan

    subjects = dbx.get_all_subjects()
    if not subjects:
        raise HTTPException(400, "Add at least one subject first")
    availability = dbx.get_all_availability()
    if not availability:
        raise HTTPException(400, "Set your weekly availability first")
    exams = dbx.get_upcoming_exams()
    if not exams:
        raise HTTPException(400, "Schedule at least one upcoming exam first")

    existing_scores = {}
    for sc in dbx.get_all_scores():
        existing_scores.setdefault(
            sc["subject_name"], {"score": sc["score"], "max_score": sc["max_score"]}
        )

    plan = agent_call(
        generate_study_plan,
        subjects=subjects,
        topics_by_subject=topics_by_subject_name(subjects),
        difficulties=difficulty_lookup(),
        exams=exams,
        availability=availability,
        existing_scores=existing_scores,
    )

    topic_map = {}
    for s in subjects:
        for t in dbx.get_topics_by_subject(s["id"]):
            topic_map[t["topic_name"]] = t["id"]

    saved = save_study_plan(plan, {s["name"]: s["id"] for s in subjects}, topic_map)
    return {
        "saved": saved,
        "reasoning": plan.get("reasoning", ""),
        "strategy": plan.get("plan_summary", ""),
    }


@app.post("/api/agent/recalculate-plan")
def agent_recalculate_plan():
    """Redistribute skipped sessions into the remaining free slots.

    Keeps the schedule honest after real life happens — the skipped rows stay
    as history, and the topics they covered get re-booked.
    """
    from agents.schedule_optimizer_agent import recalculate_after_skip

    sessions = dbx.get_all_sessions()
    skipped = [s for s in sessions if s.get("status") == "skipped"]
    if not skipped:
        raise HTTPException(400, "Nothing to redistribute — no sessions are marked skipped")

    availability = dbx.get_all_availability()
    if not availability:
        raise HTTPException(400, "Set your weekly availability first")

    remaining = [s for s in sessions if s.get("status") == "planned"]
    taken = {(s.get("session_date"), s.get("start_time")) for s in sessions}

    def slim(rows):
        return [
            {
                "subject": r.get("subject_name"),
                "topic": r.get("topic_name"),
                "date": r.get("session_date"),
                "start_time": r.get("start_time"),
                "duration_min": r.get("duration_min", 60),
                "priority": r.get("priority", "medium"),
            }
            for r in rows
        ]

    adjusted = agent_call(recalculate_after_skip, slim(skipped), slim(remaining), availability)

    subject_map = {s["name"]: s["id"] for s in dbx.get_all_subjects()}
    topic_map = {t["topic_name"]: t["id"] for t in dbx.get_all_topics()}

    def book(subject, topic, date_str, start_time, priority, technique="", notes=""):
        sid = subject_map.get(subject)
        if not sid or (date_str, start_time) in taken:
            return False
        taken.add((date_str, start_time))
        dbx.add_study_session(
            subject_id=sid,
            topic_id=topic_map.get(topic),
            session_date=date_str,
            start_time=start_time,
            duration_min=60,
            priority=priority,
            status="planned",
            session_type="study",
            study_technique=technique or "Active Recall & Problem Solving",
            notes=notes or f"Catch-up study session for {topic}",
        )
        return True

    placed = []
    for a in adjusted:
        if book(
            a.get("subject"),
            a.get("topic"),
            a.get("date", ""),
            a.get("start_time", "09:00"),
            a.get("priority", "high"),
            a.get("study_technique", ""),
            a.get("notes", ""),
        ):
            placed.append(a.get("topic"))

    # The model often proposes slots that are already booked on a full schedule.
    # Fall back to the first genuinely free slots in the availability grid.
    unplaced = [s for s in skipped if s.get("topic_name") not in placed]
    if unplaced:
        for s in unplaced:
            for date_str, start_time in _free_slots(availability, taken):
                if book(s.get("subject_name"), s.get("topic_name"), date_str, start_time, "high"):
                    placed.append(s.get("topic_name"))
                    break

    return {
        "skipped": len(skipped),
        "proposed": len(adjusted),
        "added": len(placed),
        "unplaced": len(skipped) - len(placed),
    }


def _free_slots(availability, taken, horizon_days=30):
    """Yield (date, start_time) pairs inside the availability grid that have
    no session booked, walking forward from tomorrow."""
    from agents.schedule_optimizer_agent import _generate_time_slots

    by_day = _generate_time_slots(availability)
    today = date.today()
    for offset in range(1, horizon_days + 1):
        d = today + timedelta(days=offset)
        date_str = d.strftime("%Y-%m-%d")
        for slot in by_day.get(d.strftime("%A"), []):
            key = (date_str, slot["start_time"])
            if key not in taken:
                yield key


@app.post("/api/agent/predict-readiness")
def agent_predict_readiness():
    from agents.readiness_predictor_agent import predict_all_subjects

    subjects = dbx.get_all_subjects()
    if not subjects:
        raise HTTPException(400, "Add at least one subject first")

    sessions = dbx.get_all_sessions()
    sessions_by_subject = {
        s["name"]: [x for x in sessions if x.get("subject_name") == s["name"]] for s in subjects
    }
    scores_by_subject = {}
    for sc in dbx.get_all_scores():
        scores_by_subject.setdefault(sc["subject_name"], []).append(sc)
    exam_dates = {e["subject_name"]: e["exam_date"] for e in dbx.get_upcoming_exams()}

    predictions = agent_call(
        predict_all_subjects,
        subjects,
        topics_by_subject_name(subjects),
        difficulty_lookup(),
        sessions_by_subject,
        scores_by_subject,
        exam_dates,
    )

    # Log each prediction so the feedback loop has a trend to chart.
    by_name = {s["name"]: s["id"] for s in subjects}
    for p in predictions:
        sid = by_name.get(p.get("subject"))
        if sid:
            dbx.add_performance_log(
                subject_id=sid,
                readiness_score=p.get("readiness_score", 0.0),
                predicted_score=p.get("readiness_score", 0.0),
                coverage_pct=p.get("coverage_pct", 0.0),
                reasoning=p.get("reasoning", ""),
            )
    return predictions


# ─── Feedback loop ────────────────────────────────────────────────────
@app.post("/api/agent/insights")
def agent_insights():
    from agents.feedback_loop_agent import (
        analyze_prediction_accuracy,
        generate_improvement_suggestions,
    )

    history = []
    for s in dbx.get_all_subjects():
        for h in dbx.get_performance_history(s["id"]):
            h["subject_name"] = s["name"]
            history.append(h)

    accuracy = agent_call(analyze_prediction_accuracy, history)
    suggestions = agent_call(generate_improvement_suggestions, history, dbx.get_all_sessions())
    return {"accuracy": accuracy, "suggestions": suggestions}


# ─── ADHD Adaptive Tutor ──────────────────────────────────────────────
@app.post("/api/tutor/compress")
def tutor_compress(body: TutorCompressIn):
    from agents.adaptive_tutor_agent import compress_study_material
    uploaded_notes = dbx.get_relevant_notes_for_topic(body.subject_name, body.topic_name)
    return agent_call(compress_study_material, body.subject_name, body.topic_name, body.notes or "", uploaded_notes)


@app.get("/api/subjects/{subject_id}/notes")
def list_subject_notes(subject_id: int):
    return dbx.get_study_notes_by_subject(subject_id)


@app.post("/api/tutor/ask")
def tutor_ask(body: TutorAskIn):
    from agents.adaptive_tutor_agent import ask_tutor
    return agent_call(ask_tutor, body.subject_name, body.topic_name, body.question)


# ─── ADHD Routine Tracker & Low-Energy Day Adaptation ─────────────────
@app.get("/api/routine/today")
def get_today_routine():
    return dbx.get_or_create_today_routine()


@app.post("/api/routine/energy")
def set_energy_mode(body: RoutineEnergyIn):
    return dbx.set_low_energy_day(body.is_low_energy, body.energy_level)


@app.post("/api/routine/focus")
def record_focus_time(body: RoutineFocusIn):
    return dbx.log_focus_session(body.duration_min)


@app.post("/api/routine/adapt")
def adapt_schedule(body: RoutineAdaptIn):
    return dbx.adapt_schedule_for_low_energy(body.date_str)


@app.get("/api/routine/stats")
def get_routine_statistics():
    return dbx.get_routine_stats()


# ─── Frontend hosting ─────────────────────────────────────────────────
@app.exception_handler(HTTPException)
async def http_error(_request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


if os.path.isdir(FRONTEND_DIR):
    app.mount("/css", StaticFiles(directory=os.path.join(FRONTEND_DIR, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(FRONTEND_DIR, "js")), name="js")

    @app.get("/")
    def index():
        return FileResponse(
            os.path.join(FRONTEND_DIR, "index.html"),
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"}
        )
