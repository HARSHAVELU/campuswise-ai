"""Seed synthetic syllabus documents for the RAG pipeline.

IMPORTANT: Every syllabus below is fictional, generated for demonstration
purposes only, and tied to the synthetic "Northlake University" dataset
created by seed_data.py. It must never be presented as a real institutional
document (see docs/architecture-proposal.md, "Data Provenance Disclaimer").

Run after seed_data.py:
    python scripts/seed_data.py
    python scripts/seed_syllabi.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.session import SessionLocal  # noqa: E402
from app.ingestion.syllabus_ingestion import ingest_syllabus  # noqa: E402
from app.models import Course, Professor, Syllabus, Term, University  # noqa: E402

# (course_code, professor_name, source_document, syllabus_text)
SYLLABI = [
    (
        "CS 1336",
        "Dr. Wei Chen",
        "CS1336_Fall2025.pdf",
        """Course Policies for CS 1336 - Programming Fundamentals

Attendance is required and tracked. More than 4 unexcused absences will lower your final letter grade by one step.

Grading Breakdown: Weekly quizzes are worth 15% of the final grade. Programming assignments are worth 35%. The midterm exam is worth 20% and the final exam is worth 30%.

Exam Format: Both the midterm and final exams are administered in person, closed-book, and closed-laptop. Students may bring one handwritten note card to each exam.

Late Policy: Programming assignments submitted late lose 5% per day, up to a maximum of 3 late days per assignment. No exceptions after 3 days without a documented emergency.""",
    ),
    (
        "CS 4375",
        "Dr. Elena Marquez",
        "CS4375_Fall2025.pdf",
        """Course Policies for CS 4375 - Introduction to Machine Learning

Attendance is not mandatory but strongly encouraged. Class participation counts for 5% of the final grade.

Grading Breakdown: Homework assignments are worth 30% of the final grade. There is a midterm exam worth 20% and a comprehensive final exam worth 35%. A group project counts for the remaining 10%.

Exam Format: The midterm exam is administered online through the course portal and is open-book. The final exam is also online, proctored via Honorlock, and closed-book.

Late Policy: Late assignments are accepted up to 48 hours after the deadline with a 10% per day penalty. No submissions are accepted after 48 hours without prior approval.""",
    ),
    (
        "CS 4395",
        "Dr. Marcus Fielding",
        "CS4395_Fall2025.pdf",
        """Course Policies for CS 4395 - Natural Language Processing

This course has no midterm or final exam. Grading Breakdown: Four programming assignments are worth 15% each (60% total). A semester-long team research project counts for 30%, including a final presentation. Class participation and peer review counts for 10%.

There is no traditional exam in this course -- mastery is assessed entirely through assignments and the project.

Late Policy: Assignments are accepted up to 24 hours late with a 15% penalty. The final project has no late submissions accepted, since presentations are scheduled during the last week of class.""",
    ),
    (
        "CS 4365",
        "Dr. Daniel Osei",
        "CS4365_Fall2025.pdf",
        """Course Policies for CS 4365 - Artificial Intelligence

Attendance is recorded but not directly graded. Grading Breakdown: Problem sets are worth 25%, a midterm exam is worth 25%, a final exam is worth 35%, and a search-algorithm implementation project is worth 15%.

Exam Format: Both the midterm and final exams are administered in person and are closed-book. Laptops and phones must be closed and put away during exams; only a basic calculator is permitted.

Late Policy: Problem sets are not accepted late under any circumstances, since solutions are discussed in class immediately after the deadline.""",
    ),
    (
        "CS 4347",
        "Dr. Samuel Okafor",
        "CS4347_Fall2025.pdf",
        """Course Policies for CS 4347 - Database Systems

Attendance at weekly labs is mandatory; lecture attendance is optional. Grading Breakdown: Weekly lab assignments are worth 30%. A database design project is worth 25%. The midterm exam is worth 20% and the final exam is worth 25%.

Exam Format: Both exams are administered online through the course portal and are open-book, open-note. Students may reference course materials but may not collaborate with other students during the exam window.

Late Policy: Lab assignments lose 10% per day late, up to 3 days. The design project has a hard deadline with no late submissions accepted.""",
    ),
    (
        "CS 3377",
        "Dr. Priya Natarajan",
        "CS3377_Fall2025.pdf",
        """Course Policies for CS 3377 - Software Engineering

