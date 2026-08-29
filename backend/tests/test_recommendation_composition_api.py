import uuid

from app.models import (
    Course,
    CourseTopic,
    Department,
    GradeHistory,
    Professor,
    ProfessorRating,
    Section,
    Term,
    University,
)
from app.models.course import CourseLevel
from app.models.section import DeliveryMode
from app.models.term import Season


def _grade_kwargs(bucket, count):
    kwargs = {b: 0 for b in [
        "a_plus", "a", "a_minus", "b_plus", "b", "b_minus",
        "c_plus", "c", "c_minus", "d_plus", "d", "d_minus", "f",
    ]}
    kwargs[bucket] = count
    return kwargs


def _seed_mixed_delivery_courses(db_session, online_count=3, in_person_count=3):
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
            id=uuid.uuid4(), professor_id=professor.id, overall_rating=4.5, num_ratings=40,
            source_type="student_reported", confidence=0.8,
        )
    )

    term = Term(
        id=uuid.uuid4(), university_id=university.id, name="Fall 2026", year=2026, season=Season.FALL,
        is_active_for_planning=True,
    )
    db_session.add(term)
    db_session.flush()

    modes = [DeliveryMode.ONLINE] * online_count + [DeliveryMode.IN_PERSON] * in_person_count
    for i, mode in enumerate(modes):
        course = Course(
            id=uuid.uuid4(), university_id=university.id, department_id=department.id,
            code=f"CS {2000 + i}", title=f"Python Topics {i}", credit_hours=3,
            level=CourseLevel.UNDERGRADUATE,
        )
        db_session.add(course)
        db_session.flush()
        db_session.add(CourseTopic(id=uuid.uuid4(), course_id=course.id, topic="python"))

        section = Section(
            id=uuid.uuid4(), course_id=course.id, term_id=term.id, professor_id=professor.id,
            section_number="001", delivery_mode=mode, seats_total=30, seats_available=10,
        )
        db_session.add(section)
        db_session.flush()
        db_session.add(
            GradeHistory(
                id=uuid.uuid4(), course_id=course.id, professor_id=professor.id, term_id=term.id,
                withdrawals=0, source_type="historical", **_grade_kwargs("a", 30),
            )
        )

    db_session.commit()


def test_recommendations_composes_requested_mode_counts(client, db_session):
    _seed_mixed_delivery_courses(db_session, online_count=3, in_person_count=3)
    response = client.post(
        "/api/v1/recommendations/courses",
        json={"query": "python course, 2 online and 2 in_person"},
    )
    assert response.status_code == 200
    body = response.json()
    modes = [r["section"]["delivery_mode"] for r in body["recommendations"]]
    assert modes.count("online") == 2
    assert modes.count("in_person") == 2


def test_recommendations_composition_shortfall_reported(client, db_session):
    _seed_mixed_delivery_courses(db_session, online_count=1, in_person_count=3)
    response = client.post(
        "/api/v1/recommendations/courses",
        json={"query": "python course, 2 online and 2 in_person"},
    )
    assert response.status_code == 200
    body = response.json()
    modes = [r["section"]["delivery_mode"] for r in body["recommendations"]]
    assert modes.count("online") == 1
    assert modes.count("in_person") == 2
    assert any("online" in note.lower() and "1" in note for note in body["notes"])


def test_chat_search_intent_reports_correct_mode_mix(client, db_session):
    _seed_mixed_delivery_courses(db_session, online_count=2, in_person_count=2)
    response = client.post(
        "/api/v1/ai/chat",
        json={"message": "suggest me 2 online and 2 in_person python courses", "history": []},
    )
    assert response.status_code == 200
    body = response.json()
    reply_lower = body["reply"].lower()
    assert reply_lower.count("| online |") == 2
    assert reply_lower.count("| in_person |") == 2


def test_schedule_generate_with_mode_counts(client, db_session):
    _seed_mixed_delivery_courses(db_session, online_count=3, in_person_count=3)
    response = client.post(
        "/api/v1/schedule/generate",
        json={"query": "python courses, 2 online and 2 in_person", "min_credits": 12, "max_credits": 12},
    )
    assert response.status_code == 200
    body = response.json()
    best = body["schedules"]["best_overall"]
    assert best is not None
    modes = [s["delivery_mode"] for s in best["sections"]]
    assert modes.count("online") >= 2
    assert modes.count("in_person") >= 2
