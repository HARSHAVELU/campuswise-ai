import uuid

from sqlalchemy.orm import Session

from app.models.course import Course
from app.repositories.course_repository import CourseRepository


class CourseService:
    def __init__(self, db: Session):
        self.repo = CourseRepository(db)

    def get(self, course_id: uuid.UUID) -> Course | None:
        return self.repo.get(course_id)

    def list_courses(
        self,
        university_id: uuid.UUID | None = None,
        department_code: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Course]:
        return self.repo.list_courses(
            university_id=university_id,
            department_code=department_code,
            limit=limit,
            offset=offset,
        )

    def search(self, query: str, limit: int = 20) -> list[Course]:
        return self.repo.search(query=query, limit=limit)
