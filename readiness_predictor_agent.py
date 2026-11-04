# agents/readiness_predictor_agent.py — Exam Readiness Scoring
"""
Pattern: Score prediction with Chain-of-Thought reasoning
Aggregates study progress, difficulty, and test scores to predict exam readiness.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_llm, extract_json_safe


def predict_readiness(subject_name: str, topics: list, difficulties: dict,
                      sessions: list, scores: list, exam_date: str = "") -> dict:
    """
    Predict exam readiness for a subject.

    Returns: {
        "readiness_score": float (0-100),
        "confidence": float (0-1),
        "reasoning": str,
        "coverage_pct": float,
        "critical_gaps": [str],
        "strengths": [str],
        "prediction": str
    }
    """
    # Calculate coverage
    total_topics = len(topics)
    completed_sessions = [s for s in sessions if s.get("status") == "completed"]
    covered_topics = set(s.get("topic_name") for s in completed_sessions if s.get("topic_name"))
    coverage_pct = (len(covered_topics) / total_topics * 100) if total_topics > 0 else 0

    # Score summary
    score_avg = 0
    if scores:
        pcts = [(s["score"] / s["max_score"]) * 100 for s in scores if s.get("max_score", 0) > 0]
        score_avg = sum(pcts) / len(pcts) if pcts else 0

    # Difficulty context
    hard_topics = [t["topic_name"] for t in topics if difficulties.get(t["topic_name"], {}).get("level") == "hard"]
    uncovered_hard = [t for t in hard_topics if t not in covered_topics]

    # Session stats
    total_planned = len(sessions)
    total_completed = len(completed_sessions)
    completion_rate = (total_completed / total_planned * 100) if total_planned > 0 else 0

    llm = get_llm(temperature=0.2, max_tokens=2000, json_mode=True)

    prompt = f"""You are an exam readiness predictor. Assess the student's readiness for the upcoming exam.

SUBJECT: {subject_name}
EXAM DATE: {exam_date or "Not set"}

METRICS:
- Topic Coverage: {coverage_pct:.1f}% ({len(covered_topics)}/{total_topics} topics studied)
- Average Test Score: {score_avg:.1f}%
- Session Completion Rate: {completion_rate:.1f}% ({total_completed}/{total_planned} sessions)
- Uncovered Hard Topics: {', '.join(uncovered_hard) if uncovered_hard else 'None'}
- Total Hard Topics: {len(hard_topics)}

CHAIN-OF-THOUGHT INSTRUCTIONS:
1. Consider topic coverage — are important topics covered?
2. Consider test score trends — improving or declining?
3. Consider difficulty gaps — are hard topics uncovered?
4. Consider time remaining until exam.
5. Synthesize into a readiness score (0-100).

Return JSON:
{{
    "readiness_score": 65.0,
    "confidence": 0.75,
    "reasoning": "Step-by-step reasoning...",
    "coverage_pct": {coverage_pct:.1f},
    "critical_gaps": ["Topic A", "Topic B"],
    "strengths": ["Topic C"],
    "prediction": "brief prediction statement"
}}"""

    try:
        response = llm.invoke(prompt)
        result = extract_json_safe(response.content)
        return result
    except Exception:
        return _fallback_readiness(subject_name, coverage_pct, score_avg, completion_rate, uncovered_hard)


def _fallback_readiness(subject_name, coverage_pct, score_avg, completion_rate, uncovered_hard):
    """Mathematical fallback readiness calculation."""
    # Weighted formula: 40% coverage + 35% scores + 25% completion
    readiness = (coverage_pct * 0.4) + (score_avg * 0.35) + (completion_rate * 0.25)

    # Penalty for uncovered hard topics
    penalty = len(uncovered_hard) * 3
    readiness = max(0, readiness - penalty)

    return {
        "readiness_score": round(readiness, 1),
        "confidence": 0.5,
        "reasoning": f"Mathematical estimate: 40% coverage ({coverage_pct:.0f}%) + 35% scores ({score_avg:.0f}%) + 25% completion ({completion_rate:.0f}%) - {penalty}pt penalty for {len(uncovered_hard)} uncovered hard topics",
        "coverage_pct": coverage_pct,
        "critical_gaps": uncovered_hard,
        "strengths": [],
        "prediction": f"{'On track' if readiness >= 60 else 'Needs more focus'} for {subject_name}",
    }


def predict_all_subjects(subjects: list, topics_by_subject: dict, difficulties: dict,
                         sessions_by_subject: dict, scores_by_subject: dict, exams: dict) -> list:
    """Predict readiness for all subjects."""
    results = []
    for s in subjects:
        name = s["name"]
        result = predict_readiness(
            subject_name=name,
            topics=topics_by_subject.get(name, []),
            difficulties=difficulties,
            sessions=sessions_by_subject.get(name, []),
            scores=scores_by_subject.get(name, []),
            exam_date=exams.get(name, ""),
        )
        result["subject"] = name
        results.append(result)
    return results
