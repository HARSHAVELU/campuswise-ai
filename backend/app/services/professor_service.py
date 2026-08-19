import uuid

from sqlalchemy.orm import Session

from app.analytics.grade_stats import GradeDistributionStats, compute_grade_distribution
from app.models.professor import Professor
from app.repositories.grade_repository import GradeRepository
from app.repositories.professor_repository import ProfessorRepository


class ProfessorService:
    def __init__(self, db: Session):
        self.repo = ProfessorRepository(db)
        self.grade_repo = GradeRepository(db)

    def get(self, professor_id: uuid.UUID) -> Professor | None:
        return self.repo.get(professor_id)

    def list_professors(
        self,
        university_id: uuid.UUID | None = None,
        min_rating: float | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Professor]:
        return self.repo.list_professors(
            university_id=university_id, min_rating=min_rating, limit=limit, offset=offset
        )

    def search_by_name(self, query: str, limit: int = 20) -> list[Professor]:
        return self.repo.search_by_name(query=query, limit=limit)

    def grade_distribution(
        self, professor_id: uuid.UUID, course_id: uuid.UUID | None = None
    ) -> GradeDistributionStats:
        records = self.grade_repo.find(professor_id=professor_id, course_id=course_id)
        return compute_grade_distribution(records)
