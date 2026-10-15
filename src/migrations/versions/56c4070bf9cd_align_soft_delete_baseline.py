"""Align synthetic dev baseline with existing soft-delete ORM.

Only for the dev lineage. Real data requires inventory, backup and approval
of the is_active mapping. Unknown deletion times remain NULL.
"""
from alembic import op
import sqlalchemy as sa

revision = "56c4070bf9cd"
down_revision = "d98c55d6402c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("courses", "student_courses"):
        op.add_column(table, sa.Column("is_deleted", sa.Boolean(), nullable=True))
        op.add_column(table, sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        op.execute(sa.text(f'UPDATE {table} SET is_deleted = NOT is_active'))
        # Check every row before enforcing NOT NULL and removing the old field.
        op.execute(sa.text(f"""
            DO $$ BEGIN
                IF EXISTS (SELECT 1 FROM {table}
                           WHERE is_deleted IS NULL OR is_deleted != NOT is_active)
                THEN RAISE EXCEPTION 'soft-delete backfill mismatch';
                END IF;
            END $$;
        """))
        op.alter_column(table, "is_deleted", nullable=False)
        op.drop_column(table, "is_active")


def downgrade() -> None:
    # Lossy for deleted_at: intended only for disposable test round-trips.
    for table in ("student_courses", "courses"):
        op.add_column(table, sa.Column("is_active", sa.Boolean(), nullable=True))
        op.execute(sa.text(f'UPDATE {table} SET is_active = NOT is_deleted'))
        op.alter_column(table, "is_active", nullable=False)
        op.drop_column(table, "deleted_at")
        op.drop_column(table, "is_deleted")
