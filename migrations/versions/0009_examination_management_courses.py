"""Add institution-scoped courses and candidate course registrations.

Revision ID: 0009_exam_management_courses
Revises: 0008_core_multimodal_evidence
"""

from alembic import op
import sqlalchemy as sa

revision = "0009_exam_management_courses"
down_revision = "0008_core_multimodal_evidence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "courses",
        sa.Column("course_id", sa.String(36), primary_key=True),
        sa.Column("institution_id", sa.String(36), sa.ForeignKey("institutions.institution_id"), nullable=False),
        sa.Column("course_code", sa.String(80), nullable=False),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("institution_id", "course_code", name="uq_courses_institution_course_code"),
    )
    op.create_index("ix_courses_institution_active", "courses", ["institution_id", "is_active"])
    op.create_table(
        "course_registrations",
        sa.Column("course_registration_id", sa.String(36), primary_key=True),
        sa.Column("institution_id", sa.String(36), sa.ForeignKey("institutions.institution_id"), nullable=False),
        sa.Column("course_id", sa.String(36), sa.ForeignKey("courses.course_id"), nullable=False),
        sa.Column("candidate_id", sa.String(36), sa.ForeignKey("candidates.candidate_id"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="registered"),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("course_id", "candidate_id", name="uq_course_registrations_course_candidate"),
    )
    op.create_index("ix_course_registrations_institution_status", "course_registrations", ["institution_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_course_registrations_institution_status", table_name="course_registrations")
    op.drop_table("course_registrations")
    op.drop_index("ix_courses_institution_active", table_name="courses")
    op.drop_table("courses")
