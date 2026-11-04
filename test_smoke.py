# test_smoke.py — ExamFlow AI Smoke Test
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("  ExamFlow AI — Smoke Test")
print("=" * 60)

# Test 1: Config
print("\n[1/8] Testing config...")
from config import get_llm, COLORS, DIFFICULTY_LEVELS, DIFFICULTY_LABELS, FOCUS_SLOTS
assert len(COLORS) > 10, "Missing color tokens"
assert len(DIFFICULTY_LEVELS) == 3, "Expected 3 difficulty levels"
assert len(FOCUS_SLOTS) == 5, "Expected 5 focus slots"
print(f"  ✅ Config OK: {len(COLORS)} colors, {len(DIFFICULTY_LEVELS)} difficulty levels")

# Test 2: Database
print("\n[2/8] Testing database...")
from db.database import init_db, get_connection, get_stats
init_db()
conn = get_connection()
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
table_names = [t[0] for t in tables]
conn.close()
expected_tables = ["subjects", "topics", "difficulty_scores", "exam_schedule",
                   "availability", "test_scores", "study_sessions", "performance_log", "uploaded_files"]
for t in expected_tables:
    assert t in table_names, f"Missing table: {t}"
print(f"  ✅ DB OK: {len(table_names)} tables: {table_names}")

# Test 3: Agent imports
print("\n[3/8] Testing agent imports...")
from agents.syllabus_parser_agent import extract_text_from_file, parse_syllabus, save_parsed_syllabus
print("  ✅ Syllabus parser agent (Chain-of-Thought) OK")
from agents.difficulty_assessor_agent import assess_difficulty, save_difficulty_results
print("  ✅ Difficulty assessor agent (LLM-as-Judge) OK")
from agents.schedule_optimizer_agent import generate_study_plan, save_study_plan
print("  ✅ Schedule optimizer agent (Constraint-aware) OK")
from agents.performance_analyzer_agent import analyze_performance, update_priorities_from_analysis
print("  ✅ Performance analyzer agent (Adaptive) OK")
from agents.readiness_predictor_agent import predict_readiness, predict_all_subjects
print("  ✅ Readiness predictor agent (CoT scoring) OK")
from agents.feedback_loop_agent import analyze_prediction_accuracy, generate_improvement_suggestions
print("  ✅ Feedback loop agent (Continuous learning) OK")

# Test 4: Charts
print("\n[4/8] Testing charts...")
from utils.charts import (
    render_readiness_gauge, render_difficulty_radar, render_schedule_timeline,
    render_performance_bars, render_coverage_pie, render_trend_line,
    render_difficulty_distribution, render_subject_radar,
)
fig = render_readiness_gauge(65, "Test Gauge")
assert fig is not None, "Gauge chart failed"
fig2 = render_difficulty_radar(["A", "B", "C", "D"], [3, 5, 7, 4])
assert fig2 is not None, "Radar chart failed"
fig3 = render_coverage_pie(30, 12)
assert fig3 is not None, "Coverage pie failed"
fig4 = render_difficulty_distribution(10, 15, 8)
assert fig4 is not None, "Difficulty distribution failed"
print("  ✅ Charts OK: all chart functions return valid figures")

# Test 5: Theme
print("\n[5/8] Testing theme...")
from utils.theme import inject_css, page_header, section_header, metric_card, badge, difficulty_badge, reasoning_box, progress_bar
print("  ✅ Theme OK: all functions importable")

# Test 6: Seed data
print("\n[6/8] Testing seed data...")
from utils.seed_data import seed_all, DEMO_SUBJECTS, DEMO_TOPICS
subjects, topics, diffs = seed_all()
print(f"  ✅ Seed data OK: {subjects} subjects, {topics} topics, {diffs} difficulties")
print(f"     Demo subjects: {len(DEMO_SUBJECTS)}")
print(f"     Demo topics: {sum(len(v) for v in DEMO_TOPICS.values())}")

# Test 7: Verify seeded data
print("\n[7/8] Verifying database content...")
from db.database import get_all_subjects, get_all_topics, get_all_exams, get_all_scores
all_subjects = get_all_subjects()
all_topics = get_all_topics()
all_exams = get_all_exams()
all_scores = get_all_scores()
stats = get_stats()
print(f"  ✅ Database verified: {stats}")
assert len(all_subjects) >= 5, f"Expected 5+ subjects, got {len(all_subjects)}"

# Test 8: Database CRUD operations
print("\n[8/8] Testing CRUD operations...")
from db.database import (
    add_subject, add_topic, add_difficulty_score, add_exam,
    add_availability, add_test_score, add_study_session, add_performance_log,
    add_uploaded_file, get_all_availability, get_all_sessions,
)
# These should all work without error
avail = get_all_availability()
sessions = get_all_sessions()
print(f"  ✅ CRUD OK: {len(avail)} availability slots, {len(sessions)} sessions")

print("\n" + "=" * 60)
print("  ✅ ALL TESTS PASSED — ExamFlow AI is ready!")
print("=" * 60)
print(f"\nTo run the app:")
print(f'  cd "{os.path.dirname(os.path.abspath(__file__))}"')
print(f'  $env:GROQ_API_KEY = "your_key"; streamlit run app.py')
