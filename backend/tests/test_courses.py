import uuid

from app.models import Course, CourseTopic, Department, University
from app.models.course import CourseLevel


def _make_course(db_session, code="CS 4375", title="Introduction to Machine Learning", topics=None):
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
        code=code,
        title=title,
        description="A course about " + title,
        credit_hours=3,
        level=CourseLevel.UNDERGRADUATE,
    )
    db_session.add(course)
    db_session.flush()

    for topic in topics or []:
        db_session.add(CourseTopic(id=uuid.uuid4(), course_id=course.id, topic=topic))
    db_session.commit()
    return university, department, course


def test_list_courses(client, db_session):
    _make_course(db_session, topics=["python", "machine learning"])
    response = client.get("/api/v1/courses")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["code"] == "CS 4375"
    assert body[0]["department"]["code"] == "CS"


def test_get_course_by_id(client, db_session):
    _, _, course = _make_course(db_session)
    response = client.get(f"/api/v1/courses/{course.id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Introduction to Machine Learning"


def test_get_course_not_found(client, db_session):
    response = client.get(f"/api/v1/courses/{uuid.uuid4()}")
    assert response.status_code == 404


def test_search_courses_matches_topic(client, db_session):
    _make_course(db_session, topics=["python", "machine learning"])
    response = client.get("/api/v1/courses/search", params={"q": "python"})
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_search_courses_matches_title(client, db_session):
    _make_course(db_session, code="CS 4395", title="Natural Language Processing")
    response = client.get("/api/v1/courses/search", params={"q": "natural language"})
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_search_courses_no_match(client, db_session):
    _make_course(db_session, topics=["python"])
    response = client.get("/api/v1/courses/search", params={"q": "underwater basket weaving"})
    assert response.status_code == 200
    assert response.json() == []
