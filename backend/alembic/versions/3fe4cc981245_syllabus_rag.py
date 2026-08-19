"""syllabus rag: pgvector extension, syllabi, syllabus_chunks

Revision ID: 3fe4cc981245
Revises: bd4c9bebffdb
Create Date: 2026-08-18

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "3fe4cc981245"
down_revision: Union[str, None] = "bd4c9bebffdb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = postgresql.UUID(as_uuid=True)
EMBEDDING_DIM = 512


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
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "syllabi",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("university_id", UUID, sa.ForeignKey("universities.id"), nullable=False),
        sa.Column("course_id", UUID, sa.ForeignKey("courses.id"), nullable=False),
        sa.Column("professor_id", UUID, sa.ForeignKey("professors.id"), nullable=True),
        sa.Column("term_id", UUID, sa.ForeignKey("terms.id"), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("source_document", sa.String(255), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False, server_default="syllabus"),
        *_timestamps(),
    )
    op.create_index("ix_syllabi_university_id", "syllabi", ["university_id"])
    op.create_index("ix_syllabi_course_id", "syllabi", ["course_id"])
    op.create_index("ix_syllabi_professor_id", "syllabi", ["professor_id"])
    op.create_index("ix_syllabi_term_id", "syllabi", ["term_id"])

    op.create_table(
        "syllabus_chunks",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("syllabus_id", UUID, sa.ForeignKey("syllabi.id"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
        *_timestamps(),
    )
    op.create_index("ix_syllabus_chunks_syllabus_id", "syllabus_chunks", ["syllabus_id"])


def downgrade() -> None:
    op.drop_table("syllabus_chunks")
    op.drop_table("syllabi")
    op.execute("DROP EXTENSION IF EXISTS vector")
