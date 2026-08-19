import uuid

from pydantic import BaseModel, ConfigDict


class AssessmentMetadataRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    course_id: uuid.UUID
    professor_id: uuid.UUID | None = None
    midterm_format: str | None = None
    midterm_open_book: bool | None = None
    midterm_proctoring: str | None = None
    final_format: str | None = None
    final_open_book: bool | None = None
    final_proctoring: str | None = None
    has_group_project: bool
    has_individual_project: bool
    has_presentation: bool
    has_quizzes: bool
    attendance_required: bool | None = None
    attendance_weight_pct: float | None = None
    late_policy_summary: str | None = None
    weights: dict[str, float]
    confidence: float
    extraction_method: str
    source_document: str
    source_term: str | None = None

    @classmethod
    def from_model(cls, metadata) -> "AssessmentMetadataRead":
        return cls(
            course_id=metadata.course_id,
            professor_id=metadata.professor_id,
            midterm_format=metadata.midterm_format,
            midterm_open_book=metadata.midterm_open_book,
            midterm_proctoring=metadata.midterm_proctoring,
            final_format=metadata.final_format,
            final_open_book=metadata.final_open_book,
            final_proctoring=metadata.final_proctoring,
            has_group_project=metadata.has_group_project,
            has_individual_project=metadata.has_individual_project,
            has_presentation=metadata.has_presentation,
            has_quizzes=metadata.has_quizzes,
            attendance_required=metadata.attendance_required,
            attendance_weight_pct=metadata.attendance_weight_pct,
            late_policy_summary=metadata.late_policy_summary,
            weights=metadata.weights,
            confidence=metadata.confidence,
            extraction_method=metadata.extraction_method,
            source_document=metadata.syllabus.source_document,
            source_term=metadata.syllabus.term.name if metadata.syllabus.term else None,
        )
