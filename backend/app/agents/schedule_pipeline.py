"""Schedule Builder pipeline: query -> ranked candidates -> optimized schedules.

Reuses the exact same parse -> discover -> hard-filter -> score pipeline as
the Recommendation Engine (Phase 5), then hands the scored candidates to the
CP-SAT optimizer once per named strategy. The optimizer never re-derives a
quality signal -- it only combines the scores the ranking engine already
computed from real data.
"""

import uuid

from sqlalchemy.orm import Session

from app.agents.course_discovery import discover_courses
from app.agents.recommendation_pipeline import EXCLUSION_REASON_LABELS
from app.agents.requirement_parser import parse_requirement
from app.optimization.conflict_detection import detect_conflicts
from app.optimization.schedule_optimizer import (
    STRATEGY_LABELS,
    ScheduleStrategy,
    diagnose_insufficient_mode_candidates,
    solve_schedule,
)
from app.ranking.engine import rank_sections
from app.repositories.section_repository import SectionRepository
from app.schemas.schedule import (
    ConflictWarningRead,
    ScheduleGenerateResponse,
    ScheduleResult,
    ScheduleValidateResponse,
)
from app.schemas.section import SectionRead


def generate_schedules(
    db: Session, query: str, min_credits: int, max_credits: int
) -> ScheduleGenerateResponse:
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

    for reason, count in filter_result.excluded_reasons.items():
        label = EXCLUSION_REASON_LABELS.get(reason, reason)
        notes.append(f"{count} section(s) excluded: {label}.")

    schedules: dict[str, ScheduleResult | None] = {}
    for strategy in ScheduleStrategy:
        solution = solve_schedule(
            recommendations,
            strategy,
            min_credits,
            max_credits,
            delivery_mode_counts=parsed.hard_constraints.delivery_mode_counts,
        )
        if solution is None:
            schedules[strategy.value] = None
            continue
        average_fit_score = sum(rec.fit_score for rec in solution.selected) / len(solution.selected)
        schedules[strategy.value] = ScheduleResult(
            strategy=strategy.value,
            label=STRATEGY_LABELS[strategy],
            sections=[rec.section for rec in solution.selected],
            total_credits=solution.total_credits,
            campus_days=solution.campus_days,
            average_fit_score=round(average_fit_score, 1),
        )

    if not recommendations:
        notes.append("No candidate sections were available to build a schedule from.")
    elif all(result is None for result in schedules.values()):
        if parsed.hard_constraints.delivery_mode_counts:
            notes.extend(
                diagnose_insufficient_mode_candidates(
                    recommendations, parsed.hard_constraints.delivery_mode_counts
                )
            )
        notes.append(
            f"No feasible schedule was found within {min_credits}-{max_credits} credits given "
            "your current requirements. Try widening the credit range or relaxing a requirement."
        )

    return ScheduleGenerateResponse(parsed=parsed, schedules=schedules, notes=notes)


def validate_schedule(db: Session, section_ids: list[uuid.UUID]) -> ScheduleValidateResponse:
    section_repo = SectionRepository(db)
    sections: list[SectionRead] = []
    for section_id in section_ids:
        section = section_repo.get(section_id)
        if section is not None:
            sections.append(SectionRead.model_validate(section))

    conflicts = detect_conflicts(sections)
    conflict_reads = [
        ConflictWarningRead(
            section_a_id=c.section_a_id,
            section_b_id=c.section_b_id,
            conflict_type=c.conflict_type,
            day_of_week=c.day_of_week,
            detail=c.detail,
        )
        for c in conflicts
    ]
    is_valid = not any(c.conflict_type == "time_overlap" for c in conflicts)
    return ScheduleValidateResponse(conflicts=conflict_reads, is_valid=is_valid)
