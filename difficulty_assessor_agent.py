# agents/difficulty_assessor_agent.py — Topic Difficulty Estimation
"""
Pattern: LLM-as-Judge (3-pass scoring)
1. Initial assessment → 2. Critique → 3. Calibrated final score
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_llm, extract_json_safe


BATCH_SIZE = 25  # Assess in batches of up to 25 topics so 100+ topics never truncate


def _assess_difficulty_batch(topics: list, subject_name: str = "") -> list:
    """Assess a single batch of topics using 3-pass LLM-as-Judge."""
    if not topics:
        return []

    topic_items = []
    for i, t in enumerate(topics):
        tid = t.get("topic_id", t.get("id", i + 1))
        name = t.get("topic_name", "")
        unit = t.get("unit_name", "")
        desc = t.get("description", "")
        topic_items.append(f"  - [ID: {tid}] {name} (Unit: {unit}): {desc}")
    topic_list = "\n".join(topic_items)

    llm = get_llm(temperature=0.2, max_tokens=6000, json_mode=True)

    # ─── Pass 1: Initial Assessment ──────────────────────────────
    pass1_prompt = f"""You are an academic difficulty assessor for {subject_name or 'a university course'}.

TOPICS:
{topic_list}

For each topic, assess its difficulty on a scale of 1-10 considering concept abstraction, mathematical complexity, prerequisite depth, and common student struggles. Keep factors concise (1 sentence).

Return JSON in this exact structure:
{{
    "assessments": [
        {{
            "topic_id": 1,
            "topic_name": "Exact topic name",
            "initial_score": 5.0,
            "initial_level": "easy|medium|hard",
            "factors": "Brief 1-sentence explanation of difficulty factors"
        }}
    ]
}}"""

    try:
        pass1_response = llm.invoke(pass1_prompt)
        pass1 = extract_json_safe(pass1_response.content)
    except Exception:
        # Fallback: assign medium difficulty
        return [
            {"topic_id": t.get("topic_id", t.get("id")), "topic_name": t.get("topic_name", ""), "level": "medium", "score": 5.0, "confidence": 0.3, "reasoning": "Default assessment"}
            for t in topics
        ]

    # ─── Pass 2: Critique ────────────────────────────────────────
    pass2_prompt = f"""You are a critical reviewer of academic difficulty assessments for {subject_name or 'a university course'}.

Here is an initial difficulty assessment:
{json.dumps(pass1.get('assessments', []), indent=2)}

CRITIQUE INSTRUCTIONS:
1. Check if any topics are rated too high or too low.
2. Consider relative difficulty between topics.
3. Suggest adjustments with brief reasoning.

Return JSON:
{{
    "critique": "Overall critique of the assessment",
    "adjustments": [
        {{
            "topic_id": 1,
            "topic_name": "Exact topic name",
            "original_score": 5.0,
            "suggested_score": 6.0,
            "reason": "Why this should be adjusted"
        }}
    ]
}}"""

    try:
        pass2_response = llm.invoke(pass2_prompt)
        pass2 = extract_json_safe(pass2_response.content)
    except Exception:
        pass2 = {"critique": "Critique unavailable", "adjustments": []}

    # ─── Pass 3: Final Synthesis ─────────────────────────────────
    pass3_prompt = f"""You are the final calibrator for academic topic difficulty scores for {subject_name or 'a university course'}.

INITIAL ASSESSMENT:
{json.dumps(pass1.get('assessments', []), indent=2)}

CRITIQUE & ADJUSTMENTS:
{json.dumps(pass2, indent=2)}

INSTRUCTIONS:
1. Synthesize the initial assessment and critique.
2. Produce final calibrated scores (1.0 to 10.0).
3. Assign difficulty level: easy (1.0-3.5), medium (3.6-6.5), hard (6.6-10.0).
4. Provide confidence score (0.0-1.0). Keep reasoning concise (1 sentence).

Return JSON:
{{
    "results": [
        {{
            "topic_id": 1,
            "topic_name": "Exact topic name",
            "score": 5.0,
            "level": "easy|medium|hard",
            "confidence": 0.85,
            "reasoning": "Final reasoning combining initial assessment and critique"
        }}
    ]
}}"""

    try:
        pass3_response = llm.invoke(pass3_prompt)
        pass3 = extract_json_safe(pass3_response.content)
        results = pass3.get("results", [])
        if results:
            return results
    except Exception:
        pass

    # Fallback to pass 1 results
    return [
        {
            "topic_id": a.get("topic_id"),
            "topic_name": a.get("topic_name", ""),
            "level": a.get("initial_level", "medium"),
            "score": a.get("initial_score", 5.0),
            "confidence": 0.6,
            "reasoning": a.get("factors", "Initial assessment only"),
        }
        for a in pass1.get("assessments", [])
    ]


def assess_difficulty(topics: list, subject_name: str = "") -> list:
    """
    Assess difficulty for all topics, automatically batching in chunks of 25
    so that 100+ topics are evaluated completely without hitting token limits.
    """
    if not topics:
        return []

    if len(topics) <= BATCH_SIZE:
        return _assess_difficulty_batch(topics, subject_name)

    all_results = []
    for i in range(0, len(topics), BATCH_SIZE):
        batch = topics[i : i + BATCH_SIZE]
        batch_results = _assess_difficulty_batch(batch, subject_name)
        all_results.extend(batch_results)

    return all_results


def save_difficulty_results(results: list, topic_map: dict, topic_list: list = None):
    """
    Save difficulty assessment results to database.
    topic_map: dict of {topic_name: topic_id}
    topic_list: optional list of original topic dicts [{"id": int, "topic_name": str}]
    """
    from db.database import add_difficulty_score

    saved = 0
    assigned_topic_ids = set()

    for idx, r in enumerate(results):
        topic_id = None

        # 1. Try by direct topic_id in result
        if r.get("topic_id"):
            try:
                candidate_id = int(r.get("topic_id"))
                if topic_list and any(t["id"] == candidate_id for t in topic_list):
                    topic_id = candidate_id
            except (ValueError, TypeError):
                pass

        # 2. Try exact name match
        name = r.get("topic_name", "")
        if not topic_id and name in topic_map:
            topic_id = topic_map[name]

        # 3. Try case-insensitive or substring match
        if not topic_id:
            name_lower = name.lower()
            for orig_name, tid in topic_map.items():
                if orig_name.lower() in name_lower or name_lower in orig_name.lower():
                    topic_id = tid
                    break

        # 4. Fallback: match by index if counts align
        if not topic_id and topic_list and idx < len(topic_list):
            if topic_list[idx]["id"] not in assigned_topic_ids:
                topic_id = topic_list[idx]["id"]

        if topic_id:
            assigned_topic_ids.add(topic_id)
            add_difficulty_score(
                topic_id=topic_id,
                level=r.get("level", "medium").lower(),
                score=float(r.get("score", 5.0)),
                confidence=float(r.get("confidence", 0.7)),
                reasoning=r.get("reasoning", ""),
            )
            saved += 1

    return saved
