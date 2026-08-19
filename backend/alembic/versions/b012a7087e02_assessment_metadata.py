"""exam intelligence: assessment_metadata

Revision ID: b012a7087e02
Revises: 3fe4cc981245
Create Date: 2026-08-18

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b012a7087e02"
down_revision: Union[str, None] = "3fe4cc981245"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)


def _timestamps():
    return [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "assessment_metadata",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("syllabus_id", UUID, sa.ForeignKey("syllabi.id"), nullable=False, unique=True),
        sa.Column("course_id", UUID, sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("professor_id", UUID, sa.ForeignKey("professors.id"), nullable=True),
        sa.Column("midterm_format", sa.String(16), nullable=True),
        sa.Column("midterm_open_book", sa.Boolean(), nullable=True),
        sa.Column("midterm_proctoring", sa.String(64), nullable=True),
        sa.Column("final_format", sa.String(16), nullable=True),
        sa.Column("final_open_book", sa.Boolean(), nullable=True),
        sa.Column("final_proctoring", sa.String(64), nullable=True),
        sa.Column("has_group_project", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_individual_project", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_presentation", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_quizzes", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("attendance_required", sa.Boolean(), nullable=True),
        sa.Column("attendance_weight_pct", sa.Float(), nullable=True),
        sa.Column("late_policy_summary", sa.Text(), nullable=True),
        sa.Column("weights", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("extraction_method", sa.String(16), nullable=False, server_default="rule_based"),
        *_timestamps(),
    )
    op.create_index("ix_assessment_metadata_syllabus_id", "assessment_metadata", ["syllabus_id"])
    op.create_index("ix_assessment_metadata_course_id", "assessment_metadata", ["course_id"])
    op.create_index("ix_assessment_metadata_professor_id", "assessment_metadata", ["professor_id"])


def downgrade() -> None:
    op.drop_table("assessment_metadata")
