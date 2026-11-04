# agents/schedule_optimizer_agent.py — Timetable Optimization
"""
Pattern: Constraint-aware Cognitive AI planning
Generates optimized, Claude-grade study schedules respecting exam dates, availability,
topic difficulty, and healthy human rhythms (Breakfast, Lunch, Refreshments, Dinner).
Includes robust post-processing validation and fallback scheduling.
"""
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_llm, extract_json_safe


# ─── Constants ──────────────────────────────────────────────────────
STUDY_SESSION_MIN = 90   # Standard study block duration: 1 hr 30 mins
REFRESHMENT_BREAK_MIN = 15  # 15 min refreshment break between sessions

# Standard meal & refreshment intervals (in minutes from midnight)
# Breakfast: 08:00 - 08:45 (45 mins)
# Lunch: 12:30 - 13:15 (45 mins)
# Evening Refreshment / Tea: 16:30 - 16:45 (15 mins)
# Dinner: 20:00 - 20:45 (45 mins)
MEAL_WINDOWS = [
    {"name": "Breakfast Break", "type": "break", "start": 8 * 60, "duration": 45, "notes": "Nutritious breakfast & morning coffee/tea to jumpstart focus"},
    {"name": "Lunch Break", "type": "break", "start": 12 * 60 + 30, "duration": 45, "notes": "Wholesome lunch & brain reset away from screens"},
    {"name": "Refreshment Break", "type": "break", "start": 16 * 60 + 30, "duration": 15, "notes": "Snack, hydration, and light stretching to prevent burnout"},
    {"name": "Dinner Break", "type": "break", "start": 20 * 60, "duration": 45, "notes": "Relaxing dinner & evening wind-down"},
]

MAX_OUTPUT_TOKENS = int(os.environ.get("EXAMFLOW_MAX_OUTPUT_TOKENS", "16000"))


def _calc_plan_days(exams: list, today: datetime = None) -> int:
    """Calculate how many days to plan based on the latest exam date.
    Returns days from today to 1 day before the last exam (min 7, max 60, default 14)."""
    if today is None:
        today = datetime.now()
    if not exams:
        return 14
    latest = today.date()
    for e in exams:
        try:
            exam_dt = datetime.strptime(e.get("exam_date", ""), "%Y-%m-%d").date()
            if exam_dt > latest:
                latest = exam_dt
        except (ValueError, TypeError):
            continue
    if latest == today.date():
        return 14
    days = (latest - today.date()).days
    return max(7, min(days, 60))


# ─── Availability & Slot Helpers ─────────────────────────────────────
def _build_availability_lookup(availability: list) -> dict:
    """Build a lookup: {day_name: [(start_minutes, end_minutes, is_peak, energy), ...]}"""
    lookup = {}
    for a in availability:
        day = a["day_of_week"]
        try:
            start = datetime.strptime(a["start_time"], "%H:%M")
            end = datetime.strptime(a["end_time"], "%H:%M")
            start_min = start.hour * 60 + start.minute
            end_min = end.hour * 60 + end.minute
            if end_min > start_min:
                lookup.setdefault(day, []).append(
                    (start_min, end_min, a.get("is_peak", 0), a.get("energy_level", "medium"))
                )
        except (ValueError, KeyError):
            continue
    return lookup


def _time_in_window(start_time_str: str, duration_min: int, windows: list) -> bool:
    """Check if a session (start_time + duration) fits within any availability window."""
    try:
        t = datetime.strptime(start_time_str, "%H:%M")
        session_start = t.hour * 60 + t.minute
        session_end = session_start + duration_min
    except (ValueError, TypeError):
        return False
    for win_start, win_end, _, _ in windows:
        if session_start >= win_start and session_end <= win_end:
            return True
    return False


