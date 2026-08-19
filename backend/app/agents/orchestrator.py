"""AI search pipeline entry point.

Student query -> RequirementParserAgent -> course/professor discovery ->
response. A LangGraph state machine is the natural home for this once more
branching intents exist (syllabus Q&A in Phase 6, schedule generation in
Phase 8); with a single linear intent today, a plain function is clearer and
avoids an unjustified dependency (see docs/architecture-proposal.md, "AI
Architecture" -- prefer deterministic code where an agent adds no value).
"""

from sqlalchemy.orm import Session

from app.agents.course_discovery import discover_courses, discover_professors
from app.agents.requirement_parser import parse_requirement
from app.schemas.ai_search import AISearchResponse


def run_ai_search(db: Session, query: str) -> AISearchResponse:
    parsed = parse_requirement(query)

    courses = discover_courses(db, parsed)
    professors = discover_professors(db, parsed)

    notes = list(parsed.unsupported_notes)
    if parsed.topic and not courses:
        notes.append(f"No courses matched the topic '{parsed.topic}'.")
    if parsed.hard_constraints.minimum_professor_rating is not None and not professors:
        notes.append(
            f"No professors currently have a rating at or above "
            f"{parsed.hard_constraints.minimum_professor_rating}."
        )

    return AISearchResponse(
        parsed=parsed,
        courses=courses,
        professors=professors,
        notes=notes,
    )
