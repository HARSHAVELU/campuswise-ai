"""Seed the database with a synthetic sample dataset for local development and demos.

IMPORTANT: This data is entirely fictional. "Northlake University" is not a real
institution, and every course, professor, rating, and grade record below is
generated for demonstration purposes only. It must never be presented to end
users as real institutional data (see docs/architecture-proposal.md, "Data
Provenance Disclaimer").

Usage:
    python scripts/seed_data.py
"""

import datetime
import random
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.session import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    Building,
    Course,
    CourseTopic,
    Department,
    GradeHistory,
    Professor,
    ProfessorRating,
    Room,
    Season,
    Section,
    SectionMeeting,
    Term,
    University,
)
from app.models.course import CourseLevel  # noqa: E402
from app.models.section import DayOfWeek, DeliveryMode  # noqa: E402

random.seed(42)

DEPARTMENTS = [
    ("CS", "Computer Science"),
    ("MATH", "Mathematics"),
    ("STAT", "Statistics"),
    ("BUSN", "Business Administration"),
]

# (dept_code, course_code, title, credit_hours, level, topics)
COURSES = [
    ("CS", "CS 1336", "Programming Fundamentals", 3, "undergraduate", ["python", "programming basics"]),
    ("CS", "CS 2336", "Data Structures", 3, "undergraduate", ["data structures", "java"]),
    ("CS", "CS 3345", "Algorithm Analysis", 3, "undergraduate", ["algorithms"]),
    ("CS", "CS 4347", "Database Systems", 3, "undergraduate", ["sql", "databases"]),
    ("CS", "CS 4375", "Introduction to Machine Learning", 3, "undergraduate", ["machine learning", "python", "ai"]),
    ("CS", "CS 4395", "Natural Language Processing", 3, "graduate", ["nlp", "python", "ai"]),
    ("CS", "CS 4365", "Artificial Intelligence", 3, "undergraduate", ["ai", "search algorithms"]),
    ("CS", "CS 3377", "Software Engineering", 3, "undergraduate", ["software engineering", "agile"]),
    ("CS", "CS 4348", "Operating Systems Concepts", 3, "undergraduate", ["operating systems", "systems programming"]),
    ("CS", "CS 4349", "Advanced Algorithm Design", 3, "graduate", ["algorithms", "optimization"]),
    ("MATH", "MATH 2413", "Calculus I", 4, "undergraduate", ["calculus"]),
    ("MATH", "MATH 2419", "Calculus II", 4, "undergraduate", ["calculus"]),
    ("MATH", "MATH 3315", "Probability and Statistics", 3, "undergraduate", ["statistics", "probability"]),
    ("MATH", "MATH 3321", "Linear Algebra", 3, "undergraduate", ["linear algebra"]),
    ("STAT", "STAT 4351", "Applied Statistics with Python", 3, "undergraduate", ["statistics", "python"]),
    ("STAT", "STAT 4382", "Data Visualization", 3, "undergraduate", ["data visualization", "python"]),
    ("BUSN", "BUSN 3305", "Business Analytics", 3, "undergraduate", ["analytics", "excel"]),
    ("BUSN", "BUSN 3320", "Financial Management", 3, "undergraduate", ["finance"]),
    ("BUSN", "BUSN 4310", "Marketing Strategy", 3, "undergraduate", ["marketing"]),
    ("BUSN", "BUSN 4325", "Business Python Applications", 3, "undergraduate", ["python", "business analytics"]),
]

# (dept_code, name, title)
PROFESSORS = [
    ("CS", "Dr. Elena Marquez", "Associate Professor"),
    ("CS", "Dr. Samuel Okafor", "Professor"),
    ("CS", "Dr. Priya Natarajan", "Assistant Professor"),
    ("CS", "Dr. Wei Chen", "Senior Lecturer"),
    ("CS", "Dr. Daniel Osei", "Associate Professor"),
    ("CS", "Dr. Grace Lindqvist", "Lecturer"),
    ("CS", "Dr. Marcus Fielding", "Professor"),
    ("MATH", "Dr. Ana Rocha", "Professor"),
    ("MATH", "Dr. Thomas Whitfield", "Associate Professor"),
    ("MATH", "Dr. Yuki Tanaka", "Lecturer"),
    ("STAT", "Dr. Olivia Bergstrom", "Assistant Professor"),
    ("STAT", "Dr. Rahul Deshmukh", "Senior Lecturer"),
    ("BUSN", "Dr. Claire Whitmore", "Professor"),
    ("BUSN", "Dr. Victor Adeyemi", "Associate Professor"),
    ("BUSN", "Dr. Sofia Petrov", "Lecturer"),
]

