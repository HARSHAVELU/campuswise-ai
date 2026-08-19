import enum
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.database.types import GUID

if TYPE_CHECKING:
    from app.models.department import Department


class CourseLevel(str, enum.Enum):
    UNDERGRADUATE = "undergraduate"
    GRADUATE = "graduate"


class Course(Base, TimestampMixin):
    __tablename__ = "courses"
    __table_args__ = (UniqueConstraint("department_id", "code", name="uq_course_code"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    university_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("universities.id"), nullable=False, index=True
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("departments.id"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    credit_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    level: Mapped[CourseLevel] = mapped_column(
        Enum(CourseLevel, native_enum=False), nullable=False, default=CourseLevel.UNDERGRADUATE
    )

    department: Mapped["Department"] = relationship(lazy="joined")
    topics: Mapped[list["CourseTopic"]] = relationship(
        back_populates="course", cascade="all, delete-orphan", lazy="selectin"
    )


class CourseTopic(Base, TimestampMixin):
    """Keyword/skill tags used for semantic and keyword course discovery."""

    __tablename__ = "course_topics"
    __table_args__ = (UniqueConstraint("course_id", "topic", name="uq_course_topic"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("courses.id"), nullable=False, index=True
    )
    topic: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    course: Mapped["Course"] = relationship(back_populates="topics")
