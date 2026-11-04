# views/page_02_syllabus_model.py — Subject & Syllabus Modeling
import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.theme import page_header, section_header, metric_card, badge, difficulty_badge, reasoning_box, confidence_bar, glass_panel
from utils.charts import render_difficulty_radar, render_difficulty_distribution
from db.database import (
    get_all_subjects, get_topics_by_subject, get_all_difficulties,
    get_difficulty_by_topic, get_all_topics,
)


def render():
    page_header("🧬 Syllabus Model", "AI-powered topic analysis & difficulty mapping")

    subjects = get_all_subjects()
    if not subjects:
        st.info("📝 No subjects found. Go to **Data Setup** to add subjects first.")
        return

    # ─── Overview Stats ──────────────────────────────────────────
    all_diffs = get_all_difficulties()
    easy_count = sum(1 for d in all_diffs if d["level"] == "easy")
    med_count = sum(1 for d in all_diffs if d["level"] == "medium")
    hard_count = sum(1 for d in all_diffs if d["level"] == "hard")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Total Topics", str(len(get_all_topics())))
    with c2:
        metric_card("🟢 Easy", str(easy_count))
    with c3:
        metric_card("🟡 Medium", str(med_count))
    with c4:
        metric_card("🔴 Hard", str(hard_count))

    # ─── Difficulty Distribution ─────────────────────────────────
    if all_diffs:
        st.plotly_chart(render_difficulty_distribution(easy_count, med_count, hard_count),
                        use_container_width=True, key="diff_dist")

    st.markdown("---")

    # ─── Per-Subject View ────────────────────────────────────────
    tab_names = [f"📖 {s['name']}" for s in subjects]
    tabs = st.tabs(tab_names)

    for i, s in enumerate(subjects):
        with tabs[i]:
            topics = get_topics_by_subject(s["id"])

            if not topics:
                st.info(f"No topics found for {s['name']}. Upload a syllabus in Data Setup.")

                # Manual topic add
                with st.expander("➕ Add Topics Manually"):
                    with st.form(f"add_topic_{s['id']}", clear_on_submit=True):
                        t_name = st.text_input("Topic Name", key=f"tn_{s['id']}")
                        t_unit = st.text_input("Unit Name", key=f"tu_{s['id']}", placeholder="e.g., Unit 1")
                        t_hours = st.number_input("Estimated Hours", min_value=0.5, max_value=20.0, value=2.0, key=f"th_{s['id']}")
                        if st.form_submit_button("Add Topic"):
                            from db.database import add_topic
                            add_topic(s["id"], t_name, t_unit, "", t_hours)
                            st.success(f"Added topic: {t_name}")
                            st.rerun()
                continue

            # Group by unit
            units = {}
            for t in topics:
                unit = t.get("unit_name", "General")
                units.setdefault(unit, []).append(t)

            # Difficulty radar for this subject
            topic_names = [t["topic_name"][:20] for t in topics]
            diff_scores = []
            for t in topics:
                d = get_difficulty_by_topic(t["id"])
                diff_scores.append(d["score"] if d else 5.0)

            if len(topic_names) >= 3:
                st.plotly_chart(render_difficulty_radar(topic_names, diff_scores),
                                use_container_width=True, key=f"radar_{s['id']}")

            # Topic tree
            for unit_name, unit_topics in units.items():
                st.markdown(f'<div class="unit-header">📂 {unit_name}</div>', unsafe_allow_html=True)

                for t in unit_topics:
                    diff = get_difficulty_by_topic(t["id"])

                    if diff:
                        level_badge = difficulty_badge(diff["level"])
                        score_display = f"{diff['score']}/10"
                        conf = diff.get("confidence", 0.5)
                    else:
                        level_badge = badge("Not Assessed", "info")
                        score_display = "—"
                        conf = 0

                    st.markdown(f"""
                    <div class="topic-item">
                        <div>
                            <span style="color: #E8EAED; font-weight: 500;">{t['topic_name']}</span>
                            <span style="color: #9AA0A6; font-size: 0.75rem; margin-left: 0.5rem;">⏱️ {t.get('estimated_hours', 2)}h</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 0.8rem;">
                            <span style="color: #00D9FF; font-size: 0.85rem; font-weight: 600;">{score_display}</span>
                            {level_badge}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # Show reasoning in expander
                    if diff and diff.get("reasoning"):
                        with st.expander(f"🧠 AI Reasoning — {t['topic_name']}", expanded=False):
                            reasoning_box(diff["reasoning"])
                            st.markdown(f"**Confidence:** ", unsafe_allow_html=True)
                            confidence_bar(conf)

            # ─── AI Assess Button ────────────────────────────────
            st.markdown("---")
            if st.button(f"🧠 Run AI Difficulty Assessment for {s['name']}", key=f"assess_{s['id']}", use_container_width=True):
                with st.spinner("🧠 Running 3-pass LLM-as-Judge assessment..."):
                    try:
                        from agents.difficulty_assessor_agent import assess_difficulty, save_difficulty_results

                        topic_data = [
                            {
                                "topic_id": t["id"],
                                "topic_name": t["topic_name"],
                                "unit_name": t.get("unit_name", ""),
                                "description": t.get("description", ""),
                            }
                            for t in topics
                        ]
                        results = assess_difficulty(topic_data, s["name"])

                        topic_map = {t["topic_name"]: t["id"] for t in topics}
                        saved = save_difficulty_results(results, topic_map, topic_list=topics)

                        if saved > 0:
                            st.success(f"✅ Assessed **{saved}** topics with 3-pass AI!")
                            st.rerun()
                        else:
                            st.warning("⚠️ Could not match any topics to save. Please try again.")
                    except Exception as e:
                        st.error(f"❌ Assessment error: {str(e)}")
