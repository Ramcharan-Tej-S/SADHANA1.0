# utils/seed_data.py — ExamFlow AI Demo Data Seeder
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ─── Demo Subjects ────────────────────────────────────────────────────
DEMO_SUBJECTS = [
    {"name": "Data Structures & Algorithms", "code": "CS301", "credits": 4, "semester": 3, "self_rating": 6.0},
    {"name": "Database Management Systems", "code": "CS302", "credits": 4, "semester": 3, "self_rating": 7.0},
    {"name": "Operating Systems", "code": "CS303", "credits": 3, "semester": 3, "self_rating": 5.0},
    {"name": "Computer Networks", "code": "CS304", "credits": 3, "semester": 3, "self_rating": 4.5},
    {"name": "Software Engineering", "code": "CS305", "credits": 3, "semester": 3, "self_rating": 7.5},
]

# ─── Demo Topics per Subject ─────────────────────────────────────────
DEMO_TOPICS = {
    "Data Structures & Algorithms": [
        {"unit_name": "Unit 1", "topic_name": "Arrays & Linked Lists", "estimated_hours": 3.0},
        {"unit_name": "Unit 1", "topic_name": "Stacks & Queues", "estimated_hours": 2.5},
        {"unit_name": "Unit 2", "topic_name": "Trees & Binary Search Trees", "estimated_hours": 4.0},
        {"unit_name": "Unit 2", "topic_name": "AVL Trees & Red-Black Trees", "estimated_hours": 5.0},
        {"unit_name": "Unit 3", "topic_name": "Graph Algorithms (BFS, DFS)", "estimated_hours": 4.5},
        {"unit_name": "Unit 3", "topic_name": "Shortest Path Algorithms", "estimated_hours": 4.0},
        {"unit_name": "Unit 4", "topic_name": "Sorting Algorithms", "estimated_hours": 3.0},
        {"unit_name": "Unit 4", "topic_name": "Dynamic Programming", "estimated_hours": 6.0},
        {"unit_name": "Unit 5", "topic_name": "Greedy Algorithms", "estimated_hours": 3.5},
        {"unit_name": "Unit 5", "topic_name": "Hashing & Hash Tables", "estimated_hours": 2.5},
    ],
    "Database Management Systems": [
        {"unit_name": "Unit 1", "topic_name": "ER Model & Relational Model", "estimated_hours": 3.0},
        {"unit_name": "Unit 1", "topic_name": "SQL Fundamentals", "estimated_hours": 2.0},
        {"unit_name": "Unit 2", "topic_name": "Normalization (1NF-BCNF)", "estimated_hours": 4.0},
        {"unit_name": "Unit 2", "topic_name": "Relational Algebra", "estimated_hours": 3.5},
        {"unit_name": "Unit 3", "topic_name": "Transaction Management", "estimated_hours": 3.5},
        {"unit_name": "Unit 3", "topic_name": "Concurrency Control", "estimated_hours": 4.0},
        {"unit_name": "Unit 4", "topic_name": "Indexing & B+ Trees", "estimated_hours": 3.0},
        {"unit_name": "Unit 4", "topic_name": "Query Optimization", "estimated_hours": 3.5},
    ],
    "Operating Systems": [
        {"unit_name": "Unit 1", "topic_name": "Process Management", "estimated_hours": 3.0},
        {"unit_name": "Unit 1", "topic_name": "CPU Scheduling Algorithms", "estimated_hours": 4.0},
        {"unit_name": "Unit 2", "topic_name": "Process Synchronization", "estimated_hours": 4.5},
        {"unit_name": "Unit 2", "topic_name": "Deadlocks", "estimated_hours": 3.5},
        {"unit_name": "Unit 3", "topic_name": "Memory Management", "estimated_hours": 4.0},
        {"unit_name": "Unit 3", "topic_name": "Virtual Memory & Paging", "estimated_hours": 5.0},
        {"unit_name": "Unit 4", "topic_name": "File Systems", "estimated_hours": 2.5},
        {"unit_name": "Unit 4", "topic_name": "Disk Scheduling", "estimated_hours": 2.0},
    ],
    "Computer Networks": [
        {"unit_name": "Unit 1", "topic_name": "OSI & TCP/IP Models", "estimated_hours": 2.5},
        {"unit_name": "Unit 1", "topic_name": "Data Link Layer Protocols", "estimated_hours": 3.0},
        {"unit_name": "Unit 2", "topic_name": "Network Layer & IP Addressing", "estimated_hours": 3.5},
        {"unit_name": "Unit 2", "topic_name": "Routing Algorithms", "estimated_hours": 4.0},
        {"unit_name": "Unit 3", "topic_name": "Transport Layer (TCP/UDP)", "estimated_hours": 3.5},
        {"unit_name": "Unit 3", "topic_name": "Congestion Control", "estimated_hours": 3.0},
        {"unit_name": "Unit 4", "topic_name": "Application Layer Protocols", "estimated_hours": 2.0},
        {"unit_name": "Unit 4", "topic_name": "Network Security Basics", "estimated_hours": 3.0},
    ],
    "Software Engineering": [
        {"unit_name": "Unit 1", "topic_name": "SDLC Models (Waterfall, Agile)", "estimated_hours": 2.0},
        {"unit_name": "Unit 1", "topic_name": "Requirements Engineering", "estimated_hours": 2.5},
        {"unit_name": "Unit 2", "topic_name": "UML Diagrams", "estimated_hours": 3.0},
        {"unit_name": "Unit 2", "topic_name": "Design Patterns", "estimated_hours": 4.0},
        {"unit_name": "Unit 3", "topic_name": "Testing Strategies", "estimated_hours": 3.0},
        {"unit_name": "Unit 3", "topic_name": "Software Quality Assurance", "estimated_hours": 2.5},
        {"unit_name": "Unit 4", "topic_name": "Project Management", "estimated_hours": 2.0},
        {"unit_name": "Unit 4", "topic_name": "Risk Management", "estimated_hours": 2.0},
    ],
}

