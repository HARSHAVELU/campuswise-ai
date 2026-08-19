import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.section import Section
from app.models.term import Term


class SectionRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, section_id: uuid.UUID) -> Section | None:
        return self.db.get(Section, section_id)

    def list_for_courses(
        self, course_ids: list[uuid.UUID], active_term_only: bool = True
    ) -> list[Section]:
        if not course_ids:
            return []
        stmt = select(Section).where(Section.course_id.in_(course_ids))
        if active_term_only:
            stmt = stmt.join(Term, Section.term_id == Term.id).where(
                Term.is_active_for_planning.is_(True)
            )
        return list(self.db.scalars(stmt).unique())

    def list_sections(
        self,
        course_id: uuid.UUID | None = None,
        term_id: uuid.UUID | None = None,
        professor_id: uuid.UUID | None = None,
        delivery_mode: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Section]:
        stmt = select(Section)
        if course_id is not None:
            stmt = stmt.where(Section.course_id == course_id)
        if term_id is not None:
            stmt = stmt.where(Section.term_id == term_id)
        if professor_id is not None:
            stmt = stmt.where(Section.professor_id == professor_id)
        if delivery_mode is not None:
            stmt = stmt.where(Section.delivery_mode == delivery_mode)
        stmt = stmt.order_by(Section.section_number).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).unique())
