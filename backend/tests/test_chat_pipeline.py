import uuid

from app.agents.chat_pipeline import _extract_credit_range, classify_intent
from app.ingestion.syllabus_ingestion import ingest_syllabus
from app.models import (
    Course,
    CourseTopic,
    Department,
    Professor,
    ProfessorRating,
    Section,
    Term,
    University,
)
from app.models.course import CourseLevel
from app.models.section import DeliveryMode
from app.models.term import Season


def test_classify_intent_syllabus_keywords():
    assert classify_intent("Does CS 4375 have a group project?") == "syllabus"
    assert classify_intent("Are the exams open book?") == "syllabus"
    assert classify_intent("What is the attendance policy?") == "syllabus"


def test_classify_intent_schedule_keywords():
    assert classify_intent("Build me a 12 credit schedule with no Friday classes") == "schedule"
    assert classify_intent("I need 15 credits this semester") == "schedule"


def test_classify_intent_defaults_to_search():
    assert classify_intent("Find me a python class") == "search"
    assert classify_intent("I want an easy AI elective") == "search"


def test_extract_credit_range_single_number():
    assert _extract_credit_range("I need 12 credits") == (12, 12)


def test_extract_credit_range_range():
    assert _extract_credit_range("give me a 12-15 credit schedule") == (12, 15)


def test_extract_credit_range_default_when_unspecified():
    assert _extract_credit_range("build me a schedule") == (12, 15)


def _seed_course_with_syllabus(db_session):
    university = University(id=uuid.uuid4(), name="Test University", short_name=f"TU-{uuid.uuid4().hex[:6]}")
    db_session.add(university)
    db_session.flush()

    department = Department(id=uuid.uuid4(), university_id=university.id, code="CS", name="Computer Science")
    db_session.add(department)
    db_session.flush()

    course = Course(
        id=uuid.uuid4(), university_id=university.id, department_id=department.id,
        code="CS 4375", title="Introduction to Machine Learning", credit_hours=3,
        level=CourseLevel.UNDERGRADUATE,
    )
    db_session.add(course)
    db_session.flush()
    db_session.add(CourseTopic(id=uuid.uuid4(), course_id=course.id, topic="machine learning"))

    professor = Professor(id=uuid.uuid4(), university_id=university.id, department_id=department.id, name="Dr. Test")
    db_session.add(professor)
    db_session.flush()
    db_session.add(
        ProfessorRating(
            id=uuid.uuid4(), professor_id=professor.id, overall_rating=4.5, num_ratings=40,
            source_type="student_reported", confidence=0.8,
        )
    )

    term = Term(id=uuid.uuid4(), university_id=university.id, name="Fall 2025", year=2025, season=Season.FALL)
    db_session.add(term)
    db_session.flush()

    active_term = Term(
        id=uuid.uuid4(), university_id=university.id, name="Fall 2026", year=2026,
        season=Season.FALL, is_active_for_planning=True,
    )
    db_session.add(active_term)
    db_session.flush()
    db_session.add(
        Section(
            id=uuid.uuid4(), course_id=course.id, term_id=active_term.id, professor_id=professor.id,
            section_number="001", delivery_mode=DeliveryMode.ONLINE, seats_total=30, seats_available=10,
        )
    )

    ingest_syllabus(
        db_session,
        university_id=university.id,
        course_id=course.id,
        professor_id=professor.id,
        term_id=term.id,
        title="CS 4375 Syllabus",
        source_document="CS4375_Fall2025.pdf",
        raw_text=(
            "Exam Format: The final exam is administered online through the course portal "
            "and is open-book.\n\nLate Policy: Late work loses 10% per day."
        ),
    )
    db_session.commit()
    return course


def test_chat_syllabus_intent_resolves_course_by_code(client, db_session):
    _seed_course_with_syllabus(db_session)
    response = client.post(
        "/api/v1/ai/chat", json={"message": "Is the final exam for CS 4375 online?", "history": []}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "syllabus"
    assert "CS4375_Fall2025.pdf" in body["reply"] or "online" in body["reply"].lower()
    assert body["reply_source"] == "template"  # no ANTHROPIC_API_KEY in test environment


def test_chat_syllabus_intent_clarifies_when_course_not_found(client, db_session):
    response = client.post(
        "/api/v1/ai/chat", json={"message": "What is the attendance policy?", "history": []}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "clarify"
    assert "which course" in body["reply"].lower()


def test_chat_search_intent_finds_course(client, db_session):
    _seed_course_with_syllabus(db_session)
    response = client.post(
        "/api/v1/ai/chat", json={"message": "Find me a machine learning class", "history": []}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["intent"] == "search"
    assert "CS 4375" in body["reply"]


def test_chat_maintains_conversation_history_without_error(client, db_session):
    _seed_course_with_syllabus(db_session)
    response = client.post(
        "/api/v1/ai/chat",
        json={
            "message": "Only online this time",
            "history": [
                {"role": "user", "content": "Find me a machine learning class"},
                {"role": "assistant", "content": "Here's what I found: CS 4375..."},
            ],
        },
    )
    assert response.status_code == 200
