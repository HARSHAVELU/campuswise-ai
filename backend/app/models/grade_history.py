import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin
from app.database.types import GUID

#: Grade buckets stored as individual counts so statistics (mean GPA,
#: A-range %, etc.) can be computed deterministically in app.analytics —
#: never estimated or invented by an LLM.
GRADE_BUCKETS = [
    "a_plus", "a", "a_minus",
    "b_plus", "b", "b_minus",
    "c_plus", "c", "c_minus",
    "d_plus", "d", "d_minus",
    "f",
]


class GradeHistory(Base, TimestampMixin):
    __tablename__ = "grade_history"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("courses.id"), nullable=False, index=True
    )
    professor_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("professors.id"), nullable=True, index=True
    )
    term_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("terms.id"), nullable=False, index=True
    )
    section_number: Mapped[str | None] = mapped_column(String(16), nullable=True)

    a_plus: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    a: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    a_minus: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    b_plus: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    b: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    b_minus: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    c_plus: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    c: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    c_minus: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    d_plus: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    d: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    d_minus: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    f: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    withdrawals: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    source_type: Mapped[str] = mapped_column(String(32), nullable=False, default="historical")
