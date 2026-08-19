import uuid

from app.ingestion.syllabus_ingestion import ingest_syllabus
from app.models import Course, Department, Professor, Term, University
from app.models.course import CourseLevel
from app.models.term import Season

SYLLABUS_TEXT = """Course Policies for TEST 1000 - Test Course

Attendance is required. Grading Breakdown: Homework is worth 40% and the final exam is worth 60%.

Exam Format: The final exam is administered in person and is closed-book.

Late Policy: Late homework loses 10% per day."""


def _seed(db_session):
    university = University(id=uuid.uuid4(), name="Test University", short_name=f"TU-{uuid.uuid4().hex[:6]}")
    db_session.add(university)
    db_session.flush()

    department = Department(id=uuid.uuid4(), university_id=university.id, code="CS", name="Computer Science")
    db_session.add(department)
    db_session.flush()

    course = Course(
        id=uuid.uuid4(), university_id=university.id, department_id=department.id,
        code="TEST 1000", title="Test Course", credit_hours=3, level=CourseLevel.UNDERGRADUATE,
    )
    db_session.add(course)
    db_session.flush()

    professor = Professor(id=uuid.uuid4(), university_id=university.id, department_id=department.id, name="Dr. Test")
    db_session.add(professor)
    db_session.flush()

    term = Term(id=uuid.uuid4(), university_id=university.id, name="Fall 2025", year=2025, season=Season.FALL)
    db_session.add(term)
    db_session.flush()

    ingest_syllabus(
        db_session,
        university_id=university.id,
        course_id=course.id,
        professor_id=professor.id,
        term_id=term.id,
        title="TEST 1000 Syllabus",
        source_document="TEST1000_Fall2025.pdf",
        raw_text=SYLLABUS_TEXT,
    )
    db_session.commit()
    return course, professor


def test_get_course_assessment_returns_extracted_data(client, db_session):
    course, professor = _seed(db_session)
    response = client.get(f"/api/v1/assessment/course/{course.id}")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["final_format"] == "in_person"
    assert body[0]["final_open_book"] is False
    assert body[0]["source_document"] == "TEST1000_Fall2025.pdf"
    assert body[0]["source_term"] == "Fall 2025"
    assert body[0]["extraction_method"] == "rule_based"


def test_get_professor_assessment_returns_extracted_data(client, db_session):
    course, professor = _seed(db_session)
    response = client.get(f"/api/v1/assessment/professor/{professor.id}")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["course_id"] == str(course.id)


def test_get_assessment_for_course_with_no_syllabus_returns_empty(client, db_session):
    response = client.get(f"/api/v1/assessment/course/{uuid.uuid4()}")
    assert response.status_code == 200
    assert response.json() == []
