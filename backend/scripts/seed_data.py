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
    ("ECON", "Economics"),
    ("PHYS", "Physics"),
]

# (dept_code, course_code, title, credit_hours, level, topics, description)
COURSES = [
    ("CS", "CS 1336", "Programming Fundamentals", 3, "undergraduate", ["python", "programming basics"],
     "An introduction to computer programming using Python, covering variables, control flow, "
     "functions, basic data structures, and problem-solving techniques for students with no prior "
     "programming experience."),
    ("CS", "CS 2336", "Data Structures", 3, "undergraduate", ["data structures", "java"],
     "Study of core data structures — arrays, linked lists, stacks, queues, trees, and hash tables — "
     "and their implementation and analysis using Java, with an emphasis on choosing the right "
     "structure for a given problem."),
    ("CS", "CS 3345", "Algorithm Analysis", 3, "undergraduate", ["algorithms"],
     "Formal techniques for analyzing algorithm efficiency, including asymptotic notation, "
     "divide-and-conquer, dynamic programming, and greedy algorithms, with proofs of correctness "
     "and complexity."),
    ("CS", "CS 4347", "Database Systems", 3, "undergraduate", ["sql", "databases"],
     "Relational database design, normalization, SQL query writing and optimization, transaction "
     "management, and an introduction to NoSQL data stores, with hands-on database design projects."),
    ("CS", "CS 4375", "Introduction to Machine Learning", 3, "undergraduate",
     ["machine learning", "python", "ai"],
     "Foundational machine learning techniques including linear and logistic regression, decision "
     "trees, clustering, and neural network basics, implemented in Python using scikit-learn."),
    ("CS", "CS 4395", "Natural Language Processing", 3, "graduate", ["nlp", "python", "ai"],
     "Computational techniques for processing and understanding human language, covering "
     "tokenization, part-of-speech tagging, sentiment analysis, and transformer-based language "
     "models."),
    ("CS", "CS 4365", "Artificial Intelligence", 3, "undergraduate", ["ai", "search algorithms"],
     "Classical AI techniques including search algorithms, constraint satisfaction, game playing, "
     "and an introduction to knowledge representation and planning."),
    ("CS", "CS 3377", "Software Engineering", 3, "undergraduate", ["software engineering", "agile"],
     "Team-based software development practices including requirements gathering, agile "
     "methodologies, version control, testing, and code review, culminating in a semester-long "
     "group project."),
    ("CS", "CS 4348", "Operating Systems Concepts", 3, "undergraduate",
     ["operating systems", "systems programming"],
     "Core operating system principles — processes, threads, scheduling, memory management, and "
     "file systems — with programming assignments in C."),
    ("CS", "CS 4349", "Advanced Algorithm Design", 3, "graduate", ["algorithms", "optimization"],
     "Advanced algorithmic techniques including network flow, approximation algorithms, randomized "
     "algorithms, and NP-completeness, intended as a capstone-level algorithms course."),
    ("CS", "CS 2340", "Computer Architecture", 3, "undergraduate",
     ["computer architecture", "digital logic"],
     "Digital logic design, instruction set architecture, pipelining, memory hierarchy, and the "
     "hardware/software interface, with lab exercises building simple processors."),
    ("CS", "CS 3320", "Web Application Development", 3, "undergraduate",
     ["web development", "javascript", "python"],
     "Full-stack web development covering HTML/CSS/JavaScript, a modern frontend framework, REST "
     "API design, and deployment, with a semester project building a complete web application."),
    ("CS", "CS 4341", "Computer Networks", 3, "undergraduate", ["networking", "systems programming"],
     "Networking fundamentals including the TCP/IP stack, routing, network security basics, and "
     "socket programming, with labs analyzing real network traffic."),
    ("CS", "CS 4390", "Mobile App Development", 3, "undergraduate", ["mobile development", "java"],
     "Native mobile application development for iOS and Android, covering UI design, local "
     "storage, device APIs, and app store deployment."),
    ("CS", "CS 4398", "Cybersecurity Fundamentals", 3, "undergraduate",
     ["cybersecurity", "networking"],
     "Introduction to information security including cryptography basics, common vulnerabilities, "
     "secure coding practices, and network defense, with hands-on labs in a sandboxed environment."),
    ("CS", "CS 4399", "Cloud Computing and Distributed Systems", 3, "graduate",
     ["cloud computing", "distributed systems"],
     "Principles of distributed systems and cloud infrastructure, covering containerization, "
     "orchestration, distributed consensus, and scalable system design on a major cloud platform."),
    ("MATH", "MATH 2413", "Calculus I", 4, "undergraduate", ["calculus"],
     "Limits, derivatives, and their applications, including optimization and related rates, with "
     "an introduction to definite integrals."),
    ("MATH", "MATH 2419", "Calculus II", 4, "undergraduate", ["calculus"],
     "Techniques of integration, infinite series, parametric equations, and polar coordinates, "
     "building directly on Calculus I."),
    ("MATH", "MATH 2417", "Calculus III", 4, "undergraduate", ["calculus", "multivariable calculus"],
     "Multivariable calculus including partial derivatives, multiple integrals, and vector "
     "calculus, with applications to physics and engineering."),
    ("MATH", "MATH 3315", "Probability and Statistics", 3, "undergraduate", ["statistics", "probability"],
     "Foundational probability theory and statistical inference, including random variables, "
     "distributions, hypothesis testing, and confidence intervals."),
    ("MATH", "MATH 3321", "Linear Algebra", 3, "undergraduate", ["linear algebra"],
     "Vector spaces, matrices, eigenvalues and eigenvectors, and linear transformations, with "
     "applications to computer graphics and data science."),
    ("MATH", "MATH 3350", "Discrete Mathematics", 3, "undergraduate", ["discrete math", "algorithms"],
     "Logic, set theory, combinatorics, graph theory, and proof techniques foundational to "
     "computer science and algorithm analysis."),
    ("STAT", "STAT 4351", "Applied Statistics with Python", 3, "undergraduate", ["statistics", "python"],
     "Practical statistical analysis using Python (pandas, NumPy, SciPy), covering exploratory "
     "data analysis, hypothesis testing, and regression modeling on real datasets."),
    ("STAT", "STAT 4382", "Data Visualization", 3, "undergraduate", ["data visualization", "python"],
     "Principles of effective data visualization and hands-on practice building charts, "
     "dashboards, and interactive visualizations using Python visualization libraries."),
    ("STAT", "STAT 4355", "Statistical Machine Learning", 3, "graduate",
     ["machine learning", "statistics"],
     "Statistical foundations of machine learning methods including regularization, "
     "cross-validation, ensemble methods, and model evaluation, bridging statistics and applied ML."),
    ("STAT", "STAT 4390", "Time Series Analysis", 3, "undergraduate", ["statistics", "forecasting"],
     "Analysis and forecasting of time-dependent data, covering trend and seasonality "
     "decomposition, ARIMA models, and an introduction to forecasting with modern tools."),
    ("BUSN", "BUSN 3305", "Business Analytics", 3, "undergraduate", ["analytics", "excel"],
     "Data-driven decision-making for business, covering descriptive and predictive analytics "
     "techniques using spreadsheet and BI tools, with case-study-based assignments."),
    ("BUSN", "BUSN 3320", "Financial Management", 3, "undergraduate", ["finance"],
     "Core principles of corporate finance including time value of money, capital budgeting, risk "
     "and return, and financial statement analysis."),
    ("BUSN", "BUSN 4310", "Marketing Strategy", 3, "undergraduate", ["marketing"],
     "Strategic marketing frameworks including market segmentation, positioning, the marketing "
     "mix, and digital marketing, applied through case studies and a marketing plan project."),
    ("BUSN", "BUSN 4325", "Business Python Applications", 3, "undergraduate",
     ["python", "business analytics"],
     "Applying Python programming to business problems including data cleaning, automation, and "
     "building simple analytics tools, for students with introductory programming background."),
    ("BUSN", "BUSN 3350", "Organizational Behavior", 3, "undergraduate", ["management"],
     "How individuals, teams, and organizational structures affect workplace behavior and "
     "performance, covering motivation, leadership, and organizational culture."),
    ("BUSN", "BUSN 4340", "Entrepreneurship and Innovation", 3, "undergraduate",
     ["entrepreneurship", "innovation"],
     "The startup lifecycle from ideation to launch, covering business model design, lean startup "
     "methodology, and pitching to investors, with a capstone venture pitch."),
    ("ECON", "ECON 2301", "Principles of Microeconomics", 3, "undergraduate", ["economics"],
     "Introduction to microeconomic theory including supply and demand, market structures, "
     "consumer and producer behavior, and market failures."),
    ("ECON", "ECON 4315", "Econometrics", 3, "graduate", ["economics", "statistics"],
     "Statistical methods for economic analysis, including regression modeling, causal inference, "
     "and hypothesis testing applied to real economic data."),
    ("PHYS", "PHYS 2325", "University Physics I", 4, "undergraduate", ["physics", "mechanics"],
     "Calculus-based introduction to mechanics, covering kinematics, Newton's laws, energy, "
     "momentum, and rotational motion, with a required lab component."),
    ("PHYS", "PHYS 3340", "Computational Physics", 3, "undergraduate", ["physics", "python"],
     "Numerical methods for solving physics problems using Python, including simulation of "
     "physical systems, numerical integration, and data analysis of experimental results."),
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
    ("CS", "Dr. Isabella Torres", "Assistant Professor"),
    ("CS", "Dr. Kevin Park", "Associate Professor"),
    ("CS", "Dr. Amara Nwosu", "Senior Lecturer"),
    ("CS", "Dr. Benjamin Cole", "Lecturer"),
    ("MATH", "Dr. Ana Rocha", "Professor"),
    ("MATH", "Dr. Thomas Whitfield", "Associate Professor"),
    ("MATH", "Dr. Yuki Tanaka", "Lecturer"),
    ("MATH", "Dr. Farah Al-Sayed", "Assistant Professor"),
    ("MATH", "Dr. Lucas Bennett", "Senior Lecturer"),
    ("STAT", "Dr. Olivia Bergstrom", "Assistant Professor"),
    ("STAT", "Dr. Rahul Deshmukh", "Senior Lecturer"),
    ("STAT", "Dr. Meera Iyer", "Associate Professor"),
    ("STAT", "Dr. Connor Doyle", "Lecturer"),
    ("BUSN", "Dr. Claire Whitmore", "Professor"),
    ("BUSN", "Dr. Victor Adeyemi", "Associate Professor"),
    ("BUSN", "Dr. Sofia Petrov", "Lecturer"),
    ("BUSN", "Dr. Natalie Brooks", "Assistant Professor"),
    ("BUSN", "Dr. Omar Haddad", "Senior Lecturer"),
    ("ECON", "Dr. Julia Kaminski", "Associate Professor"),
    ("ECON", "Dr. Andres Reyes", "Assistant Professor"),
    ("PHYS", "Dr. Hannah Kessler", "Professor"),
    ("PHYS", "Dr. Ravi Chandran", "Associate Professor"),
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
                email=name.split(" ", 1)[1].replace(" ", ".").replace("-", "").lower()
                + "@northlake.example.edu",
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
        for dept_code, code, title, credits, level, topics, description in COURSES:
            course = Course(
                id=uuid.uuid4(),
                university_id=university.id,
                department_id=departments[dept_code].id,
                code=code,
                title=title,
                description=description,
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
            for room_number in ["101", "204", "310", "412"]:
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

        # Every course gets 2-3 sections spread across terms/professors/delivery
        # modes so the catalog has real depth to search, filter, and schedule against.
        sections_created = 0
        section_plan: list[Course] = []
        for course in courses:
            for _ in range(random.choice([2, 3])):
                section_plan.append(course)
        random.shuffle(section_plan)

        for i, course in enumerate(section_plan):
            dept_code = next(d for d, c, *_ in COURSES if c == course.code)
            candidate_profs = professors_by_dept.get(dept_code, professors)
            professor = random.choice(candidate_profs)
            term = terms[i % len(terms)]
            delivery = random.choice(delivery_modes)
            building = random.choice(buildings)
            room = random.choice([r for r in rooms if r.building_id == building.id])

            existing_numbers = {
                s.section_number
                for s in db.query(Section)
                .filter_by(course_id=course.id, term_id=term.id)
                .all()
            }
            section_number = next(
                n for n in (f"{k:03d}" for k in range(1, 10)) if n not in existing_numbers
            )

            section = Section(
                id=uuid.uuid4(),
                course_id=course.id,
                term_id=term.id,
                professor_id=professor.id,
                section_number=section_number,
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
