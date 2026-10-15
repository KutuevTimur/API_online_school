"""account invitations activation and nullable email

Revision ID: 711e94443ef3
Revises: d897e9b55d47
Create Date: 2026-10-15 11:16:29.110131

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '711e94443ef3'
down_revision: Union[str, Sequence[str], None] = 'd897e9b55d47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    collisions = bind.execute(sa.text("SELECT count(*) FROM users a JOIN users b ON a.username = b.email WHERE a.id <> b.id")).scalar_one()
    if collisions:
        import logging
        logging.getLogger("alembic.runtime.migration").warning(
            "%s legacy username/email cross-collisions; username-only login resolves by username, emails preserved", collisions)

    op.create_table('auth_rate_limits',
    sa.Column('key', sa.String(length=64), nullable=False),
    sa.Column('window', sa.Integer(), nullable=False),
    sa.Column('count', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('key')
    )
    op.create_table('account_audit',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('actor_user_id', sa.Integer(), nullable=False),
    sa.Column('target_user_id', sa.Integer(), nullable=False),
    sa.Column('action', sa.String(length=32), nullable=False),
    sa.Column('result', sa.String(length=16), nullable=False),
    sa.Column('correlation_id', sa.String(length=32), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['actor_user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['target_user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('account_invitations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('purpose', sa.String(length=16), nullable=False),
    sa.Column('digest', sa.String(length=64), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('consumed', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('digest')
    )
    op.create_index(op.f('ix_account_invitations_user_id'), 'account_invitations', ['user_id'], unique=False)
    op.add_column('users', sa.Column('is_activated', sa.Boolean(), server_default=sa.text('true'), nullable=False))
    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(length=255),
               nullable=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    if bind.execute(sa.text("SELECT count(*) FROM users WHERE email IS NULL OR NOT is_activated")).scalar_one():
        raise RuntimeError("Cannot downgrade T05b with nullable email or pending accounts; no data changed")

    op.alter_column('users', 'email',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)
    op.drop_column('users', 'is_activated')
    op.drop_index(op.f('ix_account_invitations_user_id'), table_name='account_invitations')
    op.drop_table('account_invitations')
    op.drop_table('account_audit')
    op.drop_table('auth_rate_limits')
    # ### end Alembic commands ###