BUILDINGS = [
    ("INNO", "Innovation Hall"),
    ("SCI", "Science Building"),
    ("BUS", "Business Building"),
]

TERMS = [
    ("Fall 2025", 2025, Season.FALL, False),
    ("Spring 2026", 2026, Season.SPRING, False),
    ("Fall 2026", 2026, Season.FALL, True),
]

GRADE_BUCKET_NAMES = [
    "a_plus", "a", "a_minus",
    "b_plus", "b", "b_minus",
    "c_plus", "c", "c_minus",
    "d_plus", "d", "d_minus",
    "f",
]


def random_grade_distribution(class_size: int, difficulty: float) -> dict[str, int]:
    """Generate a plausible grade distribution.

    `difficulty` in [0, 1]: higher shifts weight toward lower grades.
    Purely synthetic — not derived from any real course.
    """
    weights = [
        max(0.02, 0.22 - difficulty * 0.15),  # a_plus
        max(0.03, 0.20 - difficulty * 0.10),  # a
        max(0.05, 0.15 - difficulty * 0.05),  # a_minus
        0.10,  # b_plus
        0.10,  # b
        0.08,  # b_minus
        0.06 + difficulty * 0.05,  # c_plus
        0.05 + difficulty * 0.05,  # c
        0.04 + difficulty * 0.05,  # c_minus
        0.02 + difficulty * 0.05,  # d_plus
        0.02 + difficulty * 0.05,  # d
        0.01 + difficulty * 0.03,  # d_minus
        0.01 + difficulty * 0.07,  # f
    ]
    total_weight = sum(weights)
    normalized = [w / total_weight for w in weights]
    counts = [round(w * class_size) for w in normalized]
    return dict(zip(GRADE_BUCKET_NAMES, counts))


