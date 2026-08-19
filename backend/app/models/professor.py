import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.database.types import GUID

if TYPE_CHECKING:
    from app.models.department import Department


class Professor(Base, TimestampMixin):
    __tablename__ = "professors"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    university_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("universities.id"), nullable=False, index=True
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("departments.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(String(128), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    department: Mapped["Department | None"] = relationship(lazy="joined")
    rating: Mapped["ProfessorRating | None"] = relationship(
        back_populates="professor", uselist=False, lazy="joined"
    )


class ProfessorRating(Base, TimestampMixin):
    """Aggregate rating snapshot for a professor.

    Individual free-text reviews and theme extraction arrive in the Review
    Intelligence phase; this table holds only the aggregate numbers, each
    carrying provenance so the UI can badge them appropriately.
    """

    __tablename__ = "professor_ratings"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    professor_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("professors.id"), nullable=False, index=True, unique=True
    )
    professor: Mapped["Professor"] = relationship(back_populates="rating")

    overall_rating: Mapped[float] = mapped_column(Float, nullable=False)
    teaching_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    difficulty_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    would_take_again_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    num_ratings: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="student_reported")
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
