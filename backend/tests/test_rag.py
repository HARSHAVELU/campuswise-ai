import uuid

from app.ingestion.syllabus_ingestion import ingest_syllabus
from app.models import Course, Department, Professor, Term, University
from app.models.course import CourseLevel
from app.models.term import Season

SYLLABUS_TEXT = """Course Policies for CS 4375 - Introduction to Machine Learning

Attendance is not mandatory but strongly encouraged. Class participation counts for 5% of the final grade.

Grading Breakdown: Homework assignments are worth 30% of the final grade. There is a midterm exam worth 20% and a comprehensive final exam worth 35%. A group project counts for the remaining 10%.

Exam Format: The midterm exam is administered online through the course portal and is open-book. The final exam is also online, proctored via Honorlock, and closed-book.

Late Policy: Late assignments are accepted up to 48 hours after the deadline with a 10% per day penalty. No submissions are accepted after 48 hours without prior approval.
"""


def _seed_syllabus(db_session):
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

    professor = Professor(id=uuid.uuid4(), university_id=university.id, department_id=department.id, name="Dr. Test")
    db_session.add(professor)
    db_session.flush()

    term = Term(
        id=uuid.uuid4(), university_id=university.id, name="Fall 2025", year=2025, season=Season.FALL,
    )
    db_session.add(term)
    db_session.flush()

    syllabus = ingest_syllabus(
        db_session,
        university_id=university.id,
        course_id=course.id,
        professor_id=professor.id,
        term_id=term.id,
        title="CS 4375 Fall 2025 Syllabus",
        source_document="CS4375_Fall2025.pdf",
        raw_text=SYLLABUS_TEXT,
    )
    db_session.commit()
    return course, professor, syllabus


def test_ingestion_creates_chunks_with_embeddings(db_session):
    course, professor, syllabus = _seed_syllabus(db_session)
    assert len(syllabus.chunks) >= 2
    for chunk in syllabus.chunks:
        assert len(chunk.embedding) > 0


def test_rag_query_finds_exam_format_and_cites_source(client, db_session):
    course, professor, _ = _seed_syllabus(db_session)
    response = client.post(
        "/api/v1/rag/query",
        json={"query": "Is the final exam online?", "course_id": str(course.id)},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["chunks_considered"] > 0
    assert body["confidence"] in {"low", "medium", "high"}
    assert len(body["citations"]) > 0
    assert body["citations"][0]["source_document"] == "CS4375_Fall2025.pdf"
    assert "online" in body["answer"].lower() or "online" in body["citations"][0]["excerpt"].lower()
    assert body["answer_source"] == "excerpt_only"  # no ANTHROPIC_API_KEY in test environment


def test_rag_query_no_syllabus_data_returns_none_confidence(client, db_session):
    response = client.post(
        "/api/v1/rag/query", json={"query": "Does this professor take attendance?"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["confidence"] == "none"
    assert body["chunks_considered"] == 0
    assert body["citations"] == []
    assert "not available" in body["answer"].lower() or "no syllabus" in body["answer"].lower()


def test_rag_query_scoped_to_course_excludes_other_courses(client, db_session):
    course, professor, _ = _seed_syllabus(db_session)
    other_course_id = uuid.uuid4()
    response = client.post(
        "/api/v1/rag/query",
        json={"query": "late policy", "course_id": str(other_course_id)},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["chunks_considered"] == 0
