import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.database.types import GUID

if TYPE_CHECKING:
    from app.models.course import Course


class DegreeProgram(Base, TimestampMixin):
    __tablename__ = "degree_programs"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    university_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("universities.id"), nullable=False, index=True
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("departments.id"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    catalog_year: Mapped[int] = mapped_column(Integer, nullable=False)

    requirement_groups: Mapped[list["DegreeRequirementGroup"]] = relationship(
        back_populates="degree_program", cascade="all, delete-orphan", lazy="selectin"
    )


class DegreeRequirementGroup(Base, TimestampMixin):
    """A named bucket (e.g. "Core", "Electives", "Capstone") requiring some
    number of courses to be completed from its eligible course list."""

    __tablename__ = "degree_requirement_groups"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    degree_program_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("degree_programs.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    required_count: Mapped[int] = mapped_column(Integer, nullable=False)

    degree_program: Mapped["DegreeProgram"] = relationship(back_populates="requirement_groups")
    eligible_courses: Mapped[list["DegreeRequirementCourse"]] = relationship(
        back_populates="requirement_group", cascade="all, delete-orphan", lazy="selectin"
    )


class DegreeRequirementCourse(Base, TimestampMixin):
    """Junction: which courses count toward a requirement group."""

    __tablename__ = "degree_requirement_courses"
    __table_args__ = (
        UniqueConstraint("requirement_group_id", "course_id", name="uq_requirement_course"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    requirement_group_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("degree_requirement_groups.id"), nullable=False, index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("courses.id"), nullable=False, index=True
    )

    requirement_group: Mapped["DegreeRequirementGroup"] = relationship(back_populates="eligible_courses")
    course: Mapped["Course"] = relationship(lazy="joined")


class CoursePrerequisite(Base, TimestampMixin):
    """One prerequisite option for a course.

    Rows sharing the same (course_id, group_number) are OR'd together;
    different group_numbers for the same course are AND'd together. E.g.
    "Course C requires A AND (B OR D)" is represented as:
        (course=C, group=1, prerequisite=A)
        (course=C, group=2, prerequisite=B)
        (course=C, group=2, prerequisite=D)
    """

    __tablename__ = "course_prerequisites"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("courses.id"), nullable=False, index=True
    )
    group_number: Mapped[int] = mapped_column(Integer, nullable=False)
    prerequisite_course_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("courses.id"), nullable=False, index=True
    )

    course: Mapped["Course"] = relationship(foreign_keys=[course_id], lazy="joined")
    prerequisite_course: Mapped["Course"] = relationship(
        foreign_keys=[prerequisite_course_id], lazy="joined"
    )


class StudentCompletedCourse(Base, TimestampMixin):
    __tablename__ = "student_completed_courses"
    __table_args__ = (UniqueConstraint("user_id", "course_id", name="uq_student_completed_course"),)

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    course_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("courses.id"), nullable=False, index=True
    )
    term_completed: Mapped[str | None] = mapped_column(String(64), nullable=True)
    grade: Mapped[str | None] = mapped_column(String(8), nullable=True)

    course: Mapped["Course"] = relationship(lazy="joined")
