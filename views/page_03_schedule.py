# views/page_03_schedule.py — Availability & Exam Schedule Integration
import streamlit as st
import os
import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.theme import page_header, section_header, metric_card, badge, glass_panel
from db.database import (
    get_all_subjects, add_exam, get_upcoming_exams, get_exams_by_subject,
    mark_exam_completed, delete_past_exams,
    add_availability, get_all_availability, clear_availability,
)
from config import FOCUS_SLOTS


DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def render():
    page_header("📅 Schedule Planner", "Set exam dates, availability & peak focus hours")

    tab1, tab2, tab3 = st.tabs(["📝 Exam Dates", "⏰ Availability", "📊 Overview"])

    subjects = get_all_subjects()
    if not subjects:
        st.info("📝 No subjects found. Go to **Data Setup** first.")
        return

    # ─── Tab 1: Exam Dates ───────────────────────────────────────
    with tab1:
        section_header("Set Exam Dates")

        with st.form("exam_form", clear_on_submit=False):
            for s in subjects:
                existing = get_exams_by_subject(s["id"])
                existing_date = existing[0]["exam_date"] if existing else None
                existing_time = existing[0].get("exam_time", "09:00") if existing else "09:00"

                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.markdown(f"**{s['name']}**")
                    if existing_date:
                        try:
                            ex_d = datetime.strptime(existing_date, "%Y-%m-%d").date()
                            if ex_d >= date.today():
                                st.markdown(f"<span style='color: #00E676; font-size: 0.8rem;'>Scheduled: {existing_date}</span>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<span style='color: #FF5252; font-size: 0.8rem;'>Past: {existing_date}</span>", unsafe_allow_html=True)
                        except ValueError:
                            st.markdown(f"<span style='color: #9AA0A6; font-size: 0.8rem;'>Current: {existing_date}</span>", unsafe_allow_html=True)
                with col2:
                    default_date = date.today() + timedelta(days=14)
                    if existing_date:
                        try:
                            parsed_d = datetime.strptime(existing_date, "%Y-%m-%d").date()
                            if parsed_d >= date.today():
                                default_date = parsed_d
                        except ValueError:
                            pass

                    exam_date = st.date_input(
                        f"Exam date",
                        value=default_date,
                        key=f"exam_date_{s['id']}",
                        label_visibility="collapsed",
                    )
                with col3:
                    time_index = 0 if existing_time == "09:00" else 1
                    exam_time = st.selectbox(
                        "Time", ["09:00", "14:00"], index=time_index, key=f"exam_time_{s['id']}",
                        label_visibility="collapsed",
                    )
                st.markdown("---")

            if st.form_submit_button("💾 Save Exam Schedule", use_container_width=True):
                for s in subjects:
                    exam_date = st.session_state.get(f"exam_date_{s['id']}")
                    exam_time = st.session_state.get(f"exam_time_{s['id']}", "09:00")
                    if exam_date:
                        add_exam(s["id"], str(exam_date), exam_time)
                st.success("✅ Exam schedule saved!")
                st.rerun()

    # ─── Tab 2: Availability ────────────────────────────────────
    with tab2:
        section_header("Weekly Availability")
        st.markdown(
            '<p style="color: #9AA0A6; font-size: 0.85rem;">Set your available study hours for each day. Mark peak focus times for harder topics.</p>',
            unsafe_allow_html=True,
        )

        # Load saved availability from DB to pre-populate form
        saved_availability = get_all_availability()
        saved_by_day = {}
        for a in saved_availability:
            saved_by_day[a["day_of_week"]] = a

        with st.form("availability_form"):
            for day in DAYS:
                saved = saved_by_day.get(day)
                # Use saved values if they exist, otherwise use defaults
                if saved:
                    try:
                        default_start = datetime.strptime(saved["start_time"], "%H:%M").time()
                    except (ValueError, KeyError):
                        default_start = datetime.strptime("06:00", "%H:%M").time()
                    try:
                        default_end = datetime.strptime(saved["end_time"], "%H:%M").time()
                    except (ValueError, KeyError):
                        default_end = datetime.strptime("20:00", "%H:%M").time()
                    default_peak = bool(saved.get("is_peak", 0))
                    default_energy = saved.get("energy_level", "medium")
                    if default_energy not in ["low", "medium", "high"]:
                        default_energy = "medium"
                else:
                    default_start = datetime.strptime("06:00", "%H:%M").time()
                    default_end = datetime.strptime("20:00", "%H:%M").time()
                    default_peak = False
                    default_energy = "medium"

                with st.expander(f"📅 {day}", expanded=day in ["Saturday", "Sunday"]):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.time_input("Start time", value=default_start, key=f"av_start_{day}")
                    with col2:
                        st.time_input("End time", value=default_end, key=f"av_end_{day}")
                    with col3:
                        st.checkbox("Peak Focus ⚡", value=default_peak, key=f"av_peak_{day}")

                    st.select_slider(
                        "Energy Level",
                        options=["low", "medium", "high"],
                        value=default_energy,
                        key=f"av_energy_{day}",
                    )

            if st.form_submit_button("💾 Save Availability", use_container_width=True):
                clear_availability()
                for day in DAYS:
                    start = st.session_state.get(f"av_start_{day}")
                    end = st.session_state.get(f"av_end_{day}")
                    is_peak = st.session_state.get(f"av_peak_{day}", False)
                    energy = st.session_state.get(f"av_energy_{day}", "medium")
                    if start and end:
                        add_availability(day, start.strftime("%H:%M"), end.strftime("%H:%M"), 1 if is_peak else 0, energy)
                st.success("✅ Availability saved!")
                st.rerun()

    # ─── Tab 3: Overview ─────────────────────────────────────────
    with tab3:
        section_header("Exam Schedule Overview")

        today = date.today()
        # Automatically filter out completed and past exams
        exams = get_upcoming_exams(today.strftime("%Y-%m-%d"))
        availability = get_all_availability()

        if exams:
            # Countdown and active exams
            for e in exams:
                exam_dt = datetime.strptime(e["exam_date"], "%Y-%m-%d").date()
                days_left = (exam_dt - today).days

                if days_left == 0:
                    countdown_badge = badge("TODAY", "danger")
                    color = "#FF5252"
                elif days_left <= 3:
                    countdown_badge = badge(f"{days_left}d LEFT", "danger")
                    color = "#FF5252"
                elif days_left <= 7:
                    countdown_badge = badge(f"{days_left}d LEFT", "warning")
                    color = "#FFB740"
                else:
                    countdown_badge = badge(f"{days_left}d LEFT", "info")
                    color = "#00D9FF"

                col_card, col_action = st.columns([5, 1])
                with col_card:
                    st.markdown(f"""
                    <div class="session-card">
                        <div style="flex: 1;">
                            <div class="session-subject">{e['subject_name']}</div>
                            <div style="color: #9AA0A6; font-size: 0.8rem;">📅 {e['exam_date']} at {e.get('exam_time', '09:00')}</div>
                        </div>
                        <div style="color: {color}; font-weight: 700; font-size: 1.1rem; margin-right: 0.5rem;">{days_left}d</div>
                        {countdown_badge}
                    </div>
                    """, unsafe_allow_html=True)
                with col_action:
                    if st.button("✅ Done", key=f"complete_exam_{e['id']}", help="Mark exam completed (removes from overview)"):
                        mark_exam_completed(e["id"])
                        st.success(f"Marked {e['subject_name']} exam as completed!")
                        st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            col_l, col_r = st.columns([3, 1])
            with col_r:
                if st.button("🧹 Purge Outdated Records", key="purge_outdated_btn", help="Permanently delete completed and past exams from database", use_container_width=True):
                    delete_past_exams(today.strftime("%Y-%m-%d"))
                    st.success("Cleaned up outdated and completed exams!")
                    st.rerun()
        else:
            st.info("🎯 No upcoming exams scheduled. Completed and past exams are automatically removed from this overview. Use the **Exam Dates** tab to schedule upcoming exams.")

        if availability:
            st.markdown("---")
            section_header("Weekly Hours Summary")

            total_hours = 0
            peak_hours = 0
            for a in availability:
                try:
                    start = datetime.strptime(a["start_time"], "%H:%M")
                    end = datetime.strptime(a["end_time"], "%H:%M")
                    hours = (end - start).seconds / 3600
                    total_hours += hours
                    if a.get("is_peak"):
                        peak_hours += hours
                except ValueError:
                    pass

            c1, c2, c3 = st.columns(3)
            with c1:
                metric_card("Total Weekly Hours", f"{total_hours:.0f}h")
            with c2:
                metric_card("⚡ Peak Focus Hours", f"{peak_hours:.0f}h")
            with c3:
                metric_card("Available Days", f"{len(set(a['day_of_week'] for a in availability))}/7")
