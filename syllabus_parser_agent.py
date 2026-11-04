# agents/syllabus_parser_agent.py — NLP-based Syllabus Extraction
"""
Pattern: Chain-of-Thought extraction
Extracts structured topic data from uploaded syllabus PDFs/TXT files.
"""
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import USE_VISION, get_llm, extract_json_safe


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text content from a PDF file."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception as e:
        return f"Error reading PDF: {e}"


_OCR_ENGINE = None

# Anything larger than this on its long edge is downscaled before OCR or upload.
# Detection cost scales with pixel count and syllabus text stays legible here.
MAX_IMAGE_EDGE = 1600


def _get_ocr_engine():
    """Build the RapidOCR engine once. Kept as the offline fallback for when
    vision is disabled or the configured model cannot read images."""
    global _OCR_ENGINE
    if _OCR_ENGINE is None:
        from rapidocr_onnxruntime import RapidOCR

        _OCR_ENGINE = RapidOCR()
    return _OCR_ENGINE


def _image_data_url(file_path: str) -> str:
    """Read an image as a base64 data URL, downscaling oversized ones."""
    import base64
    import mimetypes

    raw = None
    mime = mimetypes.guess_type(file_path)[0] or "image/png"

    try:
        from PIL import Image

        with Image.open(file_path) as im:
            if max(im.size) > MAX_IMAGE_EDGE:
                im.thumbnail((MAX_IMAGE_EDGE, MAX_IMAGE_EDGE))
                buf = io.BytesIO()
                fmt = "PNG" if im.mode in ("RGBA", "P") else "JPEG"
                im.convert("RGB" if fmt == "JPEG" else im.mode).save(buf, fmt, quality=85)
                raw = buf.getvalue()
                mime = "image/png" if fmt == "PNG" else "image/jpeg"
    except Exception:
        pass  # Pillow missing or the file is odd — send the original bytes

    if raw is None:
        with open(file_path, "rb") as f:
            raw = f.read()

    return f"data:{mime};base64,{base64.b64encode(raw).decode()}"


def _vision_json(file_path: str, prompt: str, max_tokens: int = 8000) -> dict:
    """Ask the multimodal model to read an image and answer in JSON.

    Much faster than local OCR (one network call vs ~15-25s of CPU inference)
    and more accurate, since the model sees the layout rather than a flattened
    line dump.
    """
    from langchain_core.messages import HumanMessage

    llm = get_llm(temperature=0.1, max_tokens=max_tokens, json_mode=True)
    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": _image_data_url(file_path)}},
        ]
    )
    return extract_json_safe(llm.invoke([message]).content)


def is_image(file_path: str) -> bool:
    return os.path.splitext(file_path)[1].lower() in (".png", ".jpg", ".jpeg", ".webp")


def extract_text_from_image(file_path: str) -> str:
    """Extract text from an image using on-device RapidOCR (no API key required, offline & free)."""
    try:
        engine = _get_ocr_engine()
        result, _ = engine(file_path)
        if result:
            text = "\n".join([line[1] for line in result])
            return text.strip()
        else:
            return "No text could be detected in the uploaded image. Please ensure the image is clear."
    except Exception as e:
        return f"Error extracting text from image: {e}"


def extract_text_from_file(file_path: str) -> str:
    """Extract text from PDF, TXT, or Image file."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in (".txt", ".text"):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read().strip()
    elif ext in (".png", ".jpg", ".jpeg"):
        return extract_text_from_image(file_path)
    else:
        return f"Unsupported file type: {ext}"


def parse_syllabus(text: str, subject_name: str = "") -> dict:
    """
    Use LLM to parse syllabus text into structured JSON.
    Returns: {
        "subject_name": str,
        "units": [
            {
                "unit_name": str,
                "topics": [
                    {"topic_name": str, "description": str, "estimated_hours": float}
                ]
            }
        ]
    }
    """
    llm = get_llm(temperature=0.1, max_tokens=8000, json_mode=True)

    prompt = f"""You are an academic syllabus analyzer. Parse the following syllabus text and extract a structured breakdown.

