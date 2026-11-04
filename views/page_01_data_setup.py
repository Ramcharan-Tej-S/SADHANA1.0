# views/page_01_data_setup.py — Upload Syllabus & Self-Assessment
import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.theme import page_header, section_header, metric_card, badge, glass_panel
from db.database import (
    add_subject, get_all_subjects, add_uploaded_file, get_uploaded_files,
    mark_file_processed, get_stats, delete_subject,
)
from config import UPLOAD_DIR


def render():
    page_header("📚 Data Setup", "Upload syllabus, add subjects & self-assess difficulty")

    tab1, tab2, tab3 = st.tabs(["➕ Add Subjects", "📄 Upload Files", "📋 Current Data"])

    # ─── Tab 1: Add Subjects ──────────────────────────────────────
    with tab1:
        section_header("Add a New Subject")

        with st.form("add_subject_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Subject Name *", placeholder="e.g., Data Structures & Algorithms")
                code = st.text_input("Subject Code", placeholder="e.g., CS301")
            with col2:
                credits = st.number_input("Credits", min_value=1, max_value=6, value=3)
                semester = st.number_input("Semester", min_value=1, max_value=8, value=3)

            self_rating = st.slider(
                "Self-Assessment: How comfortable are you with this subject?",
                min_value=1.0, max_value=10.0, value=5.0, step=0.5,
                help="1 = Very Difficult, 10 = Very Easy"
            )

            submitted = st.form_submit_button("➕ Add Subject", use_container_width=True)
            if submitted and name.strip():
                sid = add_subject(name.strip(), code.strip(), credits, semester, self_rating)
                st.success(f"✅ Added **{name}** (ID: {sid})")
                st.rerun()
            elif submitted:
                st.warning("Please enter a subject name.")

    # ─── Tab 2: Upload Files ─────────────────────────────────────
    with tab2:
        section_header("Upload Syllabus or Question Papers")

        subjects = get_all_subjects()
        if not subjects:
            st.info("📝 Add subjects first before uploading files.")
        else:
            subject_options = {s["name"]: s["id"] for s in subjects}
            selected_subject = st.selectbox("Select Subject", list(subject_options.keys()))
            file_type = st.radio("File Type", ["syllabus", "question_paper"], horizontal=True)

            uploaded_file = st.file_uploader(
                "Upload Document or Image (PDF, TXT, PNG, JPG)",
                type=["pdf", "txt", "png", "jpg", "jpeg"],
                key="syllabus_upload",
            )

            if uploaded_file is not None:
                if st.button("📤 Process Upload", use_container_width=True):
                    # Save file
                    file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    sid = subject_options[selected_subject]
                    file_id = add_uploaded_file(uploaded_file.name, file_path, file_type, sid)

                    st.success(f"✅ Saved **{uploaded_file.name}**")

                    # Process with AI
                    with st.spinner("🧠 AI is analyzing the document..."):
                        try:
                            from agents.syllabus_parser_agent import extract_text_from_file, parse_syllabus, save_parsed_syllabus

                            text = extract_text_from_file(file_path)

                            if text and not text.startswith("Error"):
                                if file_type == "syllabus":
                                    parsed = parse_syllabus(text, selected_subject)
                                    _, topic_count = save_parsed_syllabus(parsed, sid)
                                    mark_file_processed(file_id)
                                    st.success(f"🧬 Extracted **{topic_count} topics** from syllabus!")

                                    # Show reasoning
                                    if parsed.get("reasoning"):
                                        st.markdown("---")
                                        glass_panel(f"""
                                            <div style="color: #6C63FF; font-weight: 600; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem;">🧠 AI Reasoning</div>
                                            <div style="color: #BFC3C9; font-size: 0.85rem; line-height: 1.6;">{parsed['reasoning']}</div>
                                        """)
                                else:
                                    from agents.syllabus_parser_agent import parse_question_paper
                                    parsed = parse_question_paper(text, selected_subject)
                                    mark_file_processed(file_id)

                                    important = parsed.get("important_topics", [])
                                    if important:
                                        st.success(f"📝 Identified **{len(important)} important topics** from question paper!")
                                        for t in important:
                                            freq_badge = badge(t.get("frequency", "medium"), t.get("frequency", "info"))
                                            st.markdown(f"""
                                            <div class="topic-item">
                                                <span style="color: #E8EAED;">{t.get('topic', '')}</span>
                                                {freq_badge}
                                                <span style="color: #9AA0A6; font-size: 0.8rem;">{t.get('marks_weight', '')}</span>
                                            </div>
                                            """, unsafe_allow_html=True)
                            else:
                                st.error(f"❌ Could not extract text: {text}")
                        except Exception as e:
                            st.error(f"❌ Processing error: {str(e)}")
                            mark_file_processed(file_id)

        # Upload history
        files = get_uploaded_files()
        if files:
            section_header("Upload History")
            for f in files:
                status = badge("Processed", "success") if f["processed"] else badge("Pending", "warning")
                st.markdown(f"""
                <div class="session-card">
                    <span style="color: #E8EAED; flex: 1;">📄 {f['filename']}</span>
                    <span style="color: #9AA0A6; font-size: 0.8rem;">{f.get('file_type', '')}</span>
                    {status}
                </div>
                """, unsafe_allow_html=True)

    # ─── Tab 3: Current Data ─────────────────────────────────────
    with tab3:
        section_header("Registered Subjects")

        subjects = get_all_subjects()
        if not subjects:
            st.info("No subjects added yet. Use the 'Add Subjects' tab or seed demo data from the sidebar.")
        else:
            for s in subjects:
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                with col1:
                    st.markdown(f"**{s['name']}** ({s['code']})")
                with col2:
                    st.markdown(f"<span style='color: #9AA0A6;'>{s['credits']} credits</span>", unsafe_allow_html=True)
                with col3:
                    rating_color = "#00E676" if s['self_rating'] >= 7 else "#FFB740" if s['self_rating'] >= 4 else "#FF5252"
                    st.markdown(f"<span style='color: {rating_color}; font-weight: 600;'>Self: {s['self_rating']}/10</span>", unsafe_allow_html=True)
                with col4:
                    if st.button("🗑️", key=f"del_{s['id']}", help=f"Delete {s['name']}"):
                        delete_subject(s['id'])
                        st.rerun()

            # Quick stats
            st.markdown("---")
            stats = get_stats()
            c1, c2, c3 = st.columns(3)
            with c1:
                metric_card("Subjects", str(stats['subjects']))
            with c2:
                metric_card("Topics", str(stats['topics']))
            with c3:
                metric_card("Files Uploaded", str(len(get_uploaded_files())))
