import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.grade_history import GradeHistory


class GradeRepository:
    def __init__(self, db: Session):
        self.db = db

    def find(
        self,
        course_id: uuid.UUID | None = None,
        professor_id: uuid.UUID | None = None,
    ) -> list[GradeHistory]:
        stmt = select(GradeHistory)
        if course_id is not None:
            stmt = stmt.where(GradeHistory.course_id == course_id)
        if professor_id is not None:
            stmt = stmt.where(GradeHistory.professor_id == professor_id)
        return list(self.db.scalars(stmt))
