"""Seed synthetic degree programs, requirement groups, and prerequisites.

IMPORTANT: Every degree program below is fictional, generated for
demonstration purposes only, and tied to the synthetic "Northlake
University" dataset created by seed_data.py. It must never be presented as
a real institutional degree plan (see docs/architecture-proposal.md, "Data
Provenance Disclaimer").

Run after seed_data.py:
    python scripts/seed_data.py
    python scripts/seed_degrees.py
"""

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.session import SessionLocal  # noqa: E402
from app.models import Course, Department, DegreeProgram, University  # noqa: E402
from app.models.degree import (  # noqa: E402
    CoursePrerequisite,
    DegreeRequirementCourse,
    DegreeRequirementGroup,
)

CATALOG_YEAR = 2026

# (name, department_code, [(group_name, required_count, [course_codes]), ...])
DEGREE_PROGRAMS = [
    (
        "B.S. Computer Science",
        "CS",
        [
            ("Core", 4, ["CS 1336", "CS 2336", "CS 3345", "CS 3377", "CS 4347"]),
            ("Electives", 2, ["CS 4375", "CS 4395", "CS 4365", "CS 4348", "CS 4349"]),
            ("Capstone", 1, ["CS 4349"]),
        ],
    ),
    (
        "B.S. Data Science",
        "STAT",
        [
            ("Core", 4, ["CS 1336", "MATH 2413", "MATH 3315", "STAT 4351", "CS 4375"]),
            ("Electives", 2, ["CS 4395", "STAT 4382", "BUSN 3305"]),
            ("Capstone", 1, ["CS 4375"]),
        ],
    ),
    (
        "B.S. Business Analytics",
        "BUSN",
        [
            ("Core", 3, ["BUSN 3305", "BUSN 3320", "BUSN 4310", "STAT 4351"]),
            ("Electives", 1, ["BUSN 4325", "CS 1336"]),
            ("Capstone", 1, ["BUSN 4325"]),
        ],
    ),
]

# (course_code, [[or-group-1-codes], [or-group-2-codes], ...])
# Every inner list is an OR group; all outer groups are AND'd together.
PREREQUISITES = [
    ("CS 2336", [["CS 1336"]]),
    ("CS 3345", [["CS 2336"]]),
    ("CS 4347", [["CS 2336"]]),
    ("CS 4375", [["CS 2336"], ["MATH 3315"]]),
    ("CS 4395", [["CS 4375"]]),
    ("CS 4365", [["CS 3345", "CS 4375"]]),
    ("CS 4349", [["CS 3345"]]),
    ("MATH 2419", [["MATH 2413"]]),
    ("MATH 3321", [["MATH 2413"]]),
    ("STAT 4351", [["MATH 3315"]]),
    ("STAT 4382", [["STAT 4351"]]),
    ("BUSN 4325", [["CS 1336", "BUSN 3305"]]),
]


def seed() -> None:
    db = SessionLocal()
    try:
        university = db.query(University).filter_by(short_name="NLU").first()
        if university is None:
            print("Northlake University (NLU) not found. Run scripts/seed_data.py first.")
            return

        if db.query(DegreeProgram).filter_by(university_id=university.id).first():
            print("Sample degree programs already present for NLU. Skipping seed.")
            return

        courses_by_code = {
            c.code: c for c in db.query(Course).filter_by(university_id=university.id).all()
        }

        programs_created = 0
        for name, dept_code, groups in DEGREE_PROGRAMS:
            department = db.query(Department).filter_by(
                university_id=university.id, code=dept_code
            ).first()
            program = DegreeProgram(
                id=uuid.uuid4(),
                university_id=university.id,
                department_id=department.id if department else None,
                name=name,
                catalog_year=CATALOG_YEAR,
            )
            db.add(program)
            db.flush()
            programs_created += 1

            for group_name, required_count, course_codes in groups:
                group = DegreeRequirementGroup(
                    id=uuid.uuid4(),
                    degree_program_id=program.id,
                    name=group_name,
                    required_count=required_count,
                )
                db.add(group)
                db.flush()

                for code in course_codes:
                    course = courses_by_code.get(code)
                    if course is None:
                        print(f"Skipping unknown course code '{code}' in {name}/{group_name}.")
                        continue
                    db.add(
                        DegreeRequirementCourse(
                            id=uuid.uuid4(), requirement_group_id=group.id, course_id=course.id
                        )
                    )

        prereqs_created = 0
        for course_code, or_groups in PREREQUISITES:
            course = courses_by_code.get(course_code)
            if course is None:
                print(f"Skipping prerequisites for unknown course '{course_code}'.")
                continue
            for group_number, or_group in enumerate(or_groups, start=1):
                for prereq_code in or_group:
                    prereq_course = courses_by_code.get(prereq_code)
                    if prereq_course is None:
                        print(f"Skipping unknown prerequisite course '{prereq_code}'.")
                        continue
                    db.add(
                        CoursePrerequisite(
                            id=uuid.uuid4(),
                            course_id=course.id,
                            group_number=group_number,
                            prerequisite_course_id=prereq_course.id,
                        )
                    )
                    prereqs_created += 1

        db.commit()
        print(
            f"Seeded {programs_created} degree programs and {prereqs_created} prerequisite "
            f"relationships for '{university.name}' ({university.short_name})."
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
