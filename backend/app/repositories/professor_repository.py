import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.professor import Professor, ProfessorRating


class ProfessorRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, professor_id: uuid.UUID) -> Professor | None:
        return self.db.get(Professor, professor_id)

    def list_professors(
        self,
        university_id: uuid.UUID | None = None,
        min_rating: float | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Professor]:
        stmt = select(Professor)
        if university_id is not None:
            stmt = stmt.where(Professor.university_id == university_id)
        if min_rating is not None:
            stmt = stmt.join(ProfessorRating).where(
                ProfessorRating.overall_rating >= min_rating
            )
        stmt = stmt.order_by(Professor.name).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).unique())

    def search_by_name(self, query: str, limit: int = 20) -> list[Professor]:
        like_pattern = f"%{query.lower()}%"
        stmt = (
            select(Professor)
            .where(Professor.name.ilike(like_pattern))
            .order_by(Professor.name)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).unique())
