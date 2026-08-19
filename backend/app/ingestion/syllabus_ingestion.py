import uuid

from sqlalchemy.orm import Session

from app.agents.assessment_extractor import extract_assessment
from app.ingestion.chunking import chunk_text
from app.models.assessment import AssessmentMetadata
from app.models.syllabus import Syllabus, SyllabusChunk
from app.retrieval.embeddings import embed_batch


def ingest_syllabus(
    db: Session,
    *,
    university_id: uuid.UUID,
    course_id: uuid.UUID,
    professor_id: uuid.UUID | None,
    term_id: uuid.UUID | None,
    title: str,
    source_document: str,
    raw_text: str,
) -> Syllabus:
    syllabus = Syllabus(
        id=uuid.uuid4(),
        university_id=university_id,
        course_id=course_id,
        professor_id=professor_id,
        term_id=term_id,
        title=title,
        source_document=source_document,
        raw_text=raw_text,
        source_type="syllabus",
    )
    db.add(syllabus)
    db.flush()

    chunks = chunk_text(raw_text)
    embeddings = embed_batch(chunks, input_type="document")

    for index, (content, embedding) in enumerate(zip(chunks, embeddings)):
        db.add(
            SyllabusChunk(
                id=uuid.uuid4(),
                syllabus_id=syllabus.id,
                chunk_index=index,
                content=content,
                embedding=embedding,
            )
        )

    extracted = extract_assessment(raw_text)
    db.add(
        AssessmentMetadata(
            id=uuid.uuid4(),
            syllabus_id=syllabus.id,
            course_id=course_id,
            professor_id=professor_id,
            midterm_format=extracted.get("midterm_format"),
            midterm_open_book=extracted.get("midterm_open_book"),
            midterm_proctoring=extracted.get("midterm_proctoring"),
            final_format=extracted.get("final_format"),
            final_open_book=extracted.get("final_open_book"),
            final_proctoring=extracted.get("final_proctoring"),
            has_group_project=extracted.get("has_group_project", False),
            has_individual_project=extracted.get("has_individual_project", False),
            has_presentation=extracted.get("has_presentation", False),
            has_quizzes=extracted.get("has_quizzes", False),
            attendance_required=extracted.get("attendance_required"),
            attendance_weight_pct=extracted.get("attendance_weight_pct"),
            late_policy_summary=extracted.get("late_policy_summary"),
            weights=extracted.get("weights", {}),
            confidence=extracted.get("confidence", 0.7),
            extraction_method=extracted.get("extraction_method", "rule_based"),
        )
    )

    return syllabus
