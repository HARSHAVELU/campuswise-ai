import enum
import uuid
from datetime import time as time_type
from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.database.types import GUID

if TYPE_CHECKING:
    from app.models.building import Room
    from app.models.course import Course
    from app.models.professor import Professor
    from app.models.term import Term


class DeliveryMode(str, enum.Enum):
    IN_PERSON = "in_person"
    ONLINE = "online"
    HYBRID = "hybrid"


class DayOfWeek(str, enum.Enum):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class Section(Base, TimestampMixin):
    __tablename__ = "sections"
    __table_args__ = (
        UniqueConstraint("course_id", "term_id", "section_number", name="uq_section_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    course_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("courses.id"), nullable=False, index=True
    )
    term_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("terms.id"), nullable=False, index=True
    )
    professor_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("professors.id"), nullable=True, index=True
    )
    section_number: Mapped[str] = mapped_column(String(16), nullable=False)
    delivery_mode: Mapped[DeliveryMode] = mapped_column(
        Enum(DeliveryMode, native_enum=False), nullable=False, default=DeliveryMode.IN_PERSON
    )
    seats_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    seats_available: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    course: Mapped["Course"] = relationship(lazy="joined")
    term: Mapped["Term"] = relationship(lazy="joined")
    professor: Mapped["Professor | None"] = relationship(lazy="joined")
    meetings: Mapped[list["SectionMeeting"]] = relationship(
        back_populates="section", cascade="all, delete-orphan", lazy="selectin"
    )


class SectionMeeting(Base, TimestampMixin):
    __tablename__ = "section_meetings"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    section_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("sections.id"), nullable=False, index=True
    )
    room_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("rooms.id"), nullable=True, index=True
    )
    day_of_week: Mapped[DayOfWeek] = mapped_column(Enum(DayOfWeek, native_enum=False), nullable=False)
    start_time: Mapped[time_type] = mapped_column(Time, nullable=False)
    end_time: Mapped[time_type] = mapped_column(Time, nullable=False)

    section: Mapped["Section"] = relationship(back_populates="meetings")
    room: Mapped["Room | None"] = relationship(lazy="joined")
