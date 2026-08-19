"""Lightweight RAG evaluation harness.

Runs a fixed set of known-answerable questions (about the seeded syllabi)
and known-unanswerable questions (about courses with no syllabus) through
the real retrieval + Q&A pipeline, and checks:
  - Hit@K: did the expected source document appear in the citations?
  - Abstention accuracy: did an unanswerable question correctly get
    "not available" instead of a fabricated answer?

This is intentionally a small, fast regression check against the seeded
dataset -- not a full continuous-evaluation framework with a managed golden
dataset (see docs/architecture-proposal.md, "RAG Evaluation" for the fuller
target: context precision/recall, faithfulness, citation correctness).

Usage (against a running Postgres with seed_data.py + seed_syllabi.py already run):
    python scripts/evaluate_rag.py
"""

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agents.syllabus_qa import run_syllabus_qa  # noqa: E402
from app.database.session import SessionLocal  # noqa: E402
from app.models import Course  # noqa: E402


@dataclass
class EvalCase:
    course_code: str | None  # None = search with no course filter (should still find nothing relevant)
    question: str
    expect_source_document: str | None  # None = expect "no data" / abstention


CASES = [
    EvalCase("CS 4375", "Is the final exam online?", "CS4375_Fall2025.pdf"),
    EvalCase("CS 4395", "Does this course have a group project?", "CS4395_Fall2025.pdf"),
    EvalCase("CS 1336", "Are the exams closed-book?", "CS1336_Fall2025.pdf"),
    EvalCase("BUSN 3305", "Is there a final exam?", "BUSN3305_Fall2025.pdf"),
    EvalCase("MATH 2419", "What is the grading breakdown?", None),  # no syllabus seeded for this course
]


def run_evaluation() -> None:
    db = SessionLocal()
    hits, total_answerable = 0, 0
    correct_abstentions, total_unanswerable = 0, 0

    try:
        for case in CASES:
            course = None
            if case.course_code:
                course = db.query(Course).filter_by(code=case.course_code).first()
                if course is None:
                    print(f"SKIP  {case.course_code}: not found in seeded data")
                    continue

            result = run_syllabus_qa(db, case.question, course_id=course.id if course else None)

            if case.expect_source_document is None:
                total_unanswerable += 1
                abstained = result.confidence == "none" and result.chunks_considered == 0
                correct_abstentions += int(abstained)
                status = "PASS" if abstained else "FAIL"
                print(f"{status}  [abstain] {case.course_code}: '{case.question}' -> confidence={result.confidence}")
            else:
                total_answerable += 1
                found = any(c.source_document == case.expect_source_document for c in result.citations)
                hits += int(found)
                status = "PASS" if found else "FAIL"
                print(
                    f"{status}  [hit@{len(result.citations)}] {case.course_code}: '{case.question}' -> "
                    f"expected {case.expect_source_document}, got "
                    f"{[c.source_document for c in result.citations]}"
                )

        print()
        if total_answerable:
            print(f"Hit rate: {hits}/{total_answerable} ({100 * hits / total_answerable:.0f}%)")
        if total_unanswerable:
            print(
                f"Abstention accuracy: {correct_abstentions}/{total_unanswerable} "
                f"({100 * correct_abstentions / total_unanswerable:.0f}%)"
            )
    finally:
        db.close()


if __name__ == "__main__":
    run_evaluation()
