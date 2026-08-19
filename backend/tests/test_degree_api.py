import uuid

from app.models import Course, Department, DegreeProgram, University
from app.models.course import CourseLevel
from app.models.degree import CoursePrerequisite, DegreeRequirementCourse, DegreeRequirementGroup


def _register_and_login(client, email="student@example.edu"):
    client.post("/api/v1/auth/register", json={"email": email, "password": "supersecret123"})
    login = client.post("/api/v1/auth/login", json={"email": email, "password": "supersecret123"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _seed_degree(db_session):
    university = University(id=uuid.uuid4(), name="Test University", short_name=f"TU-{uuid.uuid4().hex[:6]}")
    db_session.add(university)
    db_session.flush()

    department = Department(id=uuid.uuid4(), university_id=university.id, code="CS", name="Computer Science")
    db_session.add(department)
    db_session.flush()

    def make_course(code):
        c = Course(
            id=uuid.uuid4(), university_id=university.id, department_id=department.id,
            code=code, title=code, credit_hours=3, level=CourseLevel.UNDERGRADUATE,
        )
        db_session.add(c)
        db_session.flush()
        return c

    course_a = make_course("CS 1000")  # no prereqs
    course_b = make_course("CS 2000")  # requires CS 1000
    course_c = make_course("CS 3000")  # requires CS 2000
    elective_1 = make_course("CS 4000")
    elective_2 = make_course("CS 4001")

    db_session.add(CoursePrerequisite(id=uuid.uuid4(), course_id=course_b.id, group_number=1, prerequisite_course_id=course_a.id))
    db_session.add(CoursePrerequisite(id=uuid.uuid4(), course_id=course_c.id, group_number=1, prerequisite_course_id=course_b.id))

    program = DegreeProgram(id=uuid.uuid4(), university_id=university.id, department_id=department.id, name="B.S. Test", catalog_year=2026)
    db_session.add(program)
    db_session.flush()

    core = DegreeRequirementGroup(id=uuid.uuid4(), degree_program_id=program.id, name="Core", required_count=2)
    db_session.add(core)
    db_session.flush()
    for c in [course_a, course_b]:
        db_session.add(DegreeRequirementCourse(id=uuid.uuid4(), requirement_group_id=core.id, course_id=c.id))

    electives = DegreeRequirementGroup(id=uuid.uuid4(), degree_program_id=program.id, name="Electives", required_count=1)
    db_session.add(electives)
    db_session.flush()
    for c in [elective_1, elective_2]:
        db_session.add(DegreeRequirementCourse(id=uuid.uuid4(), requirement_group_id=electives.id, course_id=c.id))

    db_session.commit()
    return {
        "program": program, "course_a": course_a, "course_b": course_b, "course_c": course_c,
        "elective_1": elective_1, "elective_2": elective_2,
    }


def test_get_degree_program(client, db_session):
    data = _seed_degree(db_session)
    response = client.get(f"/api/v1/degrees/{data['program'].id}")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "B.S. Test"
    assert {g["name"] for g in body["requirement_groups"]} == {"Core", "Electives"}


def test_course_prerequisites_endpoint(client, db_session):
    data = _seed_degree(db_session)
    response = client.get(f"/api/v1/courses/{data['course_c'].id}/prerequisites")
    assert response.status_code == 200
    body = response.json()
    assert len(body["groups"]) == 1
    assert body["groups"][0]["options"][0]["code"] == "CS 2000"


def test_progress_requires_enrollment(client, db_session):
    _seed_degree(db_session)
    headers = _register_and_login(client)
    response = client.get("/api/v1/degree/progress", headers=headers)
    assert response.status_code == 400


def test_full_degree_flow(client, db_session):
    data = _seed_degree(db_session)
    headers = _register_and_login(client, email="flow@example.edu")

    enroll = client.post(
        "/api/v1/degree/enroll", json={"degree_program_id": str(data["program"].id)}, headers=headers
    )
    assert enroll.status_code == 204

    add = client.post(
        "/api/v1/degree/completed-courses",
        json={"course_id": str(data["course_a"].id), "grade": "A"},
        headers=headers,
    )
    assert add.status_code == 201

    progress = client.get("/api/v1/degree/progress", headers=headers)
    assert progress.status_code == 200
    body = progress.json()
    core_group = next(g for g in body["groups"] if g["name"] == "Core")
    assert core_group["completed_count"] == 1
    assert core_group["required_count"] == 2
    assert core_group["complete"] is False
    assert "CS 1000" in core_group["completed_course_codes"]

    eligibility_b = client.get(f"/api/v1/courses/{data['course_b'].id}/eligibility", headers=headers)
    assert eligibility_b.status_code == 200
    assert eligibility_b.json()["eligible"] is True

    eligibility_c = client.get(f"/api/v1/courses/{data['course_c'].id}/eligibility", headers=headers)
    assert eligibility_c.status_code == 200
    body_c = eligibility_c.json()
    assert body_c["eligible"] is False
    assert body_c["missing"] == [["CS 2000"]]

    next_courses = client.get("/api/v1/degree/next-courses", headers=headers)
    assert next_courses.status_code == 200
    suggestions = {s["course"]["code"]: s for s in next_courses.json()}
    assert "CS 1000" not in suggestions  # already completed
    assert suggestions["CS 2000"]["eligible"] is True
    assert suggestions["CS 4000"]["requirement_group"] == "Electives"


def test_completed_courses_are_idempotent_per_pair(client, db_session):
    data = _seed_degree(db_session)
    headers = _register_and_login(client, email="dup@example.edu")
    payload = {"course_id": str(data["course_a"].id)}
    first = client.post("/api/v1/degree/completed-courses", json=payload, headers=headers)
    assert first.status_code == 201
    second = client.post("/api/v1/degree/completed-courses", json=payload, headers=headers)
    assert second.status_code == 409
