import uuid

from app.models.course import Course, CourseLevel
from app.models.degree import CoursePrerequisite
from app.services.prerequisite_engine import check_eligibility


def _course(code: str) -> Course:
    return Course(
        id=uuid.uuid4(), university_id=uuid.uuid4(), department_id=uuid.uuid4(),
        code=code, title=code, credit_hours=3, level=CourseLevel.UNDERGRADUATE,
    )


def _prereq(course: Course, group_number: int, prerequisite: Course) -> CoursePrerequisite:
    row = CoursePrerequisite(
        id=uuid.uuid4(), course_id=course.id, group_number=group_number,
        prerequisite_course_id=prerequisite.id,
    )
    row.prerequisite_course = prerequisite
    return row


def test_no_prerequisites_is_always_eligible():
    result = check_eligibility([], completed_course_ids=set())
    assert result.eligible is True
    assert result.missing == []


def test_single_and_prerequisite_satisfied():
    course_a = _course("CS 1336")
    course_c = _course("CS 2336")
    rows = [_prereq(course_c, 1, course_a)]
    result = check_eligibility(rows, completed_course_ids={course_a.id})
    assert result.eligible is True


def test_single_and_prerequisite_not_satisfied():
    course_a = _course("CS 1336")
    course_c = _course("CS 2336")
    rows = [_prereq(course_c, 1, course_a)]
    result = check_eligibility(rows, completed_course_ids=set())
    assert result.eligible is False
    assert result.missing[0].options == ["CS 1336"]


def test_and_of_two_groups_requires_both():
    course_a = _course("CS 2336")
    course_b = _course("MATH 3315")
    course_c = _course("CS 4375")
    rows = [_prereq(course_c, 1, course_a), _prereq(course_c, 2, course_b)]

    # only A completed -> still missing group 2
    result = check_eligibility(rows, completed_course_ids={course_a.id})
    assert result.eligible is False
    assert len(result.missing) == 1
    assert result.missing[0].options == ["MATH 3315"]

    # both completed -> eligible
    result = check_eligibility(rows, completed_course_ids={course_a.id, course_b.id})
    assert result.eligible is True


def test_or_group_satisfied_by_either_option():
    course_b = _course("CS 3345")
    course_d = _course("CS 4375")
    course_c = _course("CS 4365")
    rows = [_prereq(course_c, 1, course_b), _prereq(course_c, 1, course_d)]

    # neither completed
    result = check_eligibility(rows, completed_course_ids=set())
    assert result.eligible is False
    assert set(result.missing[0].options) == {"CS 3345", "CS 4375"}

    # only one of the OR options completed -> satisfied
    result = check_eligibility(rows, completed_course_ids={course_d.id})
    assert result.eligible is True


def test_and_of_or_groups_example_from_brief():
    """Course C requires A AND (B OR D)."""
    course_a = _course("A")
    course_b = _course("B")
    course_d = _course("D")
    course_c = _course("C")
    rows = [
        _prereq(course_c, 1, course_a),
        _prereq(course_c, 2, course_b),
        _prereq(course_c, 2, course_d),
    ]

    # A and B completed -> eligible
    assert check_eligibility(rows, {course_a.id, course_b.id}).eligible is True
    # A and D completed -> eligible
    assert check_eligibility(rows, {course_a.id, course_d.id}).eligible is True
    # only A completed -> not eligible (missing B or D)
    result = check_eligibility(rows, {course_a.id})
    assert result.eligible is False
    assert set(result.missing[0].options) == {"B", "D"}
    # only B completed -> not eligible (missing A)
    result = check_eligibility(rows, {course_b.id})
    assert result.eligible is False
    assert result.missing[0].options == ["A"]
