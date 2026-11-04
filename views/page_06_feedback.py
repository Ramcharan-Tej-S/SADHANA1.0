# views/page_06_feedback.py — Feedback Loop & Analytics
import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.theme import page_header, section_header, metric_card, badge, glass_panel, reasoning_box
from utils.charts import render_trend_line, render_coverage_pie, render_subject_radar
from db.database import (
    get_all_subjects, get_latest_performance, get_performance_history,
    get_all_sessions, get_all_scores, get_all_topics, get_topics_by_subject,
)


def render():
    page_header("🔄 Feedback Loop", "Continuous learning analytics & AI recommendations")

    subjects = get_all_subjects()
    if not subjects:
        st.info("📝 No subjects found. Go to **Data Setup** first.")
        return

    tab1, tab2, tab3 = st.tabs(["📈 Trends", "🧠 AI Insights", "📋 Summary"])

    # ─── Tab 1: Trends ───────────────────────────────────────────
    with tab1:
        section_header("Performance Trends")

        # Aggregate data
        all_scores = get_all_scores()
        all_sessions = get_all_sessions()

        if not all_scores:
            st.info("📝 No performance data yet. Enter test scores in the **Performance** page.")
            return

        # Overall stats
        total_study_min = sum(s.get("duration_min", 0) for s in all_sessions if s.get("status") == "completed")
        total_study_hrs = total_study_min / 60
        avg_score = sum(sc["score"] / sc["max_score"] * 100 for sc in all_scores) / len(all_scores)
        total_topics = len(get_all_topics())
        covered_topics = len(set(s.get("topic_name") for s in all_sessions if s.get("status") == "completed" and s.get("topic_name")))

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card("⏱️ Total Study Time", f"{total_study_hrs:.1f}h")
        with c2:
            metric_card("📊 Avg Score", f"{avg_score:.0f}%")
        with c3:
            metric_card("📚 Topic Coverage", f"{covered_topics}/{total_topics}")
        with c4:
            completion_rate = (sum(1 for s in all_sessions if s.get("status") == "completed") / len(all_sessions) * 100) if all_sessions else 0
            metric_card("✅ Completion Rate", f"{completion_rate:.0f}%")

        # Coverage donut
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            section_header("Syllabus Coverage")
            st.plotly_chart(
                render_coverage_pie(covered_topics, max(0, total_topics - covered_topics)),
                use_container_width=True,
            )
        with col2:
            # Score trend by subject
            section_header("Score Distribution")
            for s in subjects:
                scores = [sc for sc in all_scores if sc["subject_name"] == s["name"]]
                if scores:
                    avg = sum(sc["score"] / sc["max_score"] * 100 for sc in scores) / len(scores)
                    color = "#00E676" if avg >= 70 else "#FFB740" if avg >= 50 else "#FF5252"
                    st.markdown(f"""
                    <div style="display: flex; justify-content: space-between; padding: 0.4rem 0; border-bottom: 1px solid #2D3143;">
                        <span style="color: #E8EAED;">{s['name']}</span>
                        <span style="color: {color}; font-weight: 600;">{avg:.0f}%</span>
                    </div>
                    """, unsafe_allow_html=True)

        # Readiness trend
        for s in subjects:
            history = get_performance_history(s["id"])
            if len(history) >= 2:
                st.markdown("---")
                section_header(f"📈 {s['name']} — Readiness Trend")
                dates = [h["logged_at"][:10] for h in history]
                scores = [h["readiness_score"] for h in history]
                st.plotly_chart(render_trend_line(dates, scores, f"{s['name']} Readiness"), use_container_width=True)

    # ─── Tab 2: AI Insights ──────────────────────────────────────
    with tab2:
        section_header("AI-Powered Study Insights")

        if st.button("🧠 Generate AI Insights", use_container_width=True, type="primary"):
            with st.spinner("🧠 Analyzing your learning patterns..."):
                try:
                    from agents.feedback_loop_agent import analyze_prediction_accuracy, generate_improvement_suggestions

                    # Gather performance history
                    all_history = []
                    for s in subjects:
                        history = get_performance_history(s["id"])
                        for h in history:
                            h["subject_name"] = s["name"]
                        all_history.extend(history)

                    # Accuracy analysis
                    accuracy = analyze_prediction_accuracy(all_history)
                    if accuracy.get("reasoning"):
                        reasoning_box(accuracy["reasoning"])

                    st.markdown(f"""
                    <div class="glass-panel">
                        <h4 style="color: #E8EAED; margin-top: 0;">📊 Prediction Accuracy</h4>
                        <p style="color: #9AA0A6; line-height: 1.6;">{accuracy.get('accuracy_summary', 'No data yet')}</p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Subject accuracy
                    for sa in accuracy.get("subject_accuracy", []):
                        bias_color = "#FF5252" if sa.get("bias") == "over-predicted" else "#FFB740" if sa.get("bias") == "under-predicted" else "#00E676"
                        st.markdown(f"""
                        <div class="session-card">
                            <div style="flex: 1;">
                                <div class="session-subject">{sa.get('subject', '')}</div>
                                <div style="color: #9AA0A6; font-size: 0.8rem;">Avg Error: {sa.get('avg_error', 0):.1f}%</div>
                            </div>
                            <span style="color: {bias_color}; font-weight: 600; font-size: 0.85rem;">{sa.get('bias', 'unknown').replace('-', ' ').title()}</span>
                        </div>
                        """, unsafe_allow_html=True)

                    # Improvement suggestions
                    st.markdown("---")
                    suggestions = generate_improvement_suggestions(all_history, get_all_sessions())

                    section_header("💡 Personalized Study Tips")
                    for tip in suggestions.get("suggestions", []):
                        impact_badge = badge(tip.get("impact", "medium").upper(), "hard" if tip.get("impact") == "high" else "medium" if tip.get("impact") == "medium" else "easy")
                        cat_badge = badge(tip.get("category", "").replace("_", " ").title(), "info")
                        st.markdown(f"""
                        <div class="topic-item">
                            <span style="color: #E8EAED;">💡 {tip.get('tip', '')}</span>
                            <div>{impact_badge} {cat_badge}</div>
                        </div>
                        """, unsafe_allow_html=True)

                    if suggestions.get("overall_assessment"):
                        glass_panel(f"""
                            <div style="color: #6C63FF; font-weight: 600; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 0.5rem;">Overall Assessment</div>
                            <div style="color: #BFC3C9; font-size: 0.9rem;">{suggestions['overall_assessment']}</div>
                        """)

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    # ─── Tab 3: Summary ──────────────────────────────────────────
    with tab3:
        section_header("Semester Summary")

        all_scores = get_all_scores()
        all_sessions = get_all_sessions()

        if not all_scores and not all_sessions:
            st.info("📝 No data available yet for a summary.")
            return

        # Per-subject summary
        for s in subjects:
            scores = [sc for sc in all_scores if sc["subject_name"] == s["name"]]
            sessions = [ss for ss in all_sessions if ss.get("subject_name") == s["name"]]
            topics = get_topics_by_subject(s["id"])

            completed_sessions = sum(1 for ss in sessions if ss.get("status") == "completed")
            total_sessions = len(sessions)
            study_mins = sum(ss.get("duration_min", 0) for ss in sessions if ss.get("status") == "completed")

            avg_score = "N/A"
            score_color = "#9AA0A6"
            if scores:
                avg = sum(sc["score"] / sc["max_score"] * 100 for sc in scores) / len(scores)
                avg_score = f"{avg:.0f}%"
                score_color = "#00E676" if avg >= 70 else "#FFB740" if avg >= 50 else "#FF5252"

            st.markdown(f"""
            <div class="glass-panel">
                <h4 style="color: #E8EAED; margin-top: 0;">{s['name']} ({s['code']})</h4>
                <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-top: 0.8rem;">
                    <div>
                        <div style="color: #9AA0A6; font-size: 0.75rem;">Avg Score</div>
                        <div style="color: {score_color}; font-weight: 700; font-size: 1.2rem;">{avg_score}</div>
                    </div>
                    <div>
                        <div style="color: #9AA0A6; font-size: 0.75rem;">Sessions</div>
                        <div style="color: #00D9FF; font-weight: 700; font-size: 1.2rem;">{completed_sessions}/{total_sessions}</div>
                    </div>
                    <div>
                        <div style="color: #9AA0A6; font-size: 0.75rem;">Study Time</div>
                        <div style="color: #BB86FC; font-weight: 700; font-size: 1.2rem;">{study_mins/60:.1f}h</div>
                    </div>
                    <div>
                        <div style="color: #9AA0A6; font-size: 0.75rem;">Topics</div>
                        <div style="color: #64FFDA; font-weight: 700; font-size: 1.2rem;">{len(topics)}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
