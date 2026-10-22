"""Initial users, events and registrations schema."""
from alembic import op
import sqlalchemy as sa

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("btrim(name) <> ''", name='ck_users_name'))
    op.create_table('events',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('capacity', sa.Integer(), nullable=False),
        sa.Column('remaining_slots', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("btrim(title) <> ''", name='ck_events_title'),
        sa.CheckConstraint('capacity BETWEEN 1 AND 10000', name='ck_events_capacity'),
        sa.CheckConstraint('remaining_slots BETWEEN 0 AND capacity', name='ck_events_slots'))
    op.create_table('registrations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('event_id', sa.Integer(), sa.ForeignKey('events.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('status', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('active', 'cancelled')", name='ck_registration_status'),
        sa.CheckConstraint("(status = 'active' AND cancelled_at IS NULL) OR (status = 'cancelled' AND cancelled_at IS NOT NULL)", name='ck_registration_cancelled_at'))
    op.create_index('uq_active_registration', 'registrations', ['event_id', 'user_id'], unique=True, postgresql_where=sa.text("status = 'active'"))


def downgrade():
    op.drop_table('registrations')
    op.drop_table('events')
    op.drop_table('users')