# ─── Demo Difficulty Scores ──────────────────────────────────────────
DEMO_DIFFICULTIES = {
    "Arrays & Linked Lists": ("easy", 3.0, 0.9, "Basic data structures with straightforward operations"),
    "Stacks & Queues": ("easy", 2.5, 0.9, "Simple LIFO/FIFO structures"),
    "Trees & Binary Search Trees": ("medium", 5.5, 0.8, "Requires understanding of recursive structures"),
    "AVL Trees & Red-Black Trees": ("hard", 8.5, 0.85, "Complex balancing algorithms with rotation cases"),
    "Graph Algorithms (BFS, DFS)": ("medium", 6.0, 0.8, "Moderate — need to understand traversal strategies"),
    "Shortest Path Algorithms": ("hard", 7.5, 0.75, "Dijkstra, Bellman-Ford require mathematical reasoning"),
    "Sorting Algorithms": ("medium", 5.0, 0.9, "Multiple algorithms to compare and analyze complexity"),
    "Dynamic Programming": ("hard", 9.0, 0.9, "Requires strong problem decomposition & memoization skills"),
    "Greedy Algorithms": ("medium", 5.5, 0.8, "Moderate — proof of optimality can be tricky"),
    "Hashing & Hash Tables": ("easy", 3.5, 0.85, "Collision handling is straightforward in most cases"),
    "ER Model & Relational Model": ("easy", 2.5, 0.9, "Foundational concepts"),
    "SQL Fundamentals": ("easy", 2.0, 0.95, "Practical and widely practiced"),
    "Normalization (1NF-BCNF)": ("hard", 7.0, 0.8, "Functional dependencies and decomposition are abstract"),
    "Relational Algebra": ("medium", 6.0, 0.75, "Formal notation can be challenging"),
    "Transaction Management": ("medium", 5.5, 0.8, "ACID properties with practical scenarios"),
    "Concurrency Control": ("hard", 7.5, 0.7, "Lock protocols and deadlock detection are complex"),
    "Indexing & B+ Trees": ("medium", 5.0, 0.85, "Tree-based indexing with insertion/deletion"),
    "Query Optimization": ("medium", 6.0, 0.75, "Requires understanding of cost models"),
    "Process Management": ("easy", 3.0, 0.9, "Basic OS concepts"),
    "CPU Scheduling Algorithms": ("medium", 5.5, 0.85, "Multiple algorithms with different behaviors"),
    "Process Synchronization": ("hard", 7.5, 0.8, "Semaphores, monitors — classical concurrency problems"),
    "Deadlocks": ("medium", 6.0, 0.85, "Detection and avoidance algorithms"),
    "Memory Management": ("medium", 5.5, 0.8, "Paging, segmentation concepts"),
    "Virtual Memory & Paging": ("hard", 8.0, 0.75, "Page replacement algorithms and TLB management"),
    "File Systems": ("easy", 3.0, 0.9, "Descriptive topic"),
    "Disk Scheduling": ("easy", 3.5, 0.9, "Algorithmic but straightforward"),
    "OSI & TCP/IP Models": ("easy", 2.0, 0.95, "Memorization-heavy, conceptual"),
    "Data Link Layer Protocols": ("medium", 5.0, 0.8, "Framing, error detection, flow control"),
    "Network Layer & IP Addressing": ("medium", 6.0, 0.8, "Subnetting requires practice"),
    "Routing Algorithms": ("hard", 7.0, 0.75, "Dijkstra and distance-vector in network context"),
    "Transport Layer (TCP/UDP)": ("medium", 5.5, 0.8, "Handshake, reliability mechanisms"),
    "Congestion Control": ("hard", 7.0, 0.7, "Window-based algorithms, AIMD"),
    "Application Layer Protocols": ("easy", 2.5, 0.9, "HTTP, DNS, SMTP are practical"),
    "Network Security Basics": ("medium", 4.5, 0.8, "Encryption fundamentals, firewalls"),
    "SDLC Models (Waterfall, Agile)": ("easy", 2.0, 0.95, "Descriptive, comparison-based"),
    "Requirements Engineering": ("easy", 2.5, 0.9, "SRS documentation"),
    "UML Diagrams": ("medium", 4.5, 0.85, "Multiple diagram types to master"),
    "Design Patterns": ("hard", 7.0, 0.75, "Abstract OOP patterns require deep understanding"),
    "Testing Strategies": ("medium", 4.0, 0.85, "Black-box, white-box, integration testing"),
    "Software Quality Assurance": ("easy", 3.0, 0.9, "Standards and process-oriented"),
    "Project Management": ("easy", 2.5, 0.9, "CPM, PERT — straightforward"),
    "Risk Management": ("easy", 2.0, 0.9, "Identification and mitigation strategies"),
}