This course has no exams. Grading Breakdown: Students work in teams of four on a semester-long software project, delivered in three milestones worth 20% each (60% total). Individual code reviews and peer evaluations are worth 20%. A final team presentation and demo is worth 20%.

There is no midterm or final exam in this course; all assessment is project-based.

Late Policy: Milestone deliverables submitted late lose 5% per day. Teams are expected to manage their own schedule using the sprint planning process taught in the first two weeks.""",
    ),
    (
        "MATH 2413",
        "Dr. Ana Rocha",
        "MATH2413_Fall2025.pdf",
        """Course Policies for MATH 2413 - Calculus I

Attendance is required; more than 6 absences results in a failing grade regardless of exam performance. Grading Breakdown: Weekly homework is worth 10%. There are three unit exams worth 20% each (60% total) and a comprehensive final exam worth 30%.

Exam Format: All exams, including the final, are administered in person and are closed-book. Graphing calculators are not permitted; only a basic scientific calculator may be used.

Late Policy: Homework is not accepted late. If you miss a unit exam with a documented excuse, your final exam score will be substituted for that exam's grade.""",
    ),
    (
        "STAT 4351",
        "Dr. Olivia Bergstrom",
        "STAT4351_Fall2025.pdf",
        """Course Policies for STAT 4351 - Applied Statistics with Python

Attendance is not tracked. Grading Breakdown: Weekly Python-based data analysis assignments are worth 40%. A midterm exam is worth 25% and a final data analysis project (with a written report) is worth 35%. There is no traditional final exam.

Exam Format: The midterm exam is administered online through the course portal and is open-book, open-notebook -- students may use their own Python environment during the exam.

Late Policy: Assignments are accepted up to 72 hours late with a 5% per day penalty. The final project deadline is firm and set by the university's end-of-term deadline.""",
    ),
    (
        "BUSN 3305",
        "Dr. Claire Whitmore",
        "BUSN3305_Fall2025.pdf",
        """Course Policies for BUSN 3305 - Business Analytics

Attendance and in-class participation is worth 10% of the final grade. Grading Breakdown: Two case study write-ups are worth 20% each (40% total). A group project with a client-style presentation is worth 35%. There is no midterm or final exam.

This course is entirely case-study and project based; mastery of analytics tools is assessed through applied deliverables rather than timed exams.

Late Policy: Case study write-ups lose 10% per day late, up to 2 days, after which they are not accepted. Group project deadlines are fixed and coordinated with client presentation scheduling.""",
    ),
    (
        "BUSN 4325",
        "Dr. Victor Adeyemi",
        "BUSN4325_Fall2025.pdf",
        """Course Policies for BUSN 4325 - Business Python Applications

Attendance is optional but recommended given the hands-on lab format. Grading Breakdown: Weekly lab exercises are worth 30%. A midterm exam is worth 20%. A capstone automation project is worth 35%. Class participation is worth 15%.

Exam Format: The midterm exam is administered online through the course portal and is open-book. There is no separate final exam; the capstone project serves as the final assessment.

Late Policy: Lab exercises are accepted up to 48 hours late with a 10% per day penalty. The capstone project has a firm deadline aligned with the final presentation day.""",
    ),
]


def seed() -> None:
    db = SessionLocal()
    try:
        university = db.query(University).filter_by(short_name="NLU").first()
        if university is None:
            print("Northlake University (NLU) not found. Run scripts/seed_data.py first.")
            return

        if db.query(Syllabus).filter_by(university_id=university.id).first():
            print("Sample syllabi already present for NLU. Skipping seed.")
            return

        term = db.query(Term).filter_by(university_id=university.id, name="Fall 2025").first()

        ingested = 0
        for course_code, professor_name, source_document, text in SYLLABI:
            course = db.query(Course).filter_by(university_id=university.id, code=course_code).first()
            professor = (
                db.query(Professor).filter_by(university_id=university.id, name=professor_name).first()
            )
            if course is None or professor is None:
                print(f"Skipping {course_code} / {professor_name}: not found in seeded data.")
                continue

            ingest_syllabus(
                db,
                university_id=university.id,
                course_id=course.id,
                professor_id=professor.id,
                term_id=term.id if term else None,
                title=f"{course_code} {term.name if term else ''} Syllabus".strip(),
                source_document=source_document,
                raw_text=text,
            )
            ingested += 1

        db.commit()
        print(f"Ingested {ingested} synthetic syllabus documents for '{university.name}' ({university.short_name}).")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
