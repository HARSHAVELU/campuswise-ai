import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.database.types import GUID, EmbeddingVector

if TYPE_CHECKING:
    from app.models.course import Course
    from app.models.professor import Professor
    from app.models.term import Term


class Syllabus(Base, TimestampMixin):
    __tablename__ = "syllabi"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    university_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("universities.id"), nullable=False, index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("courses.id"), nullable=False, index=True
    )
    professor_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("professors.id"), nullable=True, index=True
    )
    term_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("terms.id"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_document: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="syllabus")

    course: Mapped["Course"] = relationship(lazy="joined")
    professor: Mapped["Professor | None"] = relationship(lazy="joined")
    term: Mapped["Term | None"] = relationship(lazy="joined")
    chunks: Mapped[list["SyllabusChunk"]] = relationship(
        back_populates="syllabus", cascade="all, delete-orphan", lazy="selectin"
    )


class SyllabusChunk(Base, TimestampMixin):
    __tablename__ = "syllabus_chunks"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    syllabus_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("syllabi.id"), nullable=False, index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(EmbeddingVector(), nullable=False)

    syllabus: Mapped["Syllabus"] = relationship(back_populates="chunks")
