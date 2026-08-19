import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.course import Course, CourseTopic


class CourseRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, course_id: uuid.UUID) -> Course | None:
        return self.db.get(Course, course_id)

    def list_courses(
        self,
        university_id: uuid.UUID | None = None,
        department_code: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Course]:
        stmt = select(Course)
        if university_id is not None:
            stmt = stmt.where(Course.university_id == university_id)
        if department_code is not None:
            stmt = stmt.join(Course.department).where(
                Course.department.has(code=department_code)
            )
        stmt = stmt.order_by(Course.code).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).unique())

    def search(self, query: str, limit: int = 20) -> list[Course]:
        """Keyword search across code, title, description, and topic tags.

        Semantic (embedding-based) discovery is layered on top of this in
        Phase 4/6; this is the deterministic keyword baseline.
        """
        like_pattern = f"%{query.lower()}%"
        topic_subquery = (
            select(CourseTopic.course_id)
            .where(CourseTopic.topic.ilike(like_pattern))
            .distinct()
        )
        stmt = (
            select(Course)
            .where(
                or_(
                    Course.title.ilike(like_pattern),
                    Course.code.ilike(like_pattern),
                    Course.description.ilike(like_pattern),
                    Course.id.in_(topic_subquery),
                )
            )
            .order_by(Course.code)
            .limit(limit)
        )
        return list(self.db.scalars(stmt).unique())
