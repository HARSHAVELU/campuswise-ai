import uuid
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin
from app.database.types import GUID

if TYPE_CHECKING:
    from app.models.syllabus import Syllabus


class AssessmentMetadata(Base, TimestampMixin):
    """Structured assessment/exam info extracted from a syllabus.

    Every value here is an *extraction* from a specific syllabus document,
    not a verified institutional fact -- it carries `confidence` and
    `extraction_method`, and the API always surfaces the source syllabus so
    the UI can badge it as SYLLABUS-derived rather than OFFICIAL (see
    docs/architecture-proposal.md, "Data Trust and Source Provenance").
    """

    __tablename__ = "assessment_metadata"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    syllabus_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("syllabi.id"), nullable=False, unique=True, index=True
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("courses.id"), nullable=False, index=True
    )
    professor_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("professors.id"), nullable=True, index=True
    )

    midterm_format: Mapped[str | None] = mapped_column(String(16), nullable=True)
    midterm_open_book: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    midterm_proctoring: Mapped[str | None] = mapped_column(String(64), nullable=True)

    final_format: Mapped[str | None] = mapped_column(String(16), nullable=True)
    final_open_book: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    final_proctoring: Mapped[str | None] = mapped_column(String(64), nullable=True)

    has_group_project: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_individual_project: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_presentation: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_quizzes: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    attendance_required: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    attendance_weight_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    late_policy_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    weights: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.7)
    extraction_method: Mapped[str] = mapped_column(String(16), nullable=False, default="rule_based")

    syllabus: Mapped["Syllabus"] = relationship(lazy="joined")