def _generate_day_schedule_slots(windows: list) -> list:
    """
    Generate study slots interleaved with meals and refreshment breaks.
    - Study sessions are prioritized at 90 minutes (1 hr 30 mins) for deep focus blocks.
    - Refreshment breaks between study sessions are 15 minutes.
    - Breakfast, Lunch, and Dinner breaks are 45 minutes.
    """
    all_slots = []
    for win_start, win_end, is_peak, energy in windows:
        curr = win_start
        while curr < win_end:
            next_meal = None
            for meal in MEAL_WINDOWS:
                m_start = meal["start"]
                m_dur = meal["duration"]
                m_end = m_start + m_dur
                if m_start <= curr < m_end and curr < win_end:
                    next_meal = (meal, 0)
                    break
                elif curr < m_start and m_start < win_end:
                    if next_meal is None or m_start < next_meal[0]["start"]:
                        next_meal = (meal, m_start - curr)

            if next_meal:
                meal, gap = next_meal
                m_start = meal["start"]
                m_dur = meal["duration"]

                # Inside meal window
                if gap == 0:
                    dur = min(m_start + m_dur - curr, win_end - curr)
                    if dur >= 15:
                        all_slots.append({
                            "type": "break",
                            "name": meal["name"],
                            "start_time": f"{curr // 60:02d}:{curr % 60:02d}",
                            "duration_min": dur,
                            "is_peak": 0,
                            "energy": "low",
                            "notes": meal["notes"],
                        })
                    curr += dur
                    continue

                # Room for full 90-min study session before meal
                if gap >= STUDY_SESSION_MIN:
                    all_slots.append({
                        "type": "study",
                        "start_time": f"{curr // 60:02d}:{curr % 60:02d}",
                        "duration_min": STUDY_SESSION_MIN,
                        "is_peak": is_peak,
                        "energy": energy,
                    })
                    curr += STUDY_SESSION_MIN
                    # Refreshment break after study session if room before meal
                    if (m_start - curr) >= (REFRESHMENT_BREAK_MIN + 30):
                        all_slots.append({
                            "type": "break",
                            "name": "Refreshment Break",
                            "start_time": f"{curr // 60:02d}:{curr % 60:02d}",
                            "duration_min": REFRESHMENT_BREAK_MIN,
                            "is_peak": 0,
                            "energy": "low",
                            "notes": "Short 15-min refreshment: hydrate, stretch, and relax eyes",
                        })
                        curr += REFRESHMENT_BREAK_MIN
                    elif curr < m_start and (m_start - curr) < 45:
                        rem_break = min(REFRESHMENT_BREAK_MIN, m_start - curr)
                        if rem_break >= 15:
                            all_slots.append({
                                "type": "break",
                                "name": "Refreshment Break",
                                "start_time": f"{curr // 60:02d}:{curr % 60:02d}",
                                "duration_min": rem_break,
                                "is_peak": 0,
                                "energy": "low",
                                "notes": "Short refreshment break before meal",
                            })
                        curr = m_start
                    continue

                # Room for a shorter 45-75 min study session before meal
                elif gap >= 45:
                    all_slots.append({
                        "type": "study",
                        "start_time": f"{curr // 60:02d}:{curr % 60:02d}",
                        "duration_min": gap,
                        "is_peak": is_peak,
                        "energy": energy,
                    })
                    curr = m_start
                    continue
                else:
                    # Small gap under 45 mins before meal
                    rem_break = min(REFRESHMENT_BREAK_MIN, m_start - curr)
                    if rem_break >= 15:
                        all_slots.append({
                            "type": "break",
                            "name": "Refreshment Break",
                            "start_time": f"{curr // 60:02d}:{curr % 60:02d}",
                            "duration_min": rem_break,
                            "is_peak": 0,
                            "energy": "low",
                            "notes": "Short refreshment break before meal",
                        })
                    curr = m_start
                    continue

            # No meal interfering: standard study block
            rem = win_end - curr
            if rem >= STUDY_SESSION_MIN:
                all_slots.append({
                    "type": "study",
                    "start_time": f"{curr // 60:02d}:{curr % 60:02d}",
                    "duration_min": STUDY_SESSION_MIN,
                    "is_peak": is_peak,
                    "energy": energy,
                })
                curr += STUDY_SESSION_MIN
                # Insert refreshment break if enough room remains for another block
                if (win_end - curr) >= (REFRESHMENT_BREAK_MIN + 30):
                    all_slots.append({
                        "type": "break",
                        "name": "Refreshment Break",
                        "start_time": f"{curr // 60:02d}:{curr % 60:02d}",
                        "duration_min": REFRESHMENT_BREAK_MIN,
                        "is_peak": 0,
                        "energy": "low",
                        "notes": "Short 15-min refreshment: hydrate, stretch, and relax eyes",
                    })
                    curr += REFRESHMENT_BREAK_MIN
                elif (win_end - curr) < 30:
                    curr = win_end
            elif rem >= 45:
                all_slots.append({
                    "type": "study",
                    "start_time": f"{curr // 60:02d}:{curr % 60:02d}",
                    "duration_min": rem,
                    "is_peak": is_peak,
                    "energy": energy,
                })
                break
            else:
                break

    return all_slots


