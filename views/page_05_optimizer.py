# views/page_05_optimizer.py — Optimized Timetable Generation
import streamlit as st
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.theme import page_header, section_header, metric_card, badge, glass_panel, reasoning_box, progress_bar
from utils.charts import render_schedule_timeline, render_readiness_gauge, render_coverage_pie, render_subject_radar
from db.database import (
    get_all_subjects, get_all_topics, get_topics_by_subject, get_all_difficulties,
    get_all_exams, get_upcoming_exams, get_all_availability, get_all_sessions, get_all_scores,
    update_session_status, clear_sessions,
)


def render():
    page_header("⚡ Optimizer", "AI-generated optimized study timetable")

    subjects = get_all_subjects()
    if not subjects:
        st.info("📝 No subjects found. Go to **Data Setup** first.")
        return

    # ─── Quick Stats ─────────────────────────────────────────────
    sessions = get_all_sessions()
    exams = get_upcoming_exams()

    planned = sum(1 for s in sessions if s.get("status") == "planned")
    completed = sum(1 for s in sessions if s.get("status") == "completed")
    skipped = sum(1 for s in sessions if s.get("status") == "skipped")
    total = len(sessions)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("📋 Total Sessions", str(total))
    with c2:
        metric_card("✅ Completed", str(completed), f"{(completed/total*100):.0f}%" if total > 0 else "0%")
    with c3:
        metric_card("⏳ Planned", str(planned))
    with c4:
        metric_card("⏭️ Skipped", str(skipped))

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["📅 Timetable", "📊 Readiness", "⚙️ Generate"])

    # ─── Tab 1: Timetable View ───────────────────────────────────
    with tab1:
        if not sessions:
            st.info("🔧 No study plan yet. Go to the **Generate** tab to create one!")
        else:
            # Timeline chart
            st.plotly_chart(render_schedule_timeline(sessions), use_container_width=True)

            # Session list grouped by date
            dates = sorted(set(s.get("session_date", "") for s in sessions))
            for d in dates:
                day_sessions = [s for s in sessions if s.get("session_date") == d]
                if not day_sessions:
                    continue

                try:
                    day_label = datetime.strptime(d, "%Y-%m-%d").strftime("%A, %b %d")
                except ValueError:
                    day_label = d

                st.markdown(f'<div class="unit-header">📅 {day_label}</div>', unsafe_allow_html=True)

                for sess in day_sessions:
                    status = sess.get("status", "planned")
                    priority = sess.get("priority", "medium")

                    status_badge = badge(status.upper(), status)
                    priority_badge = badge(priority.upper(), "hard" if priority == "high" else "medium" if priority == "medium" else "easy")

                    st.markdown(f"""
                    <div class="session-card">
                        <div class="session-time">{sess.get('start_time', '--:--')}</div>
                        <div style="flex: 1;">
                            <div class="session-subject">{sess.get('subject_name', '')}</div>
                            <div class="session-topic">{sess.get('topic_name', 'General Review')}</div>
                        </div>
                        <div style="color: #9AA0A6; font-size: 0.8rem;">{sess.get('duration_min', 60)} min</div>
                        {priority_badge}
                        {status_badge}
                    </div>
                    """, unsafe_allow_html=True)

                    # Action buttons
                    bc1, bc2, bc3 = st.columns([1, 1, 4])
                    with bc1:
                        if status == "planned" and st.button("✅", key=f"complete_{sess['id']}", help="Mark completed"):
                            update_session_status(sess["id"], "completed")
                            st.rerun()
                    with bc2:
                        if status == "planned" and st.button("⏭️", key=f"skip_{sess['id']}", help="Skip session"):
                            update_session_status(sess["id"], "skipped")
                            st.rerun()

    # ─── Tab 2: Readiness ────────────────────────────────────────
    with tab2:
        section_header("Exam Readiness Overview")

        if not sessions:
            st.info("Generate a study plan first to see readiness scores.")
        else:
            # Calculate readiness per subject
            readiness_data = []
            for s in subjects:
                s_sessions = [ss for ss in sessions if ss.get("subject_name") == s["name"]]
                s_completed = sum(1 for ss in s_sessions if ss.get("status") == "completed")
                s_total = len(s_sessions)
                completion_pct = (s_completed / s_total * 100) if s_total > 0 else 0

                topics = get_topics_by_subject(s["id"])
                total_topics = len(topics)
                covered = len(set(ss.get("topic_name") for ss in s_sessions if ss.get("status") == "completed"))
                coverage_pct = (covered / total_topics * 100) if total_topics > 0 else 0

                readiness = completion_pct * 0.6 + coverage_pct * 0.4
                readiness_data.append({
                    "subject": s["name"],
                    "readiness": round(readiness, 1),
                    "completion": round(completion_pct, 1),
                    "coverage": round(coverage_pct, 1),
                })

            # Radar chart
            if len(readiness_data) >= 3:
                st.plotly_chart(
                    render_subject_radar(
                        [r["subject"] for r in readiness_data],
                        [r["readiness"] for r in readiness_data],
                    ),
                    use_container_width=True,
                )

            # Per-subject cards
            for r in readiness_data:
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**{r['subject']}**")
                    progress_bar(r["readiness"])
                with col2:
                    color = "#00E676" if r["readiness"] >= 60 else "#FFB740" if r["readiness"] >= 30 else "#FF5252"
                    st.markdown(f'<span style="color: {color}; font-weight: 700; font-size: 1.3rem;">{r["readiness"]}%</span>', unsafe_allow_html=True)
                    st.markdown(f'<span style="color: #9AA0A6; font-size: 0.8rem;">Coverage: {r["coverage"]}%</span>', unsafe_allow_html=True)

            # AI Readiness prediction
            st.markdown("---")
            if st.button("🧠 Run AI Readiness Prediction", use_container_width=True):
                with st.spinner("🧠 Predicting exam readiness..."):
                    try:
                        from agents.readiness_predictor_agent import predict_all_subjects

                        difficulties = {}
                        for d in get_all_difficulties():
                            difficulties[d["topic_name"]] = {"level": d["level"], "score": d["score"]}

                        topics_by_subject = {s["name"]: get_topics_by_subject(s["id"]) for s in subjects}
                        sessions_by_subject = {s["name"]: [ss for ss in sessions if ss.get("subject_name") == s["name"]] for s in subjects}
                        scores_by_subject = {}
                        all_scores = get_all_scores()
                        for sc in all_scores:
                            scores_by_subject.setdefault(sc["subject_name"], []).append(sc)

                        exam_dates = {e["subject_name"]: e["exam_date"] for e in exams}

                        predictions = predict_all_subjects(subjects, topics_by_subject, difficulties, sessions_by_subject, scores_by_subject, exam_dates)

                        for pred in predictions:
                            st.plotly_chart(
                                render_readiness_gauge(pred.get("readiness_score", 0), pred.get("subject", "")),
                                use_container_width=True,
                            )
                            if pred.get("reasoning"):
                                reasoning_box(pred["reasoning"])
                            if pred.get("critical_gaps"):
                                st.markdown(f"**⚠️ Critical Gaps:** {', '.join(pred['critical_gaps'])}")

                    except Exception as e:
                        st.error(f"❌ Prediction error: {str(e)}")

    # ─── Tab 3: Generate ─────────────────────────────────────────
    with tab3:
        section_header("Generate Optimized Study Plan")

        availability = get_all_availability()
        if not availability:
            st.warning("⚠️ Set your availability in **Schedule Planner** first.")
        if not exams:
            st.warning("⚠️ Set exam dates in **Schedule Planner** first.")

        st.markdown("""
        <div class="glass-panel">
            <h4 style="color: #E8EAED; margin-top: 0;">🧠 AI Study Plan Generator</h4>
            <p style="color: #9AA0A6; font-size: 0.85rem; line-height: 1.6;">
                The AI will create an optimized study plan tailored to your exam dates, considering:<br>
                ✅ Topic difficulty levels<br>
                ✅ Your peak focus hours<br>
                ✅ Exam dates & deadlines<br>
                ✅ Spaced repetition for retention<br>
                ✅ Test score-based priority adjustments
            </p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⚡ Generate New Plan", use_container_width=True, type="primary"):
                if not availability or not exams:
                    st.error("Please set availability and exam dates first.")
                else:
                    with st.spinner("🧠 AI is optimizing your study schedule..."):
                        try:
                            from agents.schedule_optimizer_agent import generate_study_plan, save_study_plan

                            difficulties = {}
                            for d in get_all_difficulties():
                                difficulties[d["topic_name"]] = {"level": d["level"], "score": d["score"]}

                            topics_by_subject = {s["name"]: get_topics_by_subject(s["id"]) for s in subjects}

                            # Get existing scores
                            existing_scores = {}
                            for sc in get_all_scores():
                                name = sc["subject_name"]
                                if name not in existing_scores:
                                    existing_scores[name] = {"score": sc["score"], "max_score": sc["max_score"]}

                            plan = generate_study_plan(
                                subjects=subjects,
                                topics_by_subject=topics_by_subject,
                                difficulties=difficulties,
                                exams=exams,
                                availability=availability,
                                existing_scores=existing_scores,
                            )

                            # Save plan
                            subject_map = {s["name"]: s["id"] for s in subjects}
                            topic_map = {}
                            for s in subjects:
                                for t in get_topics_by_subject(s["id"]):
                                    topic_map[t["topic_name"]] = t["id"]

                            saved = save_study_plan(plan, subject_map, topic_map)

                            st.success(f"✅ Generated **{saved}** study sessions!")

                            if plan.get("reasoning"):
                                reasoning_box(plan["reasoning"])

                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Generation error: {str(e)}")

        with col2:
            if sessions and st.button("🔄 Re-calculate Plan", use_container_width=True):
                clear_sessions()
                st.info("Cleared existing plan. Click 'Generate New Plan' to create a fresh one.")
                st.rerun()
