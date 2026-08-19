"""Deterministic fallback for assessment-metadata extraction.

Used when no LLM is configured or the LLM call fails. Reliable on
consistently-templated syllabus text (like the seeded sample documents) but
not a general-purpose parser for arbitrary real-world syllabus phrasing --
the LLM-backed extractor (app.agents.assessment_llm_extractor) is the
primary path for that. Same fallback philosophy as the RequirementParserAgent
(Phase 4) and the embedding provider (Phase 6).
"""

import re

RULE_BASED_CONFIDENCE = 0.7

# Label characters deliberately exclude "\n" (unlike \s) so a weight label
# never spans across a paragraph break.
_WEIGHT_PATTERNS = [
    re.compile(r"([A-Za-z][A-Za-z ,\-]{2,50}?)\s+(?:is|are)\s+worth\s+(\d{1,3})%", re.IGNORECASE),
    re.compile(
        r"([A-Za-z][A-Za-z ,\-]{2,50}?)\s+counts\s+for\s+(?:the remaining\s+)?(\d{1,3})%",
        re.IGNORECASE,
    ),
]


def _extract_weights(text: str) -> dict[str, float]:
    weights: dict[str, float] = {}
    for pattern in _WEIGHT_PATTERNS:
        for label, pct in pattern.findall(text):
            key = label.strip().lower()
            key = re.sub(r"^(?:(?:the|a|an|and)\s+)+", "", key)
            weights[key] = float(pct)
    return weights


def _extract_exam_format_paragraph(text: str) -> str | None:
    match = re.search(r"Exam Format:(.*?)(?:\n\n|$)", text, re.DOTALL)
    return match.group(1).strip() if match else None


def _sentence_mentioning(paragraph: str, keyword: str) -> str | None:
    for sentence in re.split(r"(?<=[.!?])\s+", paragraph):
        if keyword.lower() in sentence.lower():
            return sentence
    return None


def _format_from_sentence(sentence: str | None) -> str | None:
    if sentence is None:
        return None
    lowered = sentence.lower()
    if "take-home" in lowered or "take home" in lowered:
        return "take_home"
    if "online" in lowered:
        return "online"
    if "in person" in lowered or "in-person" in lowered:
        return "in_person"
    return None


def _open_book_from_sentence(sentence: str | None) -> bool | None:
    if sentence is None:
        return None
    lowered = sentence.lower()
    if "open-book" in lowered or "open book" in lowered:
        return True
    if "closed-book" in lowered or "closed book" in lowered:
        return False
    return None


def _proctoring_from_sentence(sentence: str | None) -> str | None:
    if sentence is None:
        return None
    match = re.search(r"proctored via (\w+)", sentence, re.IGNORECASE)
    if match:
        return match.group(1)
    if "lockdown browser" in sentence.lower():
        return "LockDown Browser"
    return None


def _midterm_has_no_exam(text: str) -> bool:
    return bool(re.search(r"no midterm exam|no midterm or final exam|has no exams?", text, re.IGNORECASE))


def _final_has_no_exam(text: str) -> bool:
    return bool(
        re.search(
            r"no (?:separate |traditional )?final exam|no midterm or final exam|has no exams?",
            text,
            re.IGNORECASE,
        )
    )


ExamDetail = tuple[str | None, bool | None, str | None]


def _exam_detail_for(sentence: str | None, no_exam: bool) -> ExamDetail:
    if no_exam:
        return "none", None, None
    return (
        _format_from_sentence(sentence),
        _open_book_from_sentence(sentence),
        _proctoring_from_sentence(sentence),
    )


def _extract_exam_details(
    paragraph: str | None, no_midterm: bool, no_final: bool
) -> tuple[ExamDetail, ExamDetail]:
    if paragraph is None:
        return _exam_detail_for(None, no_midterm), _exam_detail_for(None, no_final)

    midterm_sentence = _sentence_mentioning(paragraph, "midterm")
    final_sentence = _sentence_mentioning(paragraph, "final")

    if midterm_sentence is None and final_sentence is None and re.search(
        r"both (?:the )?exams|both the midterm and final", paragraph, re.IGNORECASE
    ):
        midterm_sentence = paragraph
        final_sentence = paragraph

    return (
        _exam_detail_for(midterm_sentence, no_midterm),
        _exam_detail_for(final_sentence, no_final),
    )


def _extract_late_policy(text: str) -> str | None:
    match = re.search(r"Late Policy:(.*?)(?:\n\n|$)", text, re.DOTALL)
    if not match:
        return None
    summary = " ".join(match.group(1).split())
    return summary[:300]


def _extract_attendance(text: str) -> tuple[bool | None, float | None]:
    lowered = text.lower()
    required: bool | None = None
    if re.search(r"attendance is (required|mandatory)", lowered):
        required = True
    elif re.search(r"attendance is not (mandatory|tracked|required)", lowered):
        required = False
    elif "attendance is recorded but not directly graded" in lowered:
        required = False

    weight_match = re.search(r"attendance[^.]*?worth\s+(\d{1,3})%", lowered)
    weight = float(weight_match.group(1)) if weight_match else None
    return required, weight


def extract_assessment_rule_based(text: str) -> dict:
    no_midterm = _midterm_has_no_exam(text)
    no_final = _final_has_no_exam(text)
    exam_paragraph = _extract_exam_format_paragraph(text)

    (midterm_format, midterm_open_book, midterm_proctoring), (
        final_format,
        final_open_book,
        final_proctoring,
    ) = _extract_exam_details(exam_paragraph, no_midterm, no_final)

    attendance_required, attendance_weight_pct = _extract_attendance(text)

    return {
        "midterm_format": midterm_format,
        "midterm_open_book": midterm_open_book,
        "midterm_proctoring": midterm_proctoring,
        "final_format": final_format,
        "final_open_book": final_open_book,
        "final_proctoring": final_proctoring,
        "has_group_project": bool(
            re.search(
                r"group project|team project|team research project|teams of|team-based|in teams",
                text,
                re.IGNORECASE,
            )
        ),
        "has_individual_project": bool(re.search(r"individual project", text, re.IGNORECASE)),
        "has_presentation": bool(re.search(r"presentation", text, re.IGNORECASE)),
        "has_quizzes": bool(re.search(r"quiz", text, re.IGNORECASE)),
        "attendance_required": attendance_required,
        "attendance_weight_pct": attendance_weight_pct,
        "late_policy_summary": _extract_late_policy(text),
        "weights": _extract_weights(text),
        "confidence": RULE_BASED_CONFIDENCE,
        "extraction_method": "rule_based",
    }