def _generate_time_slots(availability: list) -> dict:
    """Generate daily time slots (study + meals/refreshment breaks) for each day of the week."""
    lookup = _build_availability_lookup(availability)
    day_slots = {}
    for day, windows in lookup.items():
        day_slots[day] = _generate_day_schedule_slots(windows)
    return day_slots


def _validate_sessions(sessions: list, availability: list) -> list:
    """Post-process LLM output: remove sessions outside availability windows."""
    avail_lookup = _build_availability_lookup(availability)
    valid = []
    for sess in sessions:
        date_str = sess.get("date", "")
        start_time = sess.get("start_time", "")
        duration = sess.get("duration_min", 60)

        if duration > 180:
            duration = 180
            sess["duration_min"] = 180

        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            day_name = dt.strftime("%A")
        except (ValueError, TypeError):
            continue

        windows = avail_lookup.get(day_name, [])
        if not windows:
            continue

        if _time_in_window(start_time, duration, windows):
            valid.append(sess)

    return valid


# ─── Main Planning Engine ───────────────────────────────────────────
def generate_study_plan(subjects: list, topics_by_subject: dict, difficulties: dict,
                        exams: list, availability: list, existing_scores: dict = None) -> dict:
    """
    Generate an intelligent, Claude-grade academic study timetable using OpenRouter.
    Includes:
    - Structured study blocks with active recall & Feynman techniques.
    - Explicit breaks for Breakfast, Lunch, Evening Refreshments, and Dinner.
    - Spaced repetition and difficulty-prioritized time-matching.
    """
    subject_info = []
    for s in subjects:
        name = s["name"]
        exam = next((e for e in exams if e.get("subject_name") == name), None)
        exam_date = exam["exam_date"] if exam else "No exam scheduled"
        topic_list = topics_by_subject.get(name, [])
        topic_details = []
        for t in topic_list:
            diff = difficulties.get(t.get("topic_name", ""), {})
            topic_details.append(
                f"    - {t['topic_name']} [Difficulty: {diff.get('level', 'medium').upper()}, "
                f"Score: {diff.get('score', 5)}/10, Est. hours: {t.get('estimated_hours', 2)}h]"
            )
        score_info = ""
        if existing_scores and name in existing_scores:
            sc = existing_scores[name]
            score_info = f", Recent Test/CIE: {sc['score']}/{sc['max_score']}"

        subject_info.append(
            f"  Subject: {name} (Exam: {exam_date}{score_info}):\n" + "\n".join(topic_details)
        )

    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    num_days = _calc_plan_days(exams, today)
    day_slots = _generate_time_slots(availability)

    allowed_slots_info = []
    for day_offset in range(num_days):
        d = today + timedelta(days=day_offset)
        day_name = d.strftime("%A")
        date_str = d.strftime("%Y-%m-%d")
        slots = day_slots.get(day_name, [])
        if slots:
            slot_strs = []
            for sl in slots:
                stype = sl.get("type", "study")
                sname = f" [{sl.get('name')}]" if stype == "break" else ""
                slot_strs.append(f"{sl['start_time']} ({sl['duration_min']}min {stype}{sname})")
            allowed_slots_info.append(f"  {date_str} ({day_name}): {', '.join(slot_strs)}")
        else:
            allowed_slots_info.append(f"  {date_str} ({day_name}): NOT AVAILABLE")

    expected_slots = sum(
        len(day_slots.get((today + timedelta(days=i)).strftime("%A"), []))
        for i in range(num_days)
    )
    max_tokens = max(5000, min(MAX_OUTPUT_TOKENS, 1200 + 80 * expected_slots))

    llm = get_llm(temperature=0.3, max_tokens=max_tokens, json_mode=True)

    prompt = f"""You are an elite academic tutor and cognitive science strategist (comparable to Claude 3.7 Sonnet).
Your goal is to build an inspiring, hyper-practical, high-retention study timetable.

TODAY'S DATE: {today_str}

ACADEMIC COURSES & SYLLABUS:
{chr(10).join(subject_info)}

MANDATORY TIMETABLE SLOTS (Dates & times available per student's real availability):
{chr(10).join(allowed_slots_info)}

CORE PRINCIPLES TO APPLY:
1. REFRESHMENTS & MEALS:
   - Study sessions can and should be 1 hour 30 minutes (90 minutes) for deep, high-retention focus blocks.
   - Refreshment breaks between study sessions are 15 minutes (short, refreshing hydration & eye rest).
   - Breakfast, Lunch, and Dinner breaks are 45 minutes each.
   - For every slot marked "break" (Breakfast, Lunch, Refreshment Break, Dinner), produce a break session with nourishing advice.
   - For study slots, assign genuine subject topics.
2. COGNITIVE SCIENCE & STUDY TECHNIQUES:
   - Match topic difficulty to student energy: Hard topics with low recent scores go to morning/peak energy slots.
   - Assign a specific high-retention study technique to each study session:
     * "Active Recall & Problem Solving" (for complex derivations, algorithms, proofs)
     * "Feynman Technique & Teaching" (for abstract theoretical frameworks)
     * "Spaced Flashcards & Mind-Mapping" (for definitions, protocols, architectures)
     * "Mock Test / Timed Practice" (for 2-3 days before exam)
3. SPUR ACTIONABLE SESSIONS:
   - In "notes", provide a razor-sharp, 1-2 sentence tactical action item (e.g. "Derive Dijkstra's using min-heap; solve 2 textbook graph problems").
4. RESPECT EXAM DATES:
   - Dedicate the last 2-3 days before an exam exclusively to intense revision, formula synthesis, and past papers.
5. STRICT TIMING:
   - ONLY schedule at the exact dates, start times, and durations listed in the ALLOWED SLOTS above.

Return JSON in this format:
{{
    "plan_summary": "High-level strategic narrative of the plan, pacing, and readiness trajectory",
    "reasoning": "Detailed rationale explaining subject balancing, circadian alignment, and break distribution",
    "sessions": [
        {{
            "session_type": "study",
            "subject": "Subject Name",
            "topic": "Topic Name",
            "date": "YYYY-MM-DD",
            "start_time": "HH:MM",
            "duration_min": 90,
            "priority": "high|medium|low",
            "study_technique": "Active Recall & Problem Solving",
            "notes": "Actionable goal for this 90-minute session",
            "rationale": "Why this session is placed here"
        }},
        {{
            "session_type": "break",
            "subject": "",
            "topic": "Refreshment Break",
            "date": "YYYY-MM-DD",
            "start_time": "10:15",
            "duration_min": 15,
            "priority": "low",
            "study_technique": "",
            "notes": "Hydrate, stretch, and relax eyes away from screens",
            "rationale": "15-min cognitive decompression between deep work blocks"
        }},
        {{
            "session_type": "break",
            "subject": "",
            "topic": "Lunch Break",
            "date": "YYYY-MM-DD",
            "start_time": "12:30",
            "duration_min": 45,
            "priority": "low",
            "study_technique": "",
            "notes": "Nutritious meal and offline relaxation to restore working memory",
            "rationale": "Mid-day 45-min meal and recovery"
        }}
    ]
}}"""

    try:
        response = llm.invoke(prompt)
        result = extract_json_safe(response.content)
        llm_sessions = result.get("sessions", [])

        # Validate against availability
        valid_sessions = _validate_sessions(llm_sessions, availability)

        # Fallback supplement if needed
        fallback_sessions = _fallback_schedule(subjects, topics_by_subject, exams, availability)
        min_expected = max(len(fallback_sessions) // 2, 5)

        if len(valid_sessions) < min_expected and fallback_sessions:
            used_slots = {(vs.get("date", ""), vs.get("start_time", "")) for vs in valid_sessions}
            for fs in fallback_sessions:
                key = (fs.get("date", ""), fs.get("start_time", ""))
                if key not in used_slots:
                    valid_sessions.append(fs)
                    used_slots.add(key)

        valid_sessions.sort(key=lambda x: (x.get("date", ""), x.get("start_time", "")))

        return {
            "plan_summary": result.get("plan_summary", "Claude-optimized comprehensive study run"),
            "reasoning": result.get("reasoning", "Constructed using cognitive science principles, active recall, and structured meal intervals."),
            "sessions": valid_sessions,
        }

    except Exception as e:
        return {
            "plan_summary": f"Using algorithmic scheduler with breaks (LLM message: {str(e)[:90]})",
            "reasoning": "Algorithmic scheduling fallback with interleaved meal breaks and active recall pacing.",
            "sessions": _fallback_schedule(subjects, topics_by_subject, exams, availability),
        }


# ─── Fallback Scheduler with Breaks ────────────────────────────────
def _fallback_schedule(subjects, topics_by_subject, exams, availability):
    """
    Generate an algorithmic fallback timetable including:
    - Breakfast, Lunch, Evening Refreshment, and Dinner breaks.
    - Topic round-robin with study techniques and notes.
    """
    sessions = []
    today = datetime.now()

    all_topics = []
    for s in subjects:
        for t in topics_by_subject.get(s["name"], []):
            all_topics.append({"subject": s["name"], "topic": t["topic_name"]})

    if not all_topics or not availability:
        return sessions

    day_slots = _generate_time_slots(availability)
    topic_idx = 0
    num_days = _calc_plan_days(exams, today)

    techniques = [
        "Active Recall & Practice Problems",
        "Feynman Technique & Explanations",
        "Concept Synthesis & Flashcards",
        "Deep Work & Code/Derivation Drill",
    ]

    for day_offset in range(num_days):
        current_date = today + timedelta(days=day_offset)
        day_name = current_date.strftime("%A")
        date_str = current_date.strftime("%Y-%m-%d")

        slots = day_slots.get(day_name, [])
        for slot in slots:
            if slot.get("type") == "break":
                sessions.append({
                    "session_type": "break",
                    "subject": "",
                    "topic": slot.get("name", "Refreshment Break"),
                    "date": date_str,
                    "start_time": slot["start_time"],
                    "duration_min": slot["duration_min"],
                    "priority": "low",
                    "study_technique": "",
                    "notes": slot.get("notes", "Step away from screen, hydrate and recharge"),
                    "rationale": "Circadian rhythm rest period",
                })
            else:
                if topic_idx >= len(all_topics):
                    topic_idx = 0
                t = all_topics[topic_idx]
                technique = techniques[topic_idx % len(techniques)]

                sessions.append({
                    "session_type": "study",
                    "subject": t["subject"],
                    "topic": t["topic"],
                    "date": date_str,
                    "start_time": slot["start_time"],
                    "duration_min": slot["duration_min"],
                    "priority": "high" if slot.get("is_peak") else "medium",
                    "study_technique": technique,
                    "notes": f"Master core mechanics of {t['topic']} using {technique.split('&')[0].strip()}.",
                    "rationale": "Algorithmic scheduling matched to available focus window",
                })
                topic_idx += 1

    return sessions


# ─── Save & Recalculate ────────────────────────────────────────────
def save_study_plan(plan: dict, subject_map: dict, topic_map: dict):
    """Save generated study plan sessions to database (handles both study and breaks)."""
    from db.database import add_study_session, clear_sessions

    clear_sessions()
    saved = 0
    for session in plan.get("sessions", []):
        stype = session.get("session_type", "study")
        sid = subject_map.get(session.get("subject")) if stype != "break" else None
        tid = topic_map.get(session.get("topic")) if stype != "break" else None

        add_study_session(
            subject_id=sid,
            topic_id=tid,
            session_date=session.get("date", ""),
            start_time=session.get("start_time", "09:00"),
            duration_min=session.get("duration_min", 60),
            priority=session.get("priority", "medium"),
            status="planned",
            session_type=stype,
            study_technique=session.get("study_technique", ""),
            notes=session.get("notes", session.get("topic") if stype == "break" else ""),
        )
        saved += 1
    return saved


def recalculate_after_skip(skipped_sessions: list, remaining_sessions: list, availability: list) -> list:
    """Redistribute skipped study session topics into remaining free slots."""
    llm = get_llm(temperature=0.2, max_tokens=2500, json_mode=True)

    study_skipped = [s for s in skipped_sessions if s.get("session_type") != "break"]
    if not study_skipped:
        return []

    prompt = f"""Some study sessions were missed or skipped. Intelligently redistribute these topics into available slots.

SKIPPED STUDY SESSIONS:
{json.dumps(study_skipped, indent=2)}

UPCOMING SESSIONS:
{json.dumps(remaining_sessions[:25], indent=2)}

AVAILABILITY CONSTRAINTS:
{json.dumps(availability[:14], indent=2)}

Redistribute the skipped topics without disrupting planned meals or peak study hours.
Return JSON:
{{
    "adjusted_sessions": [
        {{
            "session_type": "study",
            "subject": "Subject Name",
            "topic": "Topic Name",
            "date": "YYYY-MM-DD",
            "start_time": "HH:MM",
            "duration_min": 60,
            "priority": "high",
            "study_technique": "Active Recall & Rapid Review",
            "notes": "Catch-up focus session",
            "rationale": "Redistributed from skipped session"
        }}
    ]
}}"""

    try:
        response = llm.invoke(prompt)
        result = extract_json_safe(response.content)
        validated = _validate_sessions(result.get("adjusted_sessions", []), availability)
        return validated
    except Exception:
        return []