# ─── Demo Exam Schedule ──────────────────────────────────────────────
DEMO_EXAMS = [
    {"subject": "Data Structures & Algorithms", "exam_date": "2026-04-15", "exam_time": "09:00", "duration_min": 180},
    {"subject": "Database Management Systems", "exam_date": "2026-04-18", "exam_time": "09:00", "duration_min": 180},
    {"subject": "Operating Systems", "exam_date": "2026-04-21", "exam_time": "14:00", "duration_min": 180},
    {"subject": "Computer Networks", "exam_date": "2026-04-24", "exam_time": "09:00", "duration_min": 180},
    {"subject": "Software Engineering", "exam_date": "2026-04-27", "exam_time": "14:00", "duration_min": 180},
]

# ─── Demo Test Scores ────────────────────────────────────────────────
DEMO_SCORES = [
    {"subject": "Data Structures & Algorithms", "test_type": "cie1", "score": 32, "max_score": 50, "test_date": "2026-02-15"},
    {"subject": "Database Management Systems", "test_type": "cie1", "score": 38, "max_score": 50, "test_date": "2026-02-15"},
    {"subject": "Operating Systems", "test_type": "cie1", "score": 28, "max_score": 50, "test_date": "2026-02-16"},
    {"subject": "Computer Networks", "test_type": "cie1", "score": 25, "max_score": 50, "test_date": "2026-02-16"},
    {"subject": "Software Engineering", "test_type": "cie1", "score": 40, "max_score": 50, "test_date": "2026-02-17"},
]

