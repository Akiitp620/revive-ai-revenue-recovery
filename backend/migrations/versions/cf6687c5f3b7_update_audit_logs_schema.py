"""update_audit_logs_schema

Revision ID: cf6687c5f3b7
Revises: b7a56e73d32f
Create Date: 2026-09-05 23:20:25.388639

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = 'cf6687c5f3b7'
down_revision: Union[str, Sequence[str], None] = 'b7a56e73d32f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute('DELETE FROM audit_logs')
    op.add_column('audit_logs', sa.Column('trace_id', sa.String(length=100), nullable=False))
    op.add_column('audit_logs', sa.Column('investigation_id', sa.String(length=100), nullable=False))
    op.add_column('audit_logs', sa.Column('payment_id', sa.String(length=100), nullable=False))
    op.add_column('audit_logs', sa.Column('actor', sa.String(length=100), nullable=False))
    op.add_column('audit_logs', sa.Column('event_type', sa.String(length=100), nullable=False))
    op.add_column('audit_logs', sa.Column('metadata_snapshot', sa.JSON(), nullable=True))
    op.add_column('audit_logs', sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False))
    
    with op.batch_alter_table('audit_logs') as batch_op:
        batch_op.drop_index('ix_audit_logs_entity_id')
        batch_op.drop_index('ix_audit_logs_entity_type')
        batch_op.drop_column('created_at')
        batch_op.drop_column('entity_type')
        batch_op.drop_column('before_snapshot')
        batch_op.drop_column('entity_id')
        batch_op.drop_column('after_snapshot')
        batch_op.drop_column('action')
        
        batch_op.create_index(batch_op.f('ix_audit_logs_event_type'), ['event_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_audit_logs_investigation_id'), ['investigation_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_audit_logs_payment_id'), ['payment_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_audit_logs_trace_id'), ['trace_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute('DELETE FROM audit_logs')
    with op.batch_alter_table('audit_logs') as batch_op:
        batch_op.add_column(sa.Column('action', sa.VARCHAR(length=100), nullable=False))
        batch_op.add_column(sa.Column('after_snapshot', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('entity_id', sa.INTEGER(), nullable=False))
        batch_op.add_column(sa.Column('before_snapshot', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('entity_type', sa.VARCHAR(length=100), nullable=False))
        batch_op.add_column(sa.Column('created_at', sa.DATETIME(), nullable=False))
        batch_op.drop_index(batch_op.f('ix_audit_logs_trace_id'))
        batch_op.drop_index(batch_op.f('ix_audit_logs_payment_id'))
        batch_op.drop_index(batch_op.f('ix_audit_logs_investigation_id'))
        batch_op.drop_index(batch_op.f('ix_audit_logs_event_type'))
        batch_op.create_index('ix_audit_logs_entity_type', ['entity_type'], unique=False)
        batch_op.create_index('ix_audit_logs_entity_id', ['entity_id'], unique=False)
        batch_op.drop_column('timestamp')
        batch_op.drop_column('metadata_snapshot')
        batch_op.drop_column('event_type')
        batch_op.drop_column('actor')
        batch_op.drop_column('payment_id')
        batch_op.drop_column('investigation_id')
        batch_op.drop_column('trace_id')

