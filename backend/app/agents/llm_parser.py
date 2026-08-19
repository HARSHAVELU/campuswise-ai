"""LLM-backed RequirementParserAgent.

Converts a natural-language course request into structured hard constraints
and soft preferences using Claude's tool-use for schema-constrained JSON
output. This is the only place in the platform where an LLM call determines
*what the student is asking for* — it never invents facts about courses,
professors, grades, or availability; it only structures the student's own
words. Retrieval, filtering, and ranking downstream are all deterministic.
"""

import logging

import anthropic

from app.core.config import get_settings
from app.schemas.ai_search import HardConstraints, ParsedRequirement, SoftPreferences

logger = logging.getLogger(__name__)

_TOOL_NAME = "extract_course_requirements"

_TOOL_SCHEMA = {
    "name": _TOOL_NAME,
    "description": (
        "Extract structured course-search requirements from a student's natural-language "
        "request. Separate requirements that must not be violated (hard_constraints) from "
        "requirements that should only influence ranking (soft_preferences)."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "topic": {
                "type": ["string", "null"],
                "description": "The subject/skill/course topic being searched for, e.g. 'python'.",
            },
            "hard_constraints": {
                "type": "object",
                "properties": {
                    "delivery_modes": {
                        "type": ["array", "null"],
                        "items": {"type": "string", "enum": ["in_person", "online", "hybrid"]},
                    },
                    "earliest_start_time": {"type": ["string", "null"], "description": "24h 'HH:MM'"},
                    "latest_start_time": {"type": ["string", "null"], "description": "24h 'HH:MM'"},
                    "exclude_days": {
                        "type": ["array", "null"],
                        "items": {
                            "type": "string",
                            "enum": [
                                "monday", "tuesday", "wednesday", "thursday",
                                "friday", "saturday", "sunday",
                            ],
                        },
                    },
                    "minimum_professor_rating": {"type": ["number", "null"]},
                    "level": {"type": ["string", "null"], "enum": ["undergraduate", "graduate", None]},
                },
            },
            "soft_preferences": {
                "type": "object",
                "properties": {
                    "prefer_delivery_modes": {
                        "type": ["array", "null"],
                        "items": {"type": "string", "enum": ["in_person", "online", "hybrid"]},
                    },
                    "prefer_higher_rated_professor": {"type": "boolean"},
                    "prefer_easier_grading": {"type": "boolean"},
                    "prefer_online_exams": {"type": "boolean"},
                    "prefer_fewer_campus_days": {"type": "boolean"},
                },
            },
            "unsupported_notes": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Requirements the student mentioned that this platform cannot yet verify "
                    "with real data (e.g. exam format before syllabus data exists). One short "
                    "sentence each."
                ),
            },
        },
        "required": ["hard_constraints", "soft_preferences"],
    },
}

_SYSTEM_PROMPT = (
    "You extract structured course-search requirements from a university student's request. "
    "You must not invent or assume any facts about real courses, professors, ratings, grades, "
    "or availability -- you only restructure what the student explicitly said. Classify each "
    "requirement as a hard constraint (must not be violated) only if the student's phrasing is "
    "clearly mandatory ('must be', 'only', 'no ... classes', 'has to'); otherwise treat it as a "
    "soft preference. If the student mentions something this platform cannot yet verify (such as "
    "exam format, syllabus policies, or workload) add a short note to unsupported_notes."
)


class LLMParserError(RuntimeError):
    pass


def parse_requirement_with_llm(query: str) -> ParsedRequirement:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise LLMParserError("ANTHROPIC_API_KEY is not configured")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    try:
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            tools=[_TOOL_SCHEMA],
            tool_choice={"type": "tool", "name": _TOOL_NAME},
            messages=[{"role": "user", "content": query}],
        )
    except anthropic.APIError as exc:
        raise LLMParserError(f"Anthropic API call failed: {exc}") from exc

    tool_use_block = next(
        (block for block in response.content if block.type == "tool_use"), None
    )
    if tool_use_block is None:
        raise LLMParserError("Model did not return a tool_use block")

    payload = tool_use_block.input
    try:
        return ParsedRequirement(
            raw_query=query,
            topic=payload.get("topic"),
            hard_constraints=HardConstraints(**payload.get("hard_constraints", {})),
            soft_preferences=SoftPreferences(**payload.get("soft_preferences", {})),
            unsupported_notes=payload.get("unsupported_notes", []),
            parser_source="llm",
        )
    except Exception as exc:  # pydantic ValidationError or malformed payload
        raise LLMParserError(f"Model output failed schema validation: {exc}") from exc
