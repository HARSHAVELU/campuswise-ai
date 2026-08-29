"""Seed synthetic syllabus documents for the RAG pipeline -- one per course.

IMPORTANT: Every syllabus below is fictional, generated for demonstration
purposes only, and tied to the synthetic "Northlake University" dataset
created by seed_data.py. It must never be presented as a real institutional
document (see docs/architecture-proposal.md, "Data Provenance Disclaimer").

Syllabus text is template-generated (seeded per course code, so reseeding is
deterministic) rather than hand-written per course, so every course in the
catalog gets real, queryable exam/grading/policy content -- while keeping
the exact phrasing patterns (e.g. "Exam Format:", "is worth X%", "proctored
via X") that app.ingestion.assessment_extraction_rules' regex extractor
relies on, so structured extraction works identically for every course.

Run after seed_data.py:
    python scripts/seed_data.py
    python scripts/seed_syllabi.py
"""

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.session import SessionLocal  # noqa: E402
from app.ingestion.syllabus_ingestion import ingest_syllabus  # noqa: E402
from app.models import Course, Professor, Section, Syllabus, Term, University  # noqa: E402

PROCTORING_TOOLS = ["Honorlock", "LockDown Browser", "ProctorU"]


def _exam_sentence(role: str, rng: random.Random) -> str:
    """role: 'midterm' or 'final'."""
    style = rng.choice(["online_open", "online_proctored_closed", "in_person_closed", "in_person_open"])
    if style == "online_open":
        return f"The {role} exam is administered online through the course portal and is open-book."
    if style == "online_proctored_closed":
        proctor = rng.choice(PROCTORING_TOOLS)
        return f"The {role} exam is administered online, proctored via {proctor}, and closed-book."
    if style == "in_person_closed":
        return f"The {role} exam is administered in person and is closed-book."
    return f"The {role} exam is administered in person and is open-book, open-note."


def generate_syllabus_text(course_code: str, course_title: str, professor_name: str, seed: int) -> str:
    rng = random.Random(seed)

    exam_pattern = rng.choice(
        ["both_exams", "midterm_only", "final_only", "no_exams", "no_exams"]
    )
    has_midterm = exam_pattern in ("both_exams", "midterm_only")
    has_final = exam_pattern in ("both_exams", "final_only")
    has_project = rng.random() < 0.7
    is_group_project = has_project and rng.random() < 0.5
    has_quizzes = rng.random() < 0.4
    has_presentation = rng.random() < 0.3 or not (has_midterm or has_final)
    participation_graded = rng.random() < 0.5

    # Build the full list of graded components ONCE, so every percentage
    # (including participation) is drawn from the same 100%-summing pool --
    # no component is ever described twice with conflicting weights.
    components: list[str] = ["homework assignments"]
    if has_quizzes:
        components.append("weekly quizzes")
    if participation_graded:
        components.append("class participation")
    if has_project:
        components.append("a group project" if is_group_project else "an individual project")
    if has_midterm:
        components.append("a midterm exam")
    if has_final:
        components.append("a final exam")
    if not has_midterm and not has_final and not has_project:
        components.append("a final presentation")

    n = len(components)
    base = 100 // n
    pcts = [base] * n
    for i in range(100 - base * n):
        pcts[i % n] += 1
    rng.shuffle(pcts)
    weights = dict(zip(components, pcts))

    grading_sentences = []
    for label, pct in weights.items():
        if label.startswith(("a group", "an individual")):
            verb = "counts for"
        elif label.endswith(("assignments", "quizzes")):
            verb = "are worth"
        else:
            verb = "is worth"
        grading_sentences.append(f"{label[0].upper() + label[1:]} {verb} {pct}%.")
    grading_paragraph = "Grading Breakdown: " + " ".join(grading_sentences)

    if rng.random() < 0.4:
        attendance_line = (
            "Attendance is required and tracked. More than 4 unexcused absences will lower your "
            "final letter grade by one step."
        )
    elif participation_graded:
        attendance_line = (
            f"Attendance is not mandatory but strongly encouraged. Class participation counts for "
            f"{weights['class participation']}% of the final grade, as noted above."
        )
    else:
        attendance_line = "Attendance is recorded but not directly graded."

    if not has_midterm and not has_final:
        exam_paragraph = (
            "Exam Format: This course has no midterm or final exam. Mastery is assessed entirely "
            "through assignments" + (" and the project" if has_project else "") + "."
        )
    else:
        exam_lines = []
        if has_midterm:
            exam_lines.append(_exam_sentence("midterm", rng))
        else:
            exam_lines.append("There is no midterm exam in this course.")
        if has_final:
            exam_lines.append(_exam_sentence("final", rng))
        else:
            exam_lines.append(
                "There is no separate final exam; the project serves as the final assessment."
            )
        exam_paragraph = "Exam Format: " + " ".join(exam_lines)

    project_line = ""
    if has_project:
        if is_group_project:
            project_line = rng.choice(
                [
                    "Students work in teams of three to four on a semester-long group project.",
                    "A group project, worked on in teams, is due in the final weeks of the course.",
                ]
            )
        else:
            project_line = "An individual project applies course concepts to a self-selected problem."
        if has_presentation:
            project_line += " A final presentation is required."

    late_penalty = rng.choice([5, 10, 15])
    late_window = rng.choice([24, 48, 72])
    late_policy = (
        f"Late Policy: Assignments are accepted up to {late_window} hours after the deadline with "
        f"a {late_penalty}% per day penalty. No submissions are accepted after that window without "
        f"prior approval."
    )

    parts = [
        f"Course Policies for {course_code} - {course_title}",
        attendance_line,
        grading_paragraph,
        exam_paragraph,
    ]
    if project_line:
        parts.append(project_line)
    parts.append(late_policy)

    return "\n\n".join(parts)


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
        courses = db.query(Course).filter_by(university_id=university.id).all()

        ingested = 0
        for course in courses:
            # Prefer the professor teaching this course in Fall 2025 if a section
            # exists there; otherwise fall back to any section's professor.
            section = (
                db.query(Section)
                .filter_by(course_id=course.id, term_id=term.id if term else None)
                .first()
                or db.query(Section).filter_by(course_id=course.id).first()
            )
            professor: Professor | None = section.professor if section else None
            if professor is None:
                print(f"Skipping {course.code}: no professor assigned to any section.")
                continue

            source_document = f"{course.code.replace(' ', '')}_Fall2025.pdf"
            syllabus_text = generate_syllabus_text(
                course.code, course.title, professor.name, seed=hash(course.code) & 0xFFFFFFFF
            )

            ingest_syllabus(
                db,
                university_id=university.id,
                course_id=course.id,
                professor_id=professor.id,
                term_id=term.id if term else None,
                title=f"{course.code} {term.name if term else ''} Syllabus".strip(),
                source_document=source_document,
                raw_text=syllabus_text,
            )
            ingested += 1

        db.commit()
        print(
            f"Ingested {ingested} synthetic syllabus documents for "
            f"'{university.name}' ({university.short_name})."
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