def seed() -> None:
    db = SessionLocal()
    try:
        existing = db.query(University).filter_by(short_name="NLU").first()
        if existing:
            print("Sample data already present (University short_name=NLU). Skipping seed.")
            return

        university = University(
            id=uuid.uuid4(),
            name="Northlake University",
            short_name="NLU",
            city="Austin",
            state="TX",
        )
        db.add(university)
        db.flush()

        departments: dict[str, Department] = {}
        for code, name in DEPARTMENTS:
            dept = Department(id=uuid.uuid4(), university_id=university.id, code=code, name=name)
            db.add(dept)
            departments[code] = dept
        db.flush()

        professors: list[Professor] = []
        for dept_code, name, title in PROFESSORS:
            professor = Professor(
                id=uuid.uuid4(),
                university_id=university.id,
                department_id=departments[dept_code].id,
                name=name,
                title=title,
                email=name.split(" ", 1)[1].replace(" ", ".").lower() + "@northlake.example.edu",
            )
            db.add(professor)
            professors.append(professor)
        db.flush()

        for professor in professors:
            overall = round(random.uniform(3.2, 4.9), 1)
            difficulty = round(random.uniform(1.8, 4.2), 1)
            rating = ProfessorRating(
                id=uuid.uuid4(),
                professor_id=professor.id,
                overall_rating=overall,
                teaching_rating=round(min(5.0, overall + random.uniform(-0.3, 0.3)), 1),
                difficulty_rating=difficulty,
                would_take_again_pct=round(random.uniform(55, 96), 1),
                num_ratings=random.randint(12, 180),
                source_type="student_reported",
                confidence=0.8,
            )
            db.add(rating)

        courses: list[Course] = []
        for dept_code, code, title, credits, level, topics in COURSES:
            course = Course(
                id=uuid.uuid4(),
                university_id=university.id,
                department_id=departments[dept_code].id,
                code=code,
                title=title,
                description=(
                    f"{title} covers foundational and applied concepts relevant to "
                    f"{', '.join(topics)}. (Synthetic sample course description.)"
                ),
                credit_hours=credits,
                level=CourseLevel(level),
            )
            db.add(course)
            db.flush()
            for topic in topics:
                db.add(CourseTopic(id=uuid.uuid4(), course_id=course.id, topic=topic))
            courses.append(course)
        db.flush()

        buildings: list[Building] = []
        rooms: list[Room] = []
        for code, name in BUILDINGS:
            building = Building(id=uuid.uuid4(), university_id=university.id, code=code, name=name)
            db.add(building)
            db.flush()
            buildings.append(building)
            for room_number in ["101", "204", "310"]:
                room = Room(
                    id=uuid.uuid4(), building_id=building.id, room_number=room_number, capacity=40
                )
                db.add(room)
                rooms.append(room)
        db.flush()

        terms: list[Term] = []
        for name, year, season, active in TERMS:
            term = Term(
                id=uuid.uuid4(),
                university_id=university.id,
                name=name,
                year=year,
                season=season,
                is_active_for_planning=active,
            )
            db.add(term)
            terms.append(term)
        db.flush()

        professors_by_dept: dict[str, list[Professor]] = {}
        for professor, (dept_code, _, _) in zip(professors, PROFESSORS):
            professors_by_dept.setdefault(dept_code, []).append(professor)

        delivery_modes = [DeliveryMode.IN_PERSON, DeliveryMode.ONLINE, DeliveryMode.HYBRID]
        day_pairs = [
            (DayOfWeek.MONDAY, DayOfWeek.WEDNESDAY),
            (DayOfWeek.TUESDAY, DayOfWeek.THURSDAY),
            (DayOfWeek.MONDAY, DayOfWeek.FRIDAY),
        ]
        start_hours = [9, 10, 11, 13, 14, 16]

        sections_created = 0
        target_sections = 40
        course_cycle = list(courses)
        random.shuffle(course_cycle)

        for i in range(target_sections):
            course = course_cycle[i % len(course_cycle)]
            dept_code = next(d for d, c, *_ in COURSES if c == course.code)
            candidate_profs = professors_by_dept.get(dept_code, professors)
            professor = random.choice(candidate_profs)
            term = terms[i % len(terms)]
            delivery = random.choice(delivery_modes)
            building = random.choice(buildings)
            room = random.choice([r for r in rooms if r.building_id == building.id])

            section = Section(
                id=uuid.uuid4(),
                course_id=course.id,
                term_id=term.id,
                professor_id=professor.id,
                section_number=f"{(i % 5) + 1:03d}",
                delivery_mode=delivery,
                seats_total=random.choice([25, 30, 40, 60]),
            )
            section.seats_available = random.randint(0, section.seats_total)
            db.add(section)
            db.flush()
            sections_created += 1

            if delivery != DeliveryMode.ONLINE:
                start_hour = random.choice(start_hours)
                meeting_days = random.choice(day_pairs)
                for day in meeting_days:
                    db.add(
                        SectionMeeting(
                            id=uuid.uuid4(),
                            section_id=section.id,
                            room_id=room.id,
                            day_of_week=day,
                            start_time=datetime.time(hour=start_hour, minute=0),
                            end_time=datetime.time(hour=start_hour + 1, minute=15),
                        )
                    )

            # Historical grade record for this course/professor/term combination.
            difficulty = random.uniform(0.1, 0.9)
            class_size = random.randint(20, 55)
            bucket_counts = random_grade_distribution(class_size, difficulty)
            db.add(
                GradeHistory(
                    id=uuid.uuid4(),
                    course_id=course.id,
                    professor_id=professor.id,
                    term_id=term.id,
                    section_number=section.section_number,
                    withdrawals=random.randint(0, 3),
                    source_type="historical",
                    **bucket_counts,
                )
            )

        db.commit()
        print(
            f"Seeded {len(courses)} courses, {len(professors)} professors, "
            f"{sections_created} sections, and grade history across {len(terms)} terms "
            f"for synthetic university '{university.name}' ({university.short_name})."
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
