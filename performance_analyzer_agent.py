# agents/performance_analyzer_agent.py — Test Performance Analysis
"""
Pattern: Adaptive re-calibration
Analyzes test scores to identify weak areas and update topic priorities.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_llm, extract_json_safe


def analyze_performance(scores: list, subjects: list, difficulties: dict) -> dict:
    """
    Analyze test performance and re-calibrate topic priorities.

    Args:
        scores: list of {"subject_name": str, "test_type": str, "score": float, "max_score": float}
        subjects: list of subject dicts with self_rating
        difficulties: {topic_name: {"level": str, "score": float}}

    Returns: {
        "analysis_summary": str,
        "reasoning": str,
        "subject_analysis": [
            {
                "subject": str,
                "score_pct": float,
                "performance_level": str,
                "weak_areas": [str],
                "strong_areas": [str],
                "priority_shift": str,
                "new_priority_score": float
            }
        ],
        "recommendations": [str]
    }
    """
    # Calculate score percentages
    score_summary = []
    for s in scores:
        pct = (s["score"] / s["max_score"]) * 100 if s["max_score"] > 0 else 0
        score_summary.append(f"  {s['subject_name']}: {s['score']}/{s['max_score']} ({pct:.1f}%) — {s['test_type']}")

    # Include difficulty context
    diff_summary = []
    for topic, d in difficulties.items():
        diff_summary.append(f"  {topic}: {d.get('level', 'medium')} (score: {d.get('score', 5)}/10)")

    llm = get_llm(temperature=0.2, max_tokens=3000, json_mode=True)

    prompt = f"""You are an academic performance analyst. Analyze test results and identify areas needing improvement.

TEST SCORES:
{chr(10).join(score_summary)}

TOPIC DIFFICULTY CONTEXT:
{chr(10).join(diff_summary[:30])}

ANALYSIS INSTRUCTIONS:
1. Compare scores against expected performance.
2. Subjects scoring below 60% need HIGH priority.
3. Subjects scoring 60-75% need MEDIUM priority.
4. Subjects above 75% can have REDUCED priority.
5. Cross-reference with topic difficulty — low score + hard topics = critical focus area.
6. Identify surprising results (high score on hard topics, low score on easy ones).

Return JSON:
{{
    "analysis_summary": "Brief overall performance summary",
    "reasoning": "Step-by-step analysis thought process",
    "subject_analysis": [
        {{
            "subject": "Subject Name",
            "score_pct": 64.0,
            "performance_level": "below_average|average|above_average|excellent",
            "weak_areas": ["Topic 1", "Topic 2"],
            "strong_areas": ["Topic 3"],
            "priority_shift": "increase|maintain|decrease",
            "new_priority_score": 8.0,
            "focus_recommendation": "Specific advice for improvement"
        }}
    ],
    "recommendations": [
        "Overall recommendation 1",
        "Overall recommendation 2"
    ]
}}"""

    try:
        response = llm.invoke(prompt)
        return extract_json_safe(response.content)
    except Exception as e:
        return _fallback_analysis(scores)


def _fallback_analysis(scores):
    """Simple mathematical fallback analysis."""
    analysis = []
    for s in scores:
        pct = (s["score"] / s["max_score"]) * 100 if s["max_score"] > 0 else 0
        if pct < 60:
            level = "below_average"
            shift = "increase"
            priority = 9.0
        elif pct < 75:
            level = "average"
            shift = "maintain"
            priority = 6.0
        else:
            level = "above_average"
            shift = "decrease"
            priority = 4.0

        analysis.append({
            "subject": s["subject_name"],
            "score_pct": round(pct, 1),
            "performance_level": level,
            "weak_areas": [],
            "strong_areas": [],
            "priority_shift": shift,
            "new_priority_score": priority,
            "focus_recommendation": f"{'Focus heavily on this subject' if pct < 60 else 'Maintain current pace'}",
        })

    return {
        "analysis_summary": "Fallback analysis based on score percentages",
        "reasoning": "LLM unavailable, using mathematical thresholds",
        "subject_analysis": analysis,
        "recommendations": ["Review weak subjects first", "Maintain strong subjects with periodic revision"],
    }


def update_priorities_from_analysis(analysis: dict, subject_map: dict):
    """Save updated performance data after analysis."""
    from db.database import add_performance_log

    saved = 0
    for sa in analysis.get("subject_analysis", []):
        sid = subject_map.get(sa.get("subject"))
        if sid:
            add_performance_log(
                subject_id=sid,
                readiness_score=sa.get("new_priority_score", 5.0) * 10,
                predicted_score=sa.get("score_pct", 0),
                coverage_pct=0.0,
                reasoning=sa.get("focus_recommendation", ""),
            )
            saved += 1
    return saved