SUBJECT: {subject_name if subject_name else "Determine from the text"}

SYLLABUS TEXT:
\"\"\"
{text[:4000]}
\"\"\"

INSTRUCTIONS:
1. Think step-by-step about the syllabus structure.
2. Identify units/modules and their topics.
3. For each topic, estimate study hours based on complexity. Keep descriptions concise (1 sentence max) to ensure all units and topics fit completely.
4. Return ONLY valid JSON.

Return JSON in this exact format:
{{
    "subject_name": "Name of the subject",
    "reasoning": "Step-by-step analysis of how you identified the structure",
    "units": [
        {{
            "unit_name": "Unit 1: ...",
            "topics": [
                {{
                    "topic_name": "Topic name",
                    "description": "Brief description of what this topic covers",
                    "estimated_hours": 2.5
                }}
            ]
        }}
    ]
}}"""

    try:
        response = llm.invoke(prompt)
        result = extract_json_safe(response.content)
        return result
    except json.JSONDecodeError:
        return {
            "subject_name": subject_name or "Unknown",
            "reasoning": "Failed to parse LLM response as JSON",
            "units": [],
        }
    except Exception as e:
        return {
            "subject_name": subject_name or "Unknown",
            "reasoning": f"Error: {str(e)}",
            "units": [],
        }


def parse_question_paper(text: str, subject_name: str = "") -> dict:
    """
    Parse a previous year question paper to identify important topics.
    Returns: {"important_topics": [{"topic": str, "frequency": str, "marks_weight": str}]}
    """
    llm = get_llm(temperature=0.1, max_tokens=2000, json_mode=True)

    prompt = f"""You are an exam question paper analyzer. Analyze this question paper and identify frequently tested topics.

SUBJECT: {subject_name if subject_name else "Determine from the text"}

QUESTION PAPER TEXT:
\"\"\"
{text[:4000]}
\"\"\"

INSTRUCTIONS:
1. Identify each question and its topic area.
2. Note mark allocations per topic.
3. Rank topics by importance based on marks weight and frequency.

Return JSON:
{{
    "subject_name": "{subject_name}",
    "reasoning": "Step-by-step analysis of question paper",
    "important_topics": [
        {{
            "topic": "Topic name",
            "frequency": "high/medium/low",
            "marks_weight": "percentage or marks allocated",
            "question_types": "theory/numerical/practical"
        }}
    ]
}}"""

    try:
        response = llm.invoke(prompt)
        return extract_json_safe(response.content)
    except Exception as e:
        return {
            "subject_name": subject_name,
            "reasoning": f"Error: {str(e)}",
            "important_topics": [],
        }



def parse_notes(text: str, subject_name: str = "") -> dict:
    """Parse text from uploaded PDF/document of lecture slides or notes."""
    llm = get_llm(temperature=0.1, max_tokens=2500, json_mode=True)
    prompt = f"""You are an academic notes organizer. Analyze the following lecture notes or study material for {subject_name}.

NOTES TEXT:
\"\"\"
{text[:4000]}
\"\"\"

Extract the main title, a brief summary, and key concepts explained.
Return JSON:
{{
    "title": "Topic or title of these notes",
    "summary": "Brief 1-2 sentence summary of what these notes cover",
    "concepts_covered": ["Concept 1", "Concept 2"]
}}"""
    try:
        res = llm.invoke(prompt)
        parsed = extract_json_safe(res.content)
        parsed["extracted_text"] = text[:3500]
        return parsed
    except Exception:
        first_line = (text.strip().split("\n")[0])[:60]
        return {
            "title": first_line or f"Notes for {subject_name}",
            "summary": f"Uploaded study notes for {subject_name}.",
            "concepts_covered": [],
            "extracted_text": text[:3500],
        }


_NOTES_IMAGE_PROMPT = """You are an expert academic document and handwritten notes reader. Read this photo of student study notes, handwritten notebook pages, or lecture slides carefully.
Transcribe and extract the core concepts, definitions, formulas, and explanations cleanly.

SUBJECT: {subject}

