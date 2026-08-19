import datetime
import uuid

from app.models import (
    Course,
    CourseTopic,
    Department,
    GradeHistory,
    Professor,
    ProfessorRating,
    Section,
    SectionMeeting,
    Term,
    University,
)
from app.models.course import CourseLevel
from app.models.section import DayOfWeek, DeliveryMode
from app.models.term import Season


def _grade_kwargs(bucket, count):
    kwargs = {b: 0 for b in [
        "a_plus", "a", "a_minus", "b_plus", "b", "b_minus",
        "c_plus", "c", "c_minus", "d_plus", "d", "d_minus", "f",
    ]}
    kwargs[bucket] = count
    return kwargs


def _seed_two_non_conflicting_python_courses(db_session):
    university = University(id=uuid.uuid4(), name="Test University", short_name=f"TU-{uuid.uuid4().hex[:6]}")
    db_session.add(university)
    db_session.flush()

    department = Department(id=uuid.uuid4(), university_id=university.id, code="CS", name="Computer Science")
    db_session.add(department)
    db_session.flush()

    professor = Professor(id=uuid.uuid4(), university_id=university.id, department_id=department.id, name="Dr. Test")
    db_session.add(professor)
    db_session.flush()
    db_session.add(
        ProfessorRating(
            id=uuid.uuid4(), professor_id=professor.id, overall_rating=4.5, difficulty_rating=2.5,
            num_ratings=40, source_type="student_reported", confidence=0.8,
        )
    )

    term = Term(
        id=uuid.uuid4(), university_id=university.id, name="Fall 2026", year=2026, season=Season.FALL,
        is_active_for_planning=True,
    )
    db_session.add(term)
    db_session.flush()

    sections = []
    for i, (day, code) in enumerate([(DayOfWeek.MONDAY, "CS 1000"), (DayOfWeek.WEDNESDAY, "CS 2000")]):
        course = Course(
            id=uuid.uuid4(), university_id=university.id, department_id=department.id,
            code=code, title=f"Python Course {i}", credit_hours=3, level=CourseLevel.UNDERGRADUATE,
        )
        db_session.add(course)
        db_session.flush()
        db_session.add(CourseTopic(id=uuid.uuid4(), course_id=course.id, topic="python"))

        section = Section(
            id=uuid.uuid4(), course_id=course.id, term_id=term.id, professor_id=professor.id,
            section_number="001", delivery_mode=DeliveryMode.IN_PERSON, seats_total=30, seats_available=10,
        )
        db_session.add(section)
        db_session.flush()
        db_session.add(
            SectionMeeting(
                id=uuid.uuid4(), section_id=section.id, day_of_week=day,
                start_time=datetime.time(9, 0), end_time=datetime.time(10, 15),
            )
        )
        db_session.add(
            GradeHistory(
                id=uuid.uuid4(), course_id=course.id, professor_id=professor.id, term_id=term.id,
                withdrawals=0, source_type="historical", **_grade_kwargs("a", 30),
            )
        )
        sections.append(section)

    db_session.commit()
    return sections


def test_schedule_generate_returns_all_five_strategies(client, db_session):
    _seed_two_non_conflicting_python_courses(db_session)
    response = client.post(
        "/api/v1/schedule/generate",
        json={"query": "python courses", "min_credits": 3, "max_credits": 6},
    )
    assert response.status_code == 200
    body = response.json()
    assert set(body["schedules"].keys()) == {
        "best_overall", "best_professors", "fewest_campus_days", "best_grades", "online_heavy",
    }
    best_overall = body["schedules"]["best_overall"]
    assert best_overall is not None
    assert 3 <= best_overall["total_credits"] <= 6
    assert len(best_overall["sections"]) >= 1


def test_schedule_generate_infeasible_credit_range_reports_note(client, db_session):
    _seed_two_non_conflicting_python_courses(db_session)
    response = client.post(
        "/api/v1/schedule/generate",
        json={"query": "python courses", "min_credits": 20, "max_credits": 25},
    )
    assert response.status_code == 200
    body = response.json()
    assert all(v is None for v in body["schedules"].values())
    assert any("no feasible schedule" in note.lower() for note in body["notes"])


def test_schedule_validate_detects_conflict(client, db_session):
    sections = _seed_two_non_conflicting_python_courses(db_session)
    response = client.post(
        "/api/v1/schedule/validate",
        json={"section_ids": [str(s.id) for s in sections]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["is_valid"] is True
    assert body["conflicts"] == []


def test_schedule_validate_with_unknown_section_id_ignores_it(client, db_session):
    response = client.post(
        "/api/v1/schedule/validate", json={"section_ids": [str(uuid.uuid4())]}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["conflicts"] == []
    assert body["is_valid"] is True
