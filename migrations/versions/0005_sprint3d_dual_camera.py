"""Sprint 3D dual-camera roles and session links.

Revision ID: 0005_sprint3d_dual_camera
Revises: 0004_sprint3c_candidate
Create Date: 2026-07-20
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_sprint3d_dual_camera"
down_revision = "0004_sprint3c_candidate"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("camera_selection_records") as batch_op:
        batch_op.add_column(sa.Column("camera_role", sa.String(length=20), server_default="primary", nullable=False))
        batch_op.create_index(
            "ix_camera_selections_candidate_role_selected", ["candidate_id", "camera_role", "selected_at"]
        )
    with op.batch_alter_table("camera_permission_records") as batch_op:
        batch_op.add_column(sa.Column("camera_role", sa.String(length=20), server_default="primary", nullable=False))
        batch_op.create_index(
            "ix_camera_permissions_candidate_role_checked", ["candidate_id", "camera_role", "checked_at"]
        )
    with op.batch_alter_table("examination_sessions") as batch_op:
        batch_op.add_column(sa.Column("secondary_camera_selection_id", sa.String(length=36), nullable=True))
        batch_op.add_column(sa.Column("secondary_camera_permission_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_sessions_secondary_camera_selection",
            "camera_selection_records",
            ["secondary_camera_selection_id"],
            ["camera_selection_id"],
        )
        batch_op.create_foreign_key(
            "fk_sessions_secondary_camera_permission",
            "camera_permission_records",
            ["secondary_camera_permission_id"],
            ["camera_permission_id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("examination_sessions") as batch_op:
        batch_op.drop_constraint(
            "fk_sessions_secondary_camera_permission",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_sessions_secondary_camera_selection",
            type_="foreignkey",
        )
        batch_op.drop_column("secondary_camera_permission_id")
        batch_op.drop_column("secondary_camera_selection_id")
    with op.batch_alter_table("camera_permission_records") as batch_op:
        batch_op.drop_index("ix_camera_permissions_candidate_role_checked")
        batch_op.drop_column("camera_role")
    with op.batch_alter_table("camera_selection_records") as batch_op:
        batch_op.drop_index("ix_camera_selections_candidate_role_selected")
        batch_op.drop_column("camera_role")
