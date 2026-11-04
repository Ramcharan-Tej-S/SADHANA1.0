# agents/adaptive_tutor_agent.py — ADHD-Inclusive Adaptive Study Tutor
"""
Pattern: High-Grasp Cognitive Scaffolding
Compresses academic syllabus topics into clear, digestible, neuro-inclusive formats:
- Intuition Anchors (why does this exist? what problem does it solve?)
- Everyday Physical Analogies
- Clean ASCII/Text Flowcharts and Mental Models
- Jargon-free Key Mechanisms (3-4 bullet takeaways)
- Low-stakes Intuition Checkpoint Question
- Socratic Quick Help
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_llm, extract_json_safe


def compress_study_material(subject_name: str, topic_name: str, notes: str = "", uploaded_materials: str = "") -> dict:
    """
    Compress a subject topic into a high-retention, ADHD-friendly learning scroll.
    Returns:
    {
        "subject": str,
        "topic": str,
        "intuition": str,
        "analogy": str,
        "visual_diagram": str,
        "key_takeaways": [str],
        "checkpoint": {
            "question": str,
            "options": [str],
            "correct_index": int,
            "explanation": str
        }
    }
    """
    context = f"Subject: {subject_name}\nTopic: {topic_name}"
    if notes:
        context += f"\nContext/Notes: {notes}"
    if uploaded_materials:
        context += f"\n\nSTUDENT'S UPLOADED CLASS & HANDWRITTEN NOTES:\n\"\"\"\n{uploaded_materials[:3200]}\n\"\"\"\n(CRITICAL INSTRUCTION: Base your intuition, explanations, formulas, and terminology directly on the student's uploaded class notes above!)"

    prompt = f"""You are an elite, neuro-inclusive university tutor specializing in ADHD cognitive ergonomics.
Your mission is to decompress and illuminate the following academic topic so that a student with ADHD can grasp the core intuition in under 2 minutes without feeling overwhelmed or bored.

{context}

RULES FOR ADHD COGNITIVE ERGONOMICS:
1. ZERO FLUFF OR ACADEMIC PRETENSION: Avoid long preambles, buzzwords, or textbook filler.
2. INTUITION FIRST: Answer "What real-world problem does this solve and why did humans invent it?" in 1-2 sharp sentences.
3. PHYSICAL ANALOGY: Provide a concrete, everyday analogy (e.g. plumbing, traffic, cooking, split dictionaries, post office).
4. VISUAL MENTAL MODEL: Provide a clean, readable ASCII text diagram (using boxes [+---+], arrows [-->], and clean spacing) illustrating the flow or structure. Keep it under 15 lines.
5. 3-4 KEY TAKEAWAYS: Razor-sharp bullets explaining how it works mechanically.
6. LOW-STAKES CHECKPOINT: Exactly 1 friendly multiple-choice question testing the core intuition (not rote memorization). Include 3 options, the correct 0-based index, and an encouraging explanation.

Return ONLY valid JSON in this exact structure:
{{
    "subject": "{subject_name}",
    "topic": "{topic_name}",
    "intuition": "1-2 sentence core reason why this concept exists and what problem it solves.",
    "analogy": "Concrete everyday physical metaphor explaining how it works.",
    "visual_diagram": "+-----------------+\\n|    Component    | --> [ Flow Step ]\\n+-----------------+",
    "key_takeaways": [
        "First fundamental principle or mechanism",
        "Second key operational rule",
        "Common gotcha or practical advantage"
    ],
    "checkpoint": {{
        "question": "Friendly intuition check question?",
        "options": [
            "Option A description",
            "Option B description",
            "Option C description"
        ],
        "correct_index": 0,
        "explanation": "Affirmative, clear explanation of why this option is correct."
    }}
}}"""

    try:
        llm = get_llm(temperature=0.2, max_tokens=2500, json_mode=True)
        response = llm.invoke(prompt)
        result = extract_json_safe(response.content)

        # Validate required keys
        if "intuition" in result and "key_takeaways" in result:
            result.setdefault("subject", subject_name)
            result.setdefault("topic", topic_name)
            result["has_uploaded_notes"] = bool(uploaded_materials)
            return result
    except Exception as exc:
        pass

    return _fallback_compressed_material(subject_name, topic_name, notes)


def ask_tutor(subject_name: str, topic_name: str, question: str) -> dict:
    """Answer a student's question during their focus session in concise, ADHD-friendly terms."""
    prompt = f"""You are a warm, encouraging, ADHD-friendly tutor helping a university student in the middle of a focused study sprint.

SUBJECT: {subject_name}
TOPIC: {topic_name}
STUDENT QUESTION: {question}

INSTRUCTIONS:
1. Maximum 70 words.
2. Be direct, clear, and reassuring.
3. Use a quick analogy or bulleted steps if helpful.
4. Conclude with a quick 1-sentence confidence booster.

Return JSON:
{{
    "reply": "Your concise, empowering answer here"
}}"""

    try:
        llm = get_llm(temperature=0.3, max_tokens=600, json_mode=True)
        response = llm.invoke(prompt)
        res = extract_json_safe(response.content)
        if "reply" in res:
            return res
    except Exception:
        pass

    return {
        "reply": f"Think of {topic_name} as a structured rule set: break it down into inputs, transformations, and outputs. You've got this—one step at a time!"
    }


def _fallback_compressed_material(subject_name: str, topic_name: str, notes: str = "") -> dict:
    """High-quality procedural fallback when offline or LLM unavailable."""
    return {
        "subject": subject_name,
        "topic": topic_name,
        "intuition": f"{topic_name} exists to solve a core problem in {subject_name}: organizing information systematically so systems can process, scale, and verify work without errors.",
        "analogy": "Think of it like a train dispatch station: every car has a verified ticket and a designated track, so collisions are prevented even when traffic is heavy.",
        "visual_diagram": (
            "+-----------------------------------------+\n"
            f"| INPUT: Raw Data / Request               |\n"
            "+-----------------------------------------+\n"
            "                   |\n"
            "                   v\n"
            f"+-----------------------------------------+\n"
            f"| PROCESS: {topic_name[:30]:<30} |\n"
            "+-----------------------------------------+\n"
            "                   |\n"
            "                   v\n"
            "+-----------------------------------------+\n"
            "| OUTPUT: Verified, Structured Result     |\n"
            "+-----------------------------------------+"
        ),
        "key_takeaways": [
            f"Core purpose: Ensures reliable state and behavior in {subject_name}.",
            "Modular design: Decouples the work into predictable, repeatable steps.",
            "Verification: Always checks conditions before committing or progressing.",
            "Practical edge: Minimizes memory, round-trips, and computational bottlenecks."
        ],
        "checkpoint": {
            "question": f"What is the primary objective of applying {topic_name}?",
            "options": [
                "To structure and streamline data/operations reliably",
                "To increase randomness and bypass all system checks",
                "To store redundant copies without ever verifying them"
            ],
            "correct_index": 0,
            "explanation": "Exactly! The whole purpose is predictable, structured reliability."
        }
    }