Return ONLY valid JSON in this exact structure:
{{
    "title": "Topic or title of these notes",
    "summary": "Brief 1-2 sentence summary of what these notes cover",
    "concepts_covered": ["Concept 1", "Concept 2"],
    "extracted_text": "Detailed transcription and structured breakdown of the contents shown in the image"
}}"""

def parse_document(file_path: str, subject_name: str = "", kind: str = "syllabus") -> dict:
    """Parse an uploaded document, picking the fastest route for its type.

    Images go straight to the multimodal model — one call instead of ~15-25s of
    local OCR followed by a separate text parse. If that route is unavailable
    (vision disabled, or a text-only model configured) it falls back to
    RapidOCR + the text prompt, which still works fully offline.

    Raises ValueError when no text could be recovered at all.
    """
    if is_image(file_path) and USE_VISION:
        if kind == "syllabus":
            prompt = _SYLLABUS_IMAGE_PROMPT
        elif kind in ("notes", "handwritten", "lecture_notes"):
            prompt = _NOTES_IMAGE_PROMPT
        else:
            prompt = _PAPER_IMAGE_PROMPT
        try:
            result = _vision_json(file_path, prompt.format(subject=subject_name or "Determine from the image"))
            has_content = (
                result.get("units") if kind == "syllabus"
                else (result.get("extracted_text") or result.get("summary") or result.get("title")) if kind in ("notes", "handwritten", "lecture_notes")
                else result.get("important_topics")
            )
            if has_content:
                result["_route"] = "vision"
                return result
        except Exception:
            pass  # fall through to OCR

    text = extract_text_from_file(file_path)
    if not text or text.startswith("Error") or len(text.strip()) < 15:
        raise ValueError(
            text if text.startswith("Error")
            else "No readable text found. If this is a photo, ensure it is clear and well-lit."
        )

    if kind == "syllabus":
        result = parse_syllabus(text, subject_name)
    elif kind in ("notes", "handwritten", "lecture_notes"):
        result = parse_notes(text, subject_name)
    else:
        result = parse_question_paper(text, subject_name)
    result["_route"] = "ocr" if is_image(file_path) else "text"
    return result

_SYLLABUS_IMAGE_PROMPT = """You are an academic syllabus analyzer. Read this syllabus image carefully and extract a structured breakdown.

SUBJECT: {subject}

INSTRUCTIONS:
1. Read every module/unit heading and the topics listed under it.
2. Correct any obvious typos from the image.
3. Estimate study hours per topic based on complexity, using the lecture hours shown if present.
4. Return ONLY valid JSON.

Return JSON in this exact format:
{{
    "subject_name": "Name of the subject",
    "reasoning": "Step-by-step analysis of how you identified the structure",
    "units": [
        {{
            "unit_name": "Unit 1: ...",
            "topics": [
                {{"topic_name": "Topic name", "description": "Brief description", "estimated_hours": 2.5}}
            ]
        }}
    ]
}}"""


_PAPER_IMAGE_PROMPT = """You are an exam question paper analyzer. Read this question paper image and identify the topics that carry the most weight.

SUBJECT: {subject}

Return ONLY valid JSON:
{{
    "important_topics": [
        {{"topic": "Topic name", "frequency": "high|medium|low", "marks_weight": "15%", "question_types": "theory/numerical"}}
    ]
}}"""


def save_parsed_syllabus(parsed: dict, subject_id: int = None):
    """Save parsed syllabus data into the database."""
    from db.database import add_subject, add_topic, get_all_subjects

    # Create subject if needed
    sid = subject_id
    if not sid:
        sid = add_subject(parsed.get("subject_name", "Unknown"))

    topic_count = 0
    for unit in parsed.get("units", []):
        for topic in unit.get("topics", []):
            add_topic(
                subject_id=sid,
                topic_name=topic.get("topic_name", ""),
                unit_name=unit.get("unit_name", ""),
                description=topic.get("description", ""),
                estimated_hours=topic.get("estimated_hours", 2.0),
            )
            topic_count += 1

    return sid, topic_count
