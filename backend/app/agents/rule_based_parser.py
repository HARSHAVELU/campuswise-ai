"""Deterministic fallback for the RequirementParserAgent.

Used when no LLM is configured (no ANTHROPIC_API_KEY) or when the LLM call
fails, so natural-language search keeps working — with reduced accuracy —
in local development, CI, and offline demos. The LLM-backed parser
(app.agents.llm_parser) is the primary path in production.

This is intentionally a narrow set of regex rules, not a general NLU system:
it covers the phrasing patterns from the product brief's demo scenarios.
"""

import re

from app.schemas.ai_search import HardConstraints, ParsedRequirement, SoftPreferences

TOPIC_KEYWORDS = [
    "machine learning",
    "natural language processing",
    "artificial intelligence",
    "data structures",
    "data visualization",
    "business analytics",
    "software engineering",
    "operating systems",
    "linear algebra",
    "algorithms",
    "database",
    "statistics",
    "probability",
    "calculus",
    "marketing",
    "finance",
    "python",
    "nlp",
    "sql",
    "ai",
]

DAYS_OF_WEEK = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

_AMPM_HOUR = re.compile(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", re.IGNORECASE)


def _parse_clock_time(hour: str, minute: str | None, ampm: str | None) -> str:
    h = int(hour)
    m = int(minute) if minute else 0
    if ampm:
        ampm = ampm.lower()
        if ampm == "pm" and h != 12:
            h += 12
        elif ampm == "am" and h == 12:
            h = 0
    return f"{h:02d}:{m:02d}"


def _extract_topic(text: str) -> str | None:
    lowered = text.lower()
    for keyword in sorted(TOPIC_KEYWORDS, key=len, reverse=True):
        if re.search(rf"\b{re.escape(keyword)}\b", lowered):
            return keyword
    return None


def _extract_delivery_modes(text: str) -> tuple[list[str] | None, list[str] | None]:
    """Returns (hard_modes, soft_preferred_modes).

    "Online exams" describes the exam format, not the course's delivery
    mode -- e.g. "database course with online exams" should not be read as
    requiring an online course. Exam-format mentions of "online" are masked
    out before delivery-mode keywords are searched for.
    """
    lowered = text.lower()
    # Only bridge "exam"/"online" across a small set of connector words (not
    # arbitrary text), so an unrelated earlier "online" -- e.g. the course
    # delivery mode in "an online course with online exams" -- is never
    # swept into this mask.
    connectors = r"(?:should|preferably|be|is|are|will|the|final|midterm)"
    lowered = re.sub(rf"\bonline\b(?:\s+{connectors})*\s+exams?\b", "", lowered)
    lowered = re.sub(rf"\bexams?\b(?:\s+{connectors})*\s+online\b", "", lowered)

    prefer_match = re.search(r"prefer[a-z]*\s+([^.,;]+)", lowered)
    preferred_segment = prefer_match.group(1) if prefer_match else ""

    mode_patterns = {
        "online": r"\bonline\b",
        "hybrid": r"\bhybrid\b",
        "in_person": r"\bin[- ]person\b|\bon campus\b",
    }

    soft_modes: list[str] = []
    for mode, pattern in mode_patterns.items():
        if re.search(pattern, preferred_segment):
            soft_modes.append(mode)

    remaining_text = lowered.replace(preferred_segment, "") if prefer_match else lowered
    hard_modes: list[str] = []
    for mode, pattern in mode_patterns.items():
        if mode not in soft_modes and re.search(pattern, remaining_text):
            hard_modes.append(mode)

    return (hard_modes or None, soft_modes or None)


def _extract_level(text: str) -> str | None:
    lowered = text.lower()
    if re.search(r"\bundergraduate\b", lowered):
        return "undergraduate"
    if re.search(r"\bgraduate\b", lowered):
        return "graduate"
    return None


def _extract_excluded_days(text: str) -> list[str] | None:
    lowered = text.lower()
    excluded = [
        day
        for day in DAYS_OF_WEEK
        if re.search(rf"(no|without|avoid(?:ing)?)\s+{day}", lowered)
    ]
    return excluded or None


def _extract_time_window(text: str) -> tuple[str | None, str | None]:
    """Returns (earliest_start_time, latest_start_time)."""
    earliest: str | None = None
    latest: str | None = None

    neg_before = re.search(
        r"(no|nothing|don't want|do not want)[^.]{0,40}?before\s+" + _AMPM_HOUR.pattern,
        text,
        re.IGNORECASE,
    )
    if neg_before:
        # group offsets: 1=qualifier phrase word, then hour/min/ampm captured after
        hour, minute, ampm = neg_before.group(2), neg_before.group(3), neg_before.group(4)
        earliest = _parse_clock_time(hour, minute, ampm)

    after_match = re.search(r"\bafter\s+" + _AMPM_HOUR.pattern, text, re.IGNORECASE)
    if after_match:
        earliest = _parse_clock_time(*after_match.groups())

    if not neg_before:
        plain_before = re.search(r"\bbefore\s+" + _AMPM_HOUR.pattern, text, re.IGNORECASE)
        if plain_before:
            latest = _parse_clock_time(*plain_before.groups())

    return earliest, latest


def _extract_rating_threshold(text: str) -> float | None:
    match = re.search(
        r"rat(?:ing|ed)\s*(?:above|over|at least|greater than|>=?)\s*(\d(?:\.\d)?)",
        text,
        re.IGNORECASE,
    )
    return float(match.group(1)) if match else None


def parse_requirement_rule_based(query: str) -> ParsedRequirement:
    hard_modes, soft_modes = _extract_delivery_modes(query)
    earliest, latest = _extract_time_window(query)
    min_rating = _extract_rating_threshold(query)

    lowered = query.lower()
    exam_connectors = r"(?:should|preferably|be|is|are|will|the|final|midterm)"
    prefer_online_exams = bool(
        re.search(rf"\bonline\b(?:\s+{exam_connectors})*\s+exams?\b", lowered)
        or re.search(rf"\bexams?\b(?:\s+{exam_connectors})*\s+online\b", lowered)
    )
    prefer_easier_grading = bool(
        re.search(r"\beasy\b|easier grading|good grades|higher grades|historically good grades", lowered)
    )
    prefer_higher_rated = bool(
        re.search(r"good professor|best professor|highly rated|great teacher", lowered)
    ) or min_rating is not None
    prefer_fewer_campus_days = bool(
        re.search(r"fewer campus days|fewer days on campus|minimize campus days", lowered)
    )

    unsupported_notes: list[str] = []

    return ParsedRequirement(
        raw_query=query,
        topic=_extract_topic(query),
        hard_constraints=HardConstraints(
            delivery_modes=hard_modes,
            earliest_start_time=earliest,
            latest_start_time=latest,
            exclude_days=_extract_excluded_days(query),
            minimum_professor_rating=min_rating,
            level=_extract_level(query),
        ),
        soft_preferences=SoftPreferences(
            prefer_delivery_modes=soft_modes,
            prefer_higher_rated_professor=prefer_higher_rated,
            prefer_easier_grading=prefer_easier_grading,
            prefer_online_exams=prefer_online_exams,
            prefer_fewer_campus_days=prefer_fewer_campus_days,
        ),
        unsupported_notes=unsupported_notes,
        parser_source="rule_based",
    )
