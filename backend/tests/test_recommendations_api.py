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


def _seed_recommendation_scenario(db_session):
    university = University(id=uuid.uuid4(), name="Test University", short_name=f"TU-{uuid.uuid4().hex[:6]}")
    db_session.add(university)
    db_session.flush()

    department = Department(id=uuid.uuid4(), university_id=university.id, code="CS", name="Computer Science")
    db_session.add(department)
    db_session.flush()

    course = Course(
        id=uuid.uuid4(),
        university_id=university.id,
        department_id=department.id,
        code="CS 4375",
        title="Introduction to Machine Learning",
        credit_hours=3,
        level=CourseLevel.UNDERGRADUATE,
    )
    db_session.add(course)
    db_session.flush()
    db_session.add(CourseTopic(id=uuid.uuid4(), course_id=course.id, topic="python"))

    professor_good = Professor(
        id=uuid.uuid4(), university_id=university.id, department_id=department.id, name="Dr. Good"
    )
    professor_low = Professor(
        id=uuid.uuid4(), university_id=university.id, department_id=department.id, name="Dr. LowRated"
    )
    db_session.add_all([professor_good, professor_low])
    db_session.flush()

    db_session.add(
        ProfessorRating(
            id=uuid.uuid4(), professor_id=professor_good.id, overall_rating=4.7,
            difficulty_rating=2.0, num_ratings=60, source_type="student_reported", confidence=0.8,
        )
    )
    db_session.add(
        ProfessorRating(
            id=uuid.uuid4(), professor_id=professor_low.id, overall_rating=2.9,
            difficulty_rating=4.0, num_ratings=60, source_type="student_reported", confidence=0.8,
        )
    )

    term = Term(
        id=uuid.uuid4(), university_id=university.id, name="Fall 2026", year=2026, season=Season.FALL,
        is_active_for_planning=True,
    )
    db_session.add(term)
    db_session.flush()

    section_online_good = Section(
        id=uuid.uuid4(), course_id=course.id, term_id=term.id, professor_id=professor_good.id,
        section_number="001", delivery_mode=DeliveryMode.ONLINE, seats_total=30, seats_available=10,
    )
    section_in_person_low = Section(
        id=uuid.uuid4(), course_id=course.id, term_id=term.id, professor_id=professor_low.id,
        section_number="002", delivery_mode=DeliveryMode.IN_PERSON, seats_total=30, seats_available=10,
    )
    db_session.add_all([section_online_good, section_in_person_low])
    db_session.flush()

    db_session.add(
        SectionMeeting(
            id=uuid.uuid4(), section_id=section_in_person_low.id, day_of_week=DayOfWeek.FRIDAY,
            start_time=datetime.time(9, 0), end_time=datetime.time(10, 15),
        )
    )

    for section, professor, bucket in [
        (section_online_good, professor_good, "a_plus"),
        (section_in_person_low, professor_low, "c"),
    ]:
        grade_kwargs = {b: 0 for b in [
            "a_plus", "a", "a_minus", "b_plus", "b", "b_minus",
            "c_plus", "c", "c_minus", "d_plus", "d", "d_minus", "f",
        ]}
        grade_kwargs[bucket] = 25
        db_session.add(
            GradeHistory(
                id=uuid.uuid4(), course_id=course.id, professor_id=professor.id, term_id=term.id,
                withdrawals=0, source_type="historical", **grade_kwargs,
            )
        )

    db_session.commit()
    return section_online_good, section_in_person_low


def test_recommendations_filters_out_friday_and_low_rating(client, db_session):
    _seed_recommendation_scenario(db_session)
    response = client.post(
        "/api/v1/recommendations/courses",
        json={"query": "I want a python course, no Friday classes, professor rating above 4."},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["recommendations"]) == 1
    rec = body["recommendations"][0]
    assert rec["section"]["delivery_mode"] == "online"
    assert rec["fit_score"] >= 80
    assert any("excluded" in note.lower() for note in body["notes"])


def test_recommendations_no_topic_match_returns_helpful_note(client, db_session):
    _seed_recommendation_scenario(db_session)
    response = client.post(
        "/api/v1/recommendations/courses", json={"query": "Find me a marketing class."}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["recommendations"] == []
    assert any("marketing" in note for note in body["notes"])
