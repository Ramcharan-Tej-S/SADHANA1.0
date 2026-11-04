# app.py — ExamFlow AI: Intelligent Exam Timetable Optimizer
import streamlit as st
import os
import sys

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.theme import inject_css, page_header, metric_card
from db.database import init_db, get_stats

# ─── Page Config ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="📚 ExamFlow AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Initialize ──────────────────────────────────────────────────────
init_db()
inject_css()

# ─── Sidebar ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1.5rem 0;">
        <div style="font-size: 2.5rem; margin-bottom: 0.3rem;">📚</div>
        <h1 style="font-size: 1.5rem; margin:0; letter-spacing: -0.02em;
                    background: linear-gradient(135deg, #6C63FF, #00D9FF);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            ExamFlow AI
        </h1>
        <p style="font-size: 0.75rem; margin: 0.3rem 0 0 0; color: #9AA0A6;">
            AI-Powered Exam Timetable Optimizer v1.0
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    page = st.radio(
        "Navigate",
        [
            "🏠 Home",
            "📚 Data Setup",
            "🧬 Syllabus Model",
            "📅 Schedule Planner",
            "📊 Performance",
            "⚡ Optimizer",
            "🔄 Feedback Loop",
        ],
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Seed data button
    if st.button("🌱 Seed Demo Data", use_container_width=True):
        from utils.seed_data import seed_all
        subjects, topics, diffs = seed_all()
        if subjects > 0:
            st.success(f"✅ Seeded {subjects} subjects, {topics} topics, {diffs} difficulties")
        else:
            st.info("Data already seeded.")

    # Stats
    stats = get_stats()
    st.markdown(f"""
    <div style="text-align:center; padding: 1rem 0; opacity: 0.6; font-size: 0.75rem; color: #9AA0A6;">
        📖 {stats['subjects']} subjects · 📝 {stats['topics']} topics · 📅 {stats['exams']} exams · 📋 {stats['sessions']} sessions
    </div>
    """, unsafe_allow_html=True)

# ─── Page Routing ─────────────────────────────────────────────────────
if page == "🏠 Home":
    page_header("📚 ExamFlow AI", "Intelligent Exam Timetable Optimizer")

    st.markdown("""
    <div style="max-width: 700px; margin-bottom: 2rem;">
        <p style="font-size: 1.05rem; color: #9AA0A6; line-height: 1.7;">
            Transform your exam preparation from chaotic last-minute cramming into an
            intelligent, AI-powered study system that adapts to your strengths, weaknesses,
            and schedule — maximizing your exam readiness.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Feature cards
    col1, col2, col3 = st.columns(3)
    features = [
        ("📚 Data Setup", "Upload syllabi, add subjects, and self-assess your comfort level per topic.", col1),
        ("🧬 Syllabus Model", "AI analyzes topics with 3-pass LLM-as-Judge difficulty scoring and reasoning.", col1),
        ("📅 Smart Schedule", "Set exam dates, availability, and peak focus hours for intelligent planning.", col2),
        ("📊 Performance", "CIE & quiz score tracking with AI-driven priority re-calibration.", col2),
        ("⚡ AI Optimizer", "Constraint-aware timetable generation with spaced repetition and difficulty balancing.", col3),
        ("🔄 Feedback Loop", "Continuous improvement — predictions vs actuals, personalized study tips.", col3),
    ]
    for title, desc, col in features:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{title}</h3>
                <div style="color: #9AA0A6; font-size: 0.85rem; line-height: 1.5;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Quick stats
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Subjects", str(stats["subjects"]))
    with c2:
        metric_card("Topics", str(stats["topics"]))
    with c3:
        metric_card("Study Sessions", str(stats["sessions"]))
    with c4:
        metric_card("AI Model", "LLaMA 3.3 70B", "via Groq")

    # AI Architecture section
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div class="glass-panel">
        <h3 style="color: #E8EAED; margin-top: 0;">🧠 AI Patterns Used</h3>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 1rem;">
            <div>
                <div style="color: #6C63FF; font-weight: 600; font-size: 0.85rem;">Chain-of-Thought</div>
                <div style="color: #9AA0A6; font-size: 0.8rem;">AI reasons step-by-step when parsing syllabi and predicting readiness</div>
            </div>
            <div>
                <div style="color: #00D9FF; font-weight: 600; font-size: 0.85rem;">LLM-as-Judge</div>
                <div style="color: #9AA0A6; font-size: 0.8rem;">3-pass difficulty scoring: assess → critique → calibrate</div>
            </div>
            <div>
                <div style="color: #00E676; font-weight: 600; font-size: 0.85rem;">Adaptive Planning</div>
                <div style="color: #9AA0A6; font-size: 0.8rem;">Schedule recalibrates based on test performance and skipped sessions</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

elif page == "📚 Data Setup":
    from views.page_01_data_setup import render
    render()
elif page == "🧬 Syllabus Model":
    from views.page_02_syllabus_model import render
    render()
elif page == "📅 Schedule Planner":
    from views.page_03_schedule import render
    render()
elif page == "📊 Performance":
    from views.page_04_performance import render
    render()
elif page == "⚡ Optimizer":
    from views.page_05_optimizer import render
    render()
elif page == "🔄 Feedback Loop":
    from views.page_06_feedback import render
    render()
