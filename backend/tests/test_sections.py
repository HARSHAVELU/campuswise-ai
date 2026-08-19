import datetime
import uuid

from app.models import Course, Department, Section, SectionMeeting, Term, University
from app.models.course import CourseLevel
from app.models.section import DayOfWeek, DeliveryMode
from app.models.term import Season


def _make_section(db_session, delivery_mode=DeliveryMode.ONLINE):
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
        code="CS 1336",
        title="Programming Fundamentals",
        credit_hours=3,
        level=CourseLevel.UNDERGRADUATE,
    )
    db_session.add(course)
    db_session.flush()

    term = Term(
        id=uuid.uuid4(),
        university_id=university.id,
        name="Fall 2026",
        year=2026,
        season=Season.FALL,
        is_active_for_planning=True,
    )
    db_session.add(term)
    db_session.flush()

    section = Section(
        id=uuid.uuid4(),
        course_id=course.id,
        term_id=term.id,
        section_number="001",
        delivery_mode=delivery_mode,
        seats_total=30,
        seats_available=10,
    )
    db_session.add(section)
    db_session.flush()

    if delivery_mode != DeliveryMode.ONLINE:
        db_session.add(
            SectionMeeting(
                id=uuid.uuid4(),
                section_id=section.id,
                day_of_week=DayOfWeek.TUESDAY,
                start_time=datetime.time(11, 0),
                end_time=datetime.time(12, 15),
            )
        )
    db_session.commit()
    return section


def test_list_sections(client, db_session):
    _make_section(db_session)
    response = client.get("/api/v1/sections")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["delivery_mode"] == "online"
    assert body[0]["course"]["code"] == "CS 1336"


def test_filter_sections_by_delivery_mode(client, db_session):
    _make_section(db_session, delivery_mode=DeliveryMode.ONLINE)
    _make_section(db_session, delivery_mode=DeliveryMode.IN_PERSON)
    response = client.get("/api/v1/sections", params={"delivery_mode": "in_person"})
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["delivery_mode"] == "in_person"
    assert len(body[0]["meetings"]) == 1
