import uuid

from app.models import Course, CourseTopic, Department, Professor, ProfessorRating, University


def _seed(db_session):
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
    )
    db_session.add(course)
    db_session.flush()
    db_session.add(CourseTopic(id=uuid.uuid4(), course_id=course.id, topic="python"))

    professor = Professor(
        id=uuid.uuid4(), university_id=university.id, department_id=department.id, name="Dr. High Rating"
    )
    db_session.add(professor)
    db_session.flush()
    db_session.add(
        ProfessorRating(
            id=uuid.uuid4(),
            professor_id=professor.id,
            overall_rating=4.6,
            num_ratings=50,
            source_type="student_reported",
            confidence=0.8,
        )
    )
    db_session.commit()


def test_ai_search_finds_topic_and_parses_constraints(client, db_session):
    _seed(db_session)
    response = client.post("/api/v1/ai/search", json={"query": "Find me a Python class."})
    assert response.status_code == 200
    body = response.json()
    assert body["parsed"]["topic"] == "python"
    assert body["parsed"]["parser_source"] == "rule_based"
    assert len(body["courses"]) == 1
    assert body["courses"][0]["code"] == "CS 4375"


def test_ai_search_applies_rating_constraint_to_professor_discovery(client, db_session):
    _seed(db_session)
    response = client.post(
        "/api/v1/ai/search", json={"query": "I want a professor rated above 4."}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["parsed"]["hard_constraints"]["minimum_professor_rating"] == 4.0
    assert len(body["professors"]) == 1
    assert body["professors"][0]["name"] == "Dr. High Rating"


def test_ai_search_no_match_produces_helpful_note(client, db_session):
    _seed(db_session)
    response = client.post("/api/v1/ai/search", json={"query": "Find me a marketing class."})
    assert response.status_code == 200
    body = response.json()
    assert body["courses"] == []
    assert any("marketing" in note for note in body["notes"])


def test_ai_search_rejects_empty_query(client, db_session):
    response = client.post("/api/v1/ai/search", json={"query": ""})
    assert response.status_code == 422
