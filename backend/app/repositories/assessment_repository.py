import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import AssessmentMetadata


class AssessmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_for_course(self, course_id: uuid.UUID) -> list[AssessmentMetadata]:
        stmt = select(AssessmentMetadata).where(AssessmentMetadata.course_id == course_id)
        return list(self.db.scalars(stmt).unique())

    def find_for_professor(self, professor_id: uuid.UUID) -> list[AssessmentMetadata]:
        stmt = select(AssessmentMetadata).where(AssessmentMetadata.professor_id == professor_id)
        return list(self.db.scalars(stmt).unique())

    def find_one(
        self, course_id: uuid.UUID, professor_id: uuid.UUID | None
    ) -> AssessmentMetadata | None:
        stmt = select(AssessmentMetadata).where(AssessmentMetadata.course_id == course_id)
        if professor_id is not None:
            stmt = stmt.where(AssessmentMetadata.professor_id == professor_id)
        return self.db.scalars(stmt).first()
