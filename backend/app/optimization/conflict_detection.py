"""Deterministic schedule conflict detection.

Operates on already-fetched SectionRead objects (day/time/meetings), not
raw SQL -- the same section representation used everywhere else in the API,
so this logic is reusable from both the /schedule/validate endpoint and the
optimizer's constraint building.
"""

from dataclasses import dataclass

from app.schemas.section import SectionMeetingRead, SectionRead

TRANSITION_BUFFER_MINUTES = 15


@dataclass
class ConflictWarning:
    section_a_id: str
    section_b_id: str
    conflict_type: str  # "time_overlap" | "insufficient_transition_time"
    day_of_week: str
    detail: str


def _minutes_between(earlier_end, later_start) -> int:
    return (later_start.hour * 60 + later_start.minute) - (earlier_end.hour * 60 + earlier_end.minute)


def meetings_overlap(a: SectionMeetingRead, b: SectionMeetingRead) -> bool:
    return a.day_of_week == b.day_of_week and a.start_time < b.end_time and b.start_time < a.end_time


def _meetings_too_close(a: SectionMeetingRead, b: SectionMeetingRead) -> int | None:
    if a.day_of_week != b.day_of_week:
        return None
    if a.end_time <= b.start_time:
        gap = _minutes_between(a.end_time, b.start_time)
    elif b.end_time <= a.start_time:
        gap = _minutes_between(b.end_time, a.start_time)
    else:
        return None  # overlapping, not a transition-gap case
    return gap if 0 <= gap < TRANSITION_BUFFER_MINUTES else None


def find_conflicts(section_a: SectionRead, section_b: SectionRead) -> list[ConflictWarning]:
    warnings: list[ConflictWarning] = []
    for meeting_a in section_a.meetings:
        for meeting_b in section_b.meetings:
            if meetings_overlap(meeting_a, meeting_b):
                warnings.append(
                    ConflictWarning(
                        section_a_id=str(section_a.id),
                        section_b_id=str(section_b.id),
                        conflict_type="time_overlap",
                        day_of_week=meeting_a.day_of_week,
                        detail=(
                            f"{section_a.course.code} and {section_b.course.code} both meet "
                            f"{meeting_a.day_of_week.capitalize()} and overlap in time."
                        ),
                    )
                )
                continue
            gap = _meetings_too_close(meeting_a, meeting_b)
            if gap is not None:
                warnings.append(
                    ConflictWarning(
                        section_a_id=str(section_a.id),
                        section_b_id=str(section_b.id),
                        conflict_type="insufficient_transition_time",
                        day_of_week=meeting_a.day_of_week,
                        detail=(
                            f"{section_a.course.code} and {section_b.course.code} leave only "
                            f"{gap} minute(s) to get between classes on "
                            f"{meeting_a.day_of_week.capitalize()}."
                        ),
                    )
                )
    return warnings


def detect_conflicts(sections: list[SectionRead]) -> list[ConflictWarning]:
    warnings: list[ConflictWarning] = []
    for i in range(len(sections)):
        for j in range(i + 1, len(sections)):
            warnings.extend(find_conflicts(sections[i], sections[j]))
    return warnings
