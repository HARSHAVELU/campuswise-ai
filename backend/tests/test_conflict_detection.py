from app.optimization.conflict_detection import detect_conflicts
from app.schemas.course import CourseSummary
from app.schemas.section import SectionMeetingRead, SectionRead
from app.schemas.university import DepartmentRead


def _dept():
    return DepartmentRead(id="00000000-0000-0000-0000-000000000001", code="CS", name="Computer Science")


def _course(code="CS 1000"):
    return CourseSummary(
        id="00000000-0000-0000-0000-000000000002", code=code, title="Test Course",
        credit_hours=3, level="undergraduate", department=_dept(), topics=[],
    )


def _section(section_id, day, start, end, code="CS 1000"):
    return SectionRead(
        id=section_id, section_number="001", delivery_mode="in_person",
        seats_total=30, seats_available=10,
        course=_course(code),
        term={"id": "00000000-0000-0000-0000-000000000003", "name": "Fall 2026", "year": 2026, "season": "fall", "is_active_for_planning": True},
        professor=None,
        meetings=[SectionMeetingRead(day_of_week=day, start_time=start, end_time=end, room_id=None)],
    )


def test_no_conflict_for_different_days():
    a = _section("00000000-0000-0000-0000-0000000000a1", "monday", "10:00", "11:15")
    b = _section("00000000-0000-0000-0000-0000000000a2", "tuesday", "10:00", "11:15", code="CS 2000")
    assert detect_conflicts([a, b]) == []


def test_overlapping_times_same_day_detected():
    a = _section("00000000-0000-0000-0000-0000000000a1", "monday", "10:00", "11:15")
    b = _section("00000000-0000-0000-0000-0000000000a2", "monday", "10:30", "11:45", code="CS 2000")
    conflicts = detect_conflicts([a, b])
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == "time_overlap"


def test_back_to_back_with_no_gap_is_not_overlap_but_is_flagged_as_tight():
    a = _section("00000000-0000-0000-0000-0000000000a1", "monday", "10:00", "11:15")
    b = _section("00000000-0000-0000-0000-0000000000a2", "monday", "11:15", "12:30", code="CS 2000")
    conflicts = detect_conflicts([a, b])
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == "insufficient_transition_time"


def test_comfortable_gap_is_not_flagged():
    a = _section("00000000-0000-0000-0000-0000000000a1", "monday", "10:00", "11:15")
    b = _section("00000000-0000-0000-0000-0000000000a2", "monday", "11:45", "13:00", code="CS 2000")
    assert detect_conflicts([a, b]) == []


def test_no_meetings_never_conflicts():
    a = SectionRead(
        id="00000000-0000-0000-0000-0000000000a1", section_number="001", delivery_mode="online",
        seats_total=30, seats_available=10, course=_course(),
        term={"id": "00000000-0000-0000-0000-000000000003", "name": "Fall 2026", "year": 2026, "season": "fall", "is_active_for_planning": True},
        professor=None, meetings=[],
    )
    b = _section("00000000-0000-0000-0000-0000000000a2", "monday", "10:00", "11:15", code="CS 2000")
    assert detect_conflicts([a, b]) == []
