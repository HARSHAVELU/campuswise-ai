"""Deterministic hard-constraint filtering over sections.

Every rule here either passes or excludes a candidate outright -- nothing is
guessed. Where the data needed to verify a constraint doesn't exist (e.g. a
minimum-rating requirement but the professor has no rating on record), the
section is excluded rather than assumed to pass, and the reason is reported
so the caller can tell the student why (see docs/architecture-proposal.md,
"Hallucination Protection").
"""

from dataclasses import dataclass, field
from datetime import time

from app.models.section import Section
from app.schemas.ai_search import HardConstraints


def _parse_hhmm(value: str) -> time:
    hours, minutes = value.split(":")
    return time(int(hours), int(minutes))


@dataclass
class HardFilterResult:
    passed: list[Section] = field(default_factory=list)
    excluded_reasons: dict[str, int] = field(default_factory=dict)

    def _record_exclusion(self, reason: str) -> None:
        self.excluded_reasons[reason] = self.excluded_reasons.get(reason, 0) + 1


def _violates(section: Section, hard: HardConstraints) -> str | None:
    if hard.delivery_modes and section.delivery_mode.value not in hard.delivery_modes:
        return "delivery_mode"

    if hard.level and section.course.level.value != hard.level:
        return "level"

    if hard.minimum_professor_rating is not None:
        if section.professor is None or section.professor.rating is None:
            return "missing_rating_data"
        if section.professor.rating.overall_rating < hard.minimum_professor_rating:
            return "rating_below_threshold"

    earliest = _parse_hhmm(hard.earliest_start_time) if hard.earliest_start_time else None
    latest = _parse_hhmm(hard.latest_start_time) if hard.latest_start_time else None

    for meeting in section.meetings:
        if earliest is not None and meeting.start_time < earliest:
            return "starts_too_early"
        if latest is not None and meeting.start_time > latest:
            return "starts_too_late"
        if hard.exclude_days and meeting.day_of_week.value in hard.exclude_days:
            return "excluded_day"

    return None


def apply_hard_constraints(sections: list[Section], hard: HardConstraints) -> HardFilterResult:
    result = HardFilterResult()
    for section in sections:
        reason = _violates(section, hard)
        if reason is None:
            result.passed.append(section)
        else:
            result._record_exclusion(reason)
    return result
