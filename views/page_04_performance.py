# views/page_04_performance.py — Performance Re-Calibration
import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.theme import page_header, section_header, metric_card, badge, reasoning_box, glass_panel
from utils.charts import render_performance_bars
from db.database import (
    get_all_subjects, add_test_score, get_all_scores, get_scores_by_subject,
    get_all_difficulties,
)


def render():
    page_header("📊 Performance", "Input test scores & re-calibrate priorities")

    subjects = get_all_subjects()
    if not subjects:
        st.info("📝 No subjects found. Go to **Data Setup** first.")
        return

    tab1, tab2 = st.tabs(["📝 Enter Scores", "📊 Analysis"])

    # ─── Tab 1: Enter Scores ─────────────────────────────────────
    with tab1:
        section_header("Add Test Scores")

        with st.form("score_form", clear_on_submit=True):
            subject_name = st.selectbox("Subject", [s["name"] for s in subjects])
            subject_id = next(s["id"] for s in subjects if s["name"] == subject_name)

            col1, col2 = st.columns(2)
            with col1:
                test_type = st.selectbox("Test Type", ["cie1", "cie2", "cie3", "quiz", "assignment", "midterm", "mock"])
                score = st.number_input("Score Obtained", min_value=0.0, max_value=200.0, value=0.0, step=0.5)
            with col2:
                max_score = st.number_input("Maximum Score", min_value=1.0, max_value=200.0, value=50.0, step=0.5)
                test_date = st.date_input("Test Date")

            notes = st.text_area("Notes (optional)", placeholder="Any observations about the test...")

            if st.form_submit_button("💾 Save Score", use_container_width=True):
                if score > 0:
                    add_test_score(subject_id, score, max_score, test_type, str(test_date), notes)
                    st.success(f"✅ Saved: {subject_name} — {score}/{max_score} ({(score/max_score*100):.1f}%)")
                    st.rerun()
                else:
                    st.warning("Please enter a valid score.")

        # Score history
        all_scores = get_all_scores()
        if all_scores:
            section_header("Score History")
            for sc in all_scores:
                pct = (sc["score"] / sc["max_score"]) * 100 if sc["max_score"] > 0 else 0
                pct_color = "#00E676" if pct >= 70 else "#FFB740" if pct >= 50 else "#FF5252"
                type_badge = badge(sc["test_type"].upper(), "info")

                st.markdown(f"""
                <div class="session-card">
                    <div style="flex: 1;">
                        <div class="session-subject">{sc['subject_name']}</div>
                        <div style="color: #9AA0A6; font-size: 0.8rem;">{sc.get('test_date', '')} {type_badge}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="color: {pct_color}; font-weight: 700; font-size: 1.2rem;">{pct:.0f}%</div>
                        <div style="color: #9AA0A6; font-size: 0.8rem;">{sc['score']}/{sc['max_score']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ─── Tab 2: AI Analysis ──────────────────────────────────────
    with tab2:
        section_header("AI Performance Analysis")

        all_scores = get_all_scores()
        if not all_scores:
            st.info("📝 Enter test scores first to generate analysis.")
            return

        # Performance comparison chart
        subject_names = list(set(sc["subject_name"] for sc in all_scores))
        avg_scores = []
        expected_scores = []
        for name in subject_names:
            scores = [sc for sc in all_scores if sc["subject_name"] == name]
            avg = sum(sc["score"] / sc["max_score"] * 100 for sc in scores) / len(scores)
            avg_scores.append(round(avg, 1))
            # Expected based on self-rating
            subj = next((s for s in subjects if s["name"] == name), None)
            expected_scores.append(subj["self_rating"] * 10 if subj else 50)

        st.plotly_chart(
            render_performance_bars(subject_names, expected_scores, avg_scores),
            use_container_width=True,
        )

        # AI Analysis button
        if st.button("🧠 Run AI Performance Analysis", use_container_width=True):
            with st.spinner("🧠 Analyzing performance patterns..."):
                try:
                    from agents.performance_analyzer_agent import analyze_performance, update_priorities_from_analysis

                    difficulties = {}
                    for d in get_all_difficulties():
                        difficulties[d["topic_name"]] = {"level": d["level"], "score": d["score"]}

                    analysis = analyze_performance(all_scores, subjects, difficulties)

                    # Display results
                    if analysis.get("reasoning"):
                        reasoning_box(analysis["reasoning"])

                    st.markdown("---")
                    section_header("Subject Analysis")

                    for sa in analysis.get("subject_analysis", []):
                        perf_color = "#00E676" if sa.get("performance_level") == "above_average" else "#FFB740" if sa.get("performance_level") == "average" else "#FF5252"
                        shift = sa.get("priority_shift", "maintain")
                        shift_badge = badge(f"Priority: {shift.upper()}", "danger" if shift == "increase" else "success" if shift == "decrease" else "info")

                        st.markdown(f"""
                        <div class="glass-panel">
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                                <h4 style="color: #E8EAED; margin: 0;">{sa.get('subject', '')}</h4>
                                <div style="display: flex; gap: 0.5rem; align-items: center;">
                                    <span style="color: {perf_color}; font-weight: 700;">{sa.get('score_pct', 0):.0f}%</span>
                                    {shift_badge}
                                </div>
                            </div>
                            <div style="color: #9AA0A6; font-size: 0.85rem; line-height: 1.6;">
                                {sa.get('focus_recommendation', '')}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Recommendations
                    recs = analysis.get("recommendations", [])
                    if recs:
                        section_header("📋 Recommendations")
                        for r in recs:
                            st.markdown(f"• {r}")

                    # Save updated priorities
                    subject_map = {s["name"]: s["id"] for s in subjects}
                    update_priorities_from_analysis(analysis, subject_map)

                except Exception as e:
                    st.error(f"❌ Analysis error: {str(e)}")
