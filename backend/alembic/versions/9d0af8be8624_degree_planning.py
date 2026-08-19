"""degree planning: degree_programs, requirement groups, prerequisites, completed courses

Revision ID: 9d0af8be8624
Revises: b012a7087e02
Create Date: 2026-08-18

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "9d0af8be8624"
down_revision: Union[str, None] = "b012a7087e02"
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
        "degree_programs",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("university_id", UUID, sa.ForeignKey("universities.id"), nullable=False),
        sa.Column("department_id", UUID, sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("catalog_year", sa.Integer(), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_degree_programs_university_id", "degree_programs", ["university_id"])
    op.create_index("ix_degree_programs_department_id", "degree_programs", ["department_id"])

    op.create_table(
        "degree_requirement_groups",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("degree_program_id", UUID, sa.ForeignKey("degree_programs.id"), nullable=False),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("required_count", sa.Integer(), nullable=False),
        *_timestamps(),
    )
    op.create_index(
        "ix_degree_requirement_groups_degree_program_id",
        "degree_requirement_groups",
        ["degree_program_id"],
    )

    op.create_table(
        "degree_requirement_courses",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "requirement_group_id", UUID, sa.ForeignKey("degree_requirement_groups.id"), nullable=False
        ),
        sa.Column("course_id", UUID, sa.ForeignKey("courses.id"), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("requirement_group_id", "course_id", name="uq_requirement_course"),
    )
    op.create_index(
        "ix_degree_requirement_courses_requirement_group_id",
        "degree_requirement_courses",
        ["requirement_group_id"],
    )
    op.create_index(
        "ix_degree_requirement_courses_course_id", "degree_requirement_courses", ["course_id"]
    )

    op.create_table(
        "course_prerequisites",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("course_id", UUID, sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("group_number", sa.Integer(), nullable=False),
        sa.Column("prerequisite_course_id", UUID, sa.ForeignKey("courses.id"), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_course_prerequisites_course_id", "course_prerequisites", ["course_id"])
    op.create_index(
        "ix_course_prerequisites_prerequisite_course_id",
        "course_prerequisites",
        ["prerequisite_course_id"],
    )

    op.create_table(
        "student_completed_courses",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("user_id", UUID, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("course_id", UUID, sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("term_completed", sa.String(64), nullable=True),
        sa.Column("grade", sa.String(8), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("user_id", "course_id", name="uq_student_completed_course"),
    )
    op.create_index(
        "ix_student_completed_courses_user_id", "student_completed_courses", ["user_id"]
    )
    op.create_index(
        "ix_student_completed_courses_course_id", "student_completed_courses", ["course_id"]
    )

    op.add_column(
        "users", sa.Column("degree_program_id", UUID, sa.ForeignKey("degree_programs.id"), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("users", "degree_program_id")
    op.drop_table("student_completed_courses")
    op.drop_table("course_prerequisites")
    op.drop_table("degree_requirement_courses")
    op.drop_table("degree_requirement_groups")
    op.drop_table("degree_programs")