# ─── Demo Availability ───────────────────────────────────────────────
DEMO_AVAILABILITY = [
    {"day_of_week": "Monday", "start_time": "06:00", "end_time": "08:00", "is_peak": 1, "energy_level": "high"},
    {"day_of_week": "Monday", "start_time": "17:00", "end_time": "20:00", "is_peak": 0, "energy_level": "medium"},
    {"day_of_week": "Tuesday", "start_time": "06:00", "end_time": "08:00", "is_peak": 1, "energy_level": "high"},
    {"day_of_week": "Tuesday", "start_time": "17:00", "end_time": "20:00", "is_peak": 0, "energy_level": "medium"},
    {"day_of_week": "Wednesday", "start_time": "06:00", "end_time": "08:00", "is_peak": 1, "energy_level": "high"},
    {"day_of_week": "Wednesday", "start_time": "17:00", "end_time": "21:00", "is_peak": 0, "energy_level": "medium"},
    {"day_of_week": "Thursday", "start_time": "06:00", "end_time": "08:00", "is_peak": 1, "energy_level": "high"},
    {"day_of_week": "Thursday", "start_time": "17:00", "end_time": "20:00", "is_peak": 0, "energy_level": "medium"},
    {"day_of_week": "Friday", "start_time": "06:00", "end_time": "08:00", "is_peak": 1, "energy_level": "high"},
    {"day_of_week": "Friday", "start_time": "15:00", "end_time": "21:00", "is_peak": 0, "energy_level": "medium"},
    {"day_of_week": "Saturday", "start_time": "08:00", "end_time": "12:00", "is_peak": 1, "energy_level": "high"},
    {"day_of_week": "Saturday", "start_time": "14:00", "end_time": "20:00", "is_peak": 0, "energy_level": "medium"},
    {"day_of_week": "Sunday", "start_time": "09:00", "end_time": "12:00", "is_peak": 1, "energy_level": "high"},
    {"day_of_week": "Sunday", "start_time": "15:00", "end_time": "19:00", "is_peak": 0, "energy_level": "low"},
]


def seed_all():
    """Seed the database with demo data. Returns (subjects, topics, difficulties) counts."""
    from db.database import (
        get_connection, add_subject, add_topic, add_difficulty_score,
        add_exam, add_test_score, add_availability, clear_availability, get_all_subjects,
    )

    # Check if already seeded
    existing = get_all_subjects()
    if len(existing) >= len(DEMO_SUBJECTS):
        return 0, 0, 0

    subject_map = {}
    topic_count = 0
    diff_count = 0

    # Seed subjects
    for s in DEMO_SUBJECTS:
        sid = add_subject(s["name"], s["code"], s["credits"], s["semester"], s["self_rating"])
        subject_map[s["name"]] = sid

    # Seed topics + difficulties
    for subject_name, topics in DEMO_TOPICS.items():
        sid = subject_map.get(subject_name)
        if not sid:
            continue
        for t in topics:
            tid = add_topic(sid, t["topic_name"], t["unit_name"], "", t["estimated_hours"])
            topic_count += 1

            # Add difficulty
            diff = DEMO_DIFFICULTIES.get(t["topic_name"])
            if diff:
                add_difficulty_score(tid, diff[0], diff[1], diff[2], diff[3])
                diff_count += 1

    # Seed exams with future dates
    from datetime import date, timedelta
    today = date.today()
    demo_offsets = [15, 18, 21, 24, 27]
    for idx, e in enumerate(DEMO_EXAMS):
        sid = subject_map.get(e["subject"])
        if sid:
            future_date = (today + timedelta(days=demo_offsets[idx % len(demo_offsets)])).strftime("%Y-%m-%d")
            add_exam(sid, future_date, e["exam_time"], e["duration_min"])

    # Seed test scores
    for ts in DEMO_SCORES:
        sid = subject_map.get(ts["subject"])
        if sid:
            add_test_score(sid, ts["score"], ts["max_score"], ts["test_type"], ts["test_date"])

    # Seed availability
    clear_availability()
    for a in DEMO_AVAILABILITY:
        add_availability(a["day_of_week"], a["start_time"], a["end_time"], a["is_peak"], a["energy_level"])

    return len(DEMO_SUBJECTS), topic_count, diff_count
