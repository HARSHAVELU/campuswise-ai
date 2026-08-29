"""Recommendation Engine pipeline: query -> parsed requirement -> ranked, explained sections.

Query -> RequirementParserAgent -> course discovery -> section candidates for
the active planning term -> hard constraint filter -> feature scoring ->
Fit Score -> explanation -> ranked recommendations -> optional composition
(e.g. "2 online and 2 in-person") over the ranked set.
"""

from sqlalchemy.orm import Session

from app.agents.course_discovery import discover_courses
from app.agents.requirement_parser import parse_requirement
from app.ranking.composition import compose_by_delivery_mode_counts
from app.ranking.engine import rank_sections
from app.repositories.section_repository import SectionRepository
from app.schemas.recommendation import RecommendationResponse

EXCLUSION_REASON_LABELS = {
    "delivery_mode": "delivery mode",
    "level": "course level",
    "missing_rating_data": "professor rating not on record",
    "rating_below_threshold": "professor rating below your threshold",
    "starts_too_early": "starts earlier than you want",
    "starts_too_late": "starts later than you want",
    "excluded_day": "meets on a day you excluded",
}


def run_course_recommendations(db: Session, query: str, limit: int = 10) -> RecommendationResponse:
    parsed = parse_requirement(query)

    courses = discover_courses(db, parsed)
    section_repo = SectionRepository(db)
    sections = section_repo.list_for_courses(
        course_ids=[course.id for course in courses], active_term_only=True
    )

    recommendations, filter_result = rank_sections(db, parsed, sections)

    notes = list(parsed.unsupported_notes)
    if parsed.topic and not courses:
        notes.append(f"No courses matched the topic '{parsed.topic}'.")
    elif courses and not sections:
        notes.append("No sections are scheduled for these courses in the active planning term.")
    elif sections and not recommendations:
        notes.append("Every candidate section was excluded by your requirements.")

    for reason, count in filter_result.excluded_reasons.items():
        label = EXCLUSION_REASON_LABELS.get(reason, reason)
        notes.append(f"{count} section(s) excluded: {label}.")

    if parsed.hard_constraints.delivery_mode_counts:
        recommendations, composition_notes = compose_by_delivery_mode_counts(
            recommendations, parsed.hard_constraints.delivery_mode_counts
        )
        notes.extend(composition_notes)
    else:
        recommendations = recommendations[:limit]

    return RecommendationResponse(parsed=parsed, recommendations=recommendations, notes=notes)
