"""Degree progress calculation and next-semester course suggestions.

Deterministic throughout: progress is arithmetic over the student's actual
completed-course record against the degree program's requirement groups,
and suggestions are filtered by the prerequisite engine's real eligibility
check -- never an LLM guess at what a student "probably" still needs.
"""

import uuid
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.degree import DegreeProgram
from app.repositories.degree_repository import DegreeRepository
from app.repositories.section_repository import SectionRepository
from app.services.prerequisite_engine import check_eligibility


@dataclass
class RequirementGroupProgress:
    name: str
    required_count: int
    completed_count: int
    complete: bool
    completed_course_codes: list[str]
    remaining_course_codes: list[str]


@dataclass
class DegreeProgressResult:
    degree_program_name: str
    overall_percent: float
    groups: list[RequirementGroupProgress] = field(default_factory=list)


@dataclass
class SuggestedCourse:
    course: Course
    requirement_group: str
    eligible: bool
    missing_prerequisites: list[str]
    offered_this_term: bool


def calculate_progress(
    degree_program: DegreeProgram, completed_course_ids: set[uuid.UUID]
) -> DegreeProgressResult:
    groups: list[RequirementGroupProgress] = []
    for group in degree_program.requirement_groups:
        eligible_courses = {erc.course_id: erc.course for erc in group.eligible_courses}
        completed_in_group = [
            course for cid, course in eligible_courses.items() if cid in completed_course_ids
        ]
        remaining = [
            course for cid, course in eligible_courses.items() if cid not in completed_course_ids
        ]
        groups.append(
            RequirementGroupProgress(
                name=group.name,
                required_count=group.required_count,
                completed_count=len(completed_in_group),
                complete=len(completed_in_group) >= group.required_count,
                completed_course_codes=sorted(c.code for c in completed_in_group),
                remaining_course_codes=sorted(c.code for c in remaining),
            )
        )

    total_required = sum(g.required_count for g in groups)
    if total_required > 0:
        earned = sum(min(g.completed_count, g.required_count) for g in groups)
        overall_percent = round(100 * earned / total_required, 1)
    else:
        overall_percent = 0.0

    return DegreeProgressResult(
        degree_program_name=degree_program.name, overall_percent=overall_percent, groups=groups
    )


def suggest_next_courses(
    db: Session,
    degree_program: DegreeProgram,
    completed_course_ids: set[uuid.UUID],
    active_term_id: uuid.UUID | None,
) -> list[SuggestedCourse]:
    degree_repo = DegreeRepository(db)
    section_repo = SectionRepository(db)

    suggestions: list[SuggestedCourse] = []
    seen_course_ids: set[uuid.UUID] = set()

    for group in degree_program.requirement_groups:
        completed_in_group = sum(
            1 for erc in group.eligible_courses if erc.course_id in completed_course_ids
        )
        if completed_in_group >= group.required_count:
            continue  # this requirement is already satisfied

        for erc in group.eligible_courses:
            if erc.course_id in completed_course_ids or erc.course_id in seen_course_ids:
                continue
            seen_course_ids.add(erc.course_id)

            prereqs = degree_repo.prerequisites_for(erc.course_id)
            eligibility = check_eligibility(prereqs, completed_course_ids)

            offered_this_term = False
            if active_term_id is not None:
                sections = section_repo.list_for_courses([erc.course_id], active_term_only=True)
                offered_this_term = len(sections) > 0

            suggestions.append(
                SuggestedCourse(
                    course=erc.course,
                    requirement_group=group.name,
                    eligible=eligibility.eligible,
                    missing_prerequisites=[
                        " or ".join(m.options) for m in eligibility.missing
                    ],
                    offered_this_term=offered_this_term,
                )
            )

    suggestions.sort(key=lambda s: (not s.eligible, not s.offered_this_term, s.course.code))
    return suggestions
