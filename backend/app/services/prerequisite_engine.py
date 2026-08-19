"""Deterministic prerequisite eligibility checking.

Rows sharing a group_number are OR'd together; different group_numbers are
AND'd together (see app.models.degree.CoursePrerequisite). This is never
delegated to an LLM -- eligibility is a factual yes/no derived from the
student's actual completed-course record (see docs/architecture-proposal.md,
"Prerequisite Engine": "Do NOT rely on the LLM alone to determine eligibility").
"""

import uuid
from dataclasses import dataclass, field

from app.models.degree import CoursePrerequisite


@dataclass
class MissingRequirement:
    """One AND-group that isn't satisfied yet; `options` are the OR'd choices."""

    options: list[str]  # course codes, any one of which would satisfy this group


@dataclass
class EligibilityResult:
    eligible: bool
    missing: list[MissingRequirement] = field(default_factory=list)


def check_eligibility(
    prerequisite_rows: list[CoursePrerequisite], completed_course_ids: set[uuid.UUID]
) -> EligibilityResult:
    groups: dict[int, list[CoursePrerequisite]] = {}
    for row in prerequisite_rows:
        groups.setdefault(row.group_number, []).append(row)

    missing: list[MissingRequirement] = []
    for group_number in sorted(groups):
        rows = groups[group_number]
        satisfied = any(row.prerequisite_course_id in completed_course_ids for row in rows)
        if not satisfied:
            missing.append(
                MissingRequirement(options=[row.prerequisite_course.code for row in rows])
            )

    return EligibilityResult(eligible=not missing, missing=missing)
