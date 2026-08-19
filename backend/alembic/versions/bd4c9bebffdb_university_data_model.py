"""university data model: universities, departments, courses, professors, terms, sections, grades

Revision ID: bd4c9bebffdb
Revises: de59ebb36ae6
Create Date: 2026-08-18

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "bd4c9bebffdb"
down_revision: Union[str, None] = "de59ebb36ae6"
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
        "universities",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("short_name", sa.String(32), nullable=False),
        sa.Column("city", sa.String(128), nullable=True),
        sa.Column("state", sa.String(64), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_universities_short_name", "universities", ["short_name"], unique=True)

    op.create_table(
        "departments",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("university_id", UUID, sa.ForeignKey("universities.id"), nullable=False),
        sa.Column("code", sa.String(16), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("university_id", "code", name="uq_department_code"),
    )
    op.create_index("ix_departments_university_id", "departments", ["university_id"])

    op.create_table(
        "terms",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("university_id", UUID, sa.ForeignKey("universities.id"), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("season", sa.String(16), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column(
            "is_active_for_planning", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        *_timestamps(),
        sa.UniqueConstraint("university_id", "year", "season", name="uq_term"),
    )
    op.create_index("ix_terms_university_id", "terms", ["university_id"])

    op.create_table(
        "buildings",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("university_id", UUID, sa.ForeignKey("universities.id"), nullable=False),
        sa.Column("code", sa.String(16), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("university_id", "code", name="uq_building_code"),
    )
    op.create_index("ix_buildings_university_id", "buildings", ["university_id"])

    op.create_table(
        "rooms",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("building_id", UUID, sa.ForeignKey("buildings.id"), nullable=False),
        sa.Column("room_number", sa.String(32), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("building_id", "room_number", name="uq_room_number"),
    )
    op.create_index("ix_rooms_building_id", "rooms", ["building_id"])

    op.create_table(
        "courses",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("university_id", UUID, sa.ForeignKey("universities.id"), nullable=False),
        sa.Column("department_id", UUID, sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("code", sa.String(32), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("credit_hours", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("level", sa.String(32), nullable=False, server_default="undergraduate"),
        *_timestamps(),
        sa.UniqueConstraint("department_id", "code", name="uq_course_code"),
    )
    op.create_index("ix_courses_university_id", "courses", ["university_id"])
    op.create_index("ix_courses_department_id", "courses", ["department_id"])
    op.create_index("ix_courses_code", "courses", ["code"])

    op.create_table(
        "course_topics",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("course_id", UUID, sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("topic", sa.String(128), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("course_id", "topic", name="uq_course_topic"),
    )
    op.create_index("ix_course_topics_course_id", "course_topics", ["course_id"])
    op.create_index("ix_course_topics_topic", "course_topics", ["topic"])

    op.create_table(
        "professors",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("university_id", UUID, sa.ForeignKey("universities.id"), nullable=False),
        sa.Column("department_id", UUID, sa.ForeignKey("departments.id"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("title", sa.String(128), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        *_timestamps(),
    )
    op.create_index("ix_professors_university_id", "professors", ["university_id"])
    op.create_index("ix_professors_department_id", "professors", ["department_id"])
    op.create_index("ix_professors_name", "professors", ["name"])

    op.create_table(
        "professor_ratings",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "professor_id", UUID, sa.ForeignKey("professors.id"), nullable=False, unique=True
        ),
        sa.Column("overall_rating", sa.Float(), nullable=False),
        sa.Column("teaching_rating", sa.Float(), nullable=True),
        sa.Column("difficulty_rating", sa.Float(), nullable=True),
        sa.Column("would_take_again_pct", sa.Float(), nullable=True),
        sa.Column("num_ratings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "source_type", sa.String(32), nullable=False, server_default="student_reported"
        ),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        *_timestamps(),
    )
    op.create_index("ix_professor_ratings_professor_id", "professor_ratings", ["professor_id"])

    op.create_table(
        "sections",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("course_id", UUID, sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("term_id", UUID, sa.ForeignKey("terms.id"), nullable=False),
        sa.Column("professor_id", UUID, sa.ForeignKey("professors.id"), nullable=True),
        sa.Column("section_number", sa.String(16), nullable=False),
        sa.Column(
            "delivery_mode", sa.String(16), nullable=False, server_default="in_person"
        ),
        sa.Column("seats_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("seats_available", sa.Integer(), nullable=False, server_default="0"),
        *_timestamps(),
        sa.UniqueConstraint("course_id", "term_id", "section_number", name="uq_section_number"),
    )
    op.create_index("ix_sections_course_id", "sections", ["course_id"])
    op.create_index("ix_sections_term_id", "sections", ["term_id"])
    op.create_index("ix_sections_professor_id", "sections", ["professor_id"])

    op.create_table(
        "section_meetings",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("section_id", UUID, sa.ForeignKey("sections.id"), nullable=False),
        sa.Column("room_id", UUID, sa.ForeignKey("rooms.id"), nullable=True),
        sa.Column("day_of_week", sa.String(16), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_section_meetings_section_id", "section_meetings", ["section_id"])
    op.create_index("ix_section_meetings_room_id", "section_meetings", ["room_id"])

    op.create_table(
        "grade_history",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("course_id", UUID, sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("professor_id", UUID, sa.ForeignKey("professors.id"), nullable=True),
        sa.Column("term_id", UUID, sa.ForeignKey("terms.id"), nullable=False),
        sa.Column("section_number", sa.String(16), nullable=True),
        sa.Column("a_plus", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("a", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("a_minus", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("b_plus", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("b", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("b_minus", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("c_plus", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("c", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("c_minus", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("d_plus", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("d", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("d_minus", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("f", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("withdrawals", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_type", sa.String(32), nullable=False, server_default="historical"),
        *_timestamps(),
    )
    op.create_index("ix_grade_history_course_id", "grade_history", ["course_id"])
    op.create_index("ix_grade_history_professor_id", "grade_history", ["professor_id"])
    op.create_index("ix_grade_history_term_id", "grade_history", ["term_id"])


def downgrade() -> None:
    op.drop_table("grade_history")
    op.drop_table("section_meetings")
    op.drop_table("sections")
    op.drop_table("professor_ratings")
    op.drop_table("professors")
    op.drop_table("course_topics")
    op.drop_table("courses")
    op.drop_table("rooms")
    op.drop_table("buildings")
    op.drop_table("terms")
    op.drop_table("departments")
    op.drop_table("universities")
