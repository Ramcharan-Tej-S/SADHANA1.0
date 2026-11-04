# agents/feedback_loop_agent.py — Continuous Learning Refinement
"""
Pattern: Continuous learning feedback loop
Compares predictions vs actuals, refines the model over time.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_llm, extract_json_safe


def analyze_prediction_accuracy(performance_history: list) -> dict:
    """
    Analyze how accurate past predictions have been.

    Args:
        performance_history: list of {"subject_name": str, "predicted_score": float,
                                      "actual_score": float, "readiness_score": float, "logged_at": str}

    Returns: {
        "accuracy_summary": str,
        "reasoning": str,
        "subject_accuracy": [
            {"subject": str, "avg_error": float, "bias": str, "trend": str}
        ],
        "model_adjustments": [str],
        "study_tips": [str]
    }
    """
    # Filter entries with both predicted and actual scores
    paired = [h for h in performance_history if h.get("actual_score") is not None and h.get("predicted_score")]

    if not paired:
        return {
            "accuracy_summary": "No prediction-actual pairs available yet.",
            "reasoning": "Need at least one exam result to compare predictions.",
            "subject_accuracy": [],
            "model_adjustments": [],
            "study_tips": ["Keep logging your test scores to improve predictions."],
        }

    # Calculate errors
    summary_lines = []
    for h in paired:
        error = abs(h["predicted_score"] - h["actual_score"])
        direction = "over" if h["predicted_score"] > h["actual_score"] else "under"
        summary_lines.append(
            f"  {h['subject_name']}: Predicted {h['predicted_score']:.1f}%, "
            f"Actual {h['actual_score']:.1f}%, Error: {error:.1f}% ({direction}-predicted)"
        )

    llm = get_llm(temperature=0.2, max_tokens=2000, json_mode=True)

    prompt = f"""You are a learning analytics expert. Analyze prediction accuracy and suggest model improvements.

PREDICTION vs ACTUAL RESULTS:
{chr(10).join(summary_lines)}

ANALYSIS INSTRUCTIONS:
1. Calculate average prediction error per subject.
2. Identify if the model tends to over-predict or under-predict.
3. Suggest what factors might be causing errors.
4. Provide specific study tips based on where predictions were wrong.
5. Suggest how the study plan should be adjusted.

Return JSON:
{{
    "accuracy_summary": "Overall accuracy assessment",
    "reasoning": "Step-by-step analysis",
    "subject_accuracy": [
        {{
            "subject": "Subject Name",
            "avg_error": 5.0,
            "bias": "over-predicted|under-predicted|accurate",
            "trend": "improving|declining|stable"
        }}
    ],
    "model_adjustments": [
        "Specific suggestion for model improvement"
    ],
    "study_tips": [
        "Practical study tip based on analysis"
    ]
}}"""

    try:
        response = llm.invoke(prompt)
        return extract_json_safe(response.content)
    except Exception:
        return _fallback_accuracy(paired)


def _fallback_accuracy(paired):
    """Simple mathematical accuracy analysis."""
    subject_errors = {}
    for h in paired:
        name = h["subject_name"]
        error = h["predicted_score"] - h["actual_score"]
        subject_errors.setdefault(name, []).append(error)

    accuracy = []
    for subj, errors in subject_errors.items():
        avg_err = sum(abs(e) for e in errors) / len(errors)
        avg_signed = sum(errors) / len(errors)
        bias = "over-predicted" if avg_signed > 2 else "under-predicted" if avg_signed < -2 else "accurate"
        accuracy.append({
            "subject": subj,
            "avg_error": round(avg_err, 1),
            "bias": bias,
            "trend": "stable",
        })

    return {
        "accuracy_summary": f"Average prediction error across subjects: {sum(a['avg_error'] for a in accuracy) / len(accuracy):.1f}%",
        "reasoning": "Mathematical error calculation (LLM unavailable)",
        "subject_accuracy": accuracy,
        "model_adjustments": ["Increase study time for under-predicted subjects"],
        "study_tips": ["Focus on subjects where prediction was over-optimistic"],
    }


def generate_improvement_suggestions(performance_history: list, current_plan: list) -> dict:
    """Generate personalized improvement suggestions based on learning history."""
    llm = get_llm(temperature=0.3, max_tokens=1500, json_mode=True)

    # Summarize history
    history_lines = []
    for h in performance_history[-10:]:
        history_lines.append(
            f"  {h.get('subject_name', 'Unknown')}: Readiness={h.get('readiness_score', 0):.0f}%, "
            f"Coverage={h.get('coverage_pct', 0):.0f}%"
        )

    prompt = f"""You are a personalized study coach. Based on the student's learning history, provide improvement suggestions.

RECENT PERFORMANCE:
{chr(10).join(history_lines) if history_lines else "No history yet"}

CURRENT PLAN: {len(current_plan)} sessions scheduled

Provide 5-7 actionable study tips personalized to this student's performance.

Return JSON:
{{
    "suggestions": [
        {{
            "tip": "Actionable study tip",
            "category": "time_management|technique|focus|revision|motivation",
            "impact": "high|medium|low"
        }}
    ],
    "overall_assessment": "Brief assessment of student's study approach"
}}"""

    try:
        response = llm.invoke(prompt)
        return extract_json_safe(response.content)
    except Exception:
        return {
            "suggestions": [
                {"tip": "Study hard topics during your peak focus hours", "category": "time_management", "impact": "high"},
                {"tip": "Use active recall instead of passive reading", "category": "technique", "impact": "high"},
                {"tip": "Review completed topics weekly for retention", "category": "revision", "impact": "medium"},
                {"tip": "Take short breaks (Pomodoro: 25 min study, 5 min break)", "category": "focus", "impact": "medium"},
                {"tip": "Solve previous year question papers for practice", "category": "technique", "impact": "high"},
            ],
            "overall_assessment": "Keep maintaining a consistent study schedule.",
        }
