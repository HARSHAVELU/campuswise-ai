import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.syllabus import Syllabus, SyllabusChunk


class SyllabusRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, syllabus_id: uuid.UUID) -> Syllabus | None:
        return self.db.get(Syllabus, syllabus_id)

    def find_chunks(
        self,
        course_id: uuid.UUID | None = None,
        professor_id: uuid.UUID | None = None,
    ) -> list[SyllabusChunk]:
        stmt = select(SyllabusChunk).join(Syllabus)
        if course_id is not None:
            stmt = stmt.where(Syllabus.course_id == course_id)
        if professor_id is not None:
            stmt = stmt.where(Syllabus.professor_id == professor_id)
        return list(self.db.scalars(stmt).unique())
