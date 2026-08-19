import uuid

from app.models import Department, Professor, ProfessorRating, University


def _make_professor(db_session, name="Dr. Elena Marquez", overall_rating=4.5):
    university = University(id=uuid.uuid4(), name="Test University", short_name=f"TU-{uuid.uuid4().hex[:6]}")
    db_session.add(university)
    db_session.flush()

    department = Department(id=uuid.uuid4(), university_id=university.id, code="CS", name="Computer Science")
    db_session.add(department)
    db_session.flush()

    professor = Professor(
        id=uuid.uuid4(),
        university_id=university.id,
        department_id=department.id,
        name=name,
        title="Associate Professor",
    )
    db_session.add(professor)
    db_session.flush()

    rating = ProfessorRating(
        id=uuid.uuid4(),
        professor_id=professor.id,
        overall_rating=overall_rating,
        teaching_rating=overall_rating,
        difficulty_rating=3.0,
        would_take_again_pct=85.0,
        num_ratings=42,
        source_type="student_reported",
        confidence=0.8,
    )
    db_session.add(rating)
    db_session.commit()
    return university, department, professor


def test_list_professors(client, db_session):
    _make_professor(db_session)
    response = client.get("/api/v1/professors")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["rating"]["overall_rating"] == 4.5


def test_list_professors_min_rating_filter(client, db_session):
    _make_professor(db_session, name="Dr. Low Rating", overall_rating=3.0)
    _make_professor(db_session, name="Dr. High Rating", overall_rating=4.8)
    response = client.get("/api/v1/professors", params={"min_rating": 4.0})
    assert response.status_code == 200
    names = {p["name"] for p in response.json()}
    assert names == {"Dr. High Rating"}


def test_get_professor_not_found(client, db_session):
    response = client.get(f"/api/v1/professors/{uuid.uuid4()}")
    assert response.status_code == 404


def test_professor_grades_no_data_returns_nulls(client, db_session):
    _, _, professor = _make_professor(db_session)
    response = client.get(f"/api/v1/professors/{professor.id}/grades")
    assert response.status_code == 200
    body = response.json()
    assert body["total_students"] == 0
    assert body["mean_gpa"] is None
    assert "does not guarantee" in body["disclaimer"]
