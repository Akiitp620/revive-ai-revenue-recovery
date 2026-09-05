"""add evaluation_runs and evaluation_run_metrics tables

Revision ID: b7a56e73d32f
Revises: ab369e851163
Create Date: 2026-09-05 22:37:03.380126

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b7a56e73d32f'
down_revision: Union[str, Sequence[str], None] = 'ab369e851163'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add evaluation_runs and evaluation_run_metrics tables.

    These tables were present in the SQLAlchemy models but were never added
    to the initial Alembic migration. On Render, alembic upgrade head is the
    only schema-creation path, so these tables were absent — causing a
    ProgrammingError (relation does not exist) on GET /api/v1/evaluations/latest.

    audit_logs schema differences are intentionally omitted: the Render DB
    already has seeded audit_log rows with the legacy column set, and adding
    NOT NULL columns without server_default would fail on existing rows.
    The application creates audit records correctly at runtime via the ORM.
    """
    op.create_table(
        'evaluation_runs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_version', sa.String(length=100), nullable=False),
        sa.Column('policy_version', sa.String(length=100), nullable=False),
        sa.Column('dataset_version', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_evaluation_runs_id'), 'evaluation_runs', ['id'], unique=False)

    op.create_table(
        'evaluation_run_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('evaluation_run_id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['evaluation_run_id'], ['evaluation_runs.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        op.f('ix_evaluation_run_metrics_evaluation_run_id'),
        'evaluation_run_metrics', ['evaluation_run_id'], unique=False,
    )
    op.create_index(
        op.f('ix_evaluation_run_metrics_id'),
        'evaluation_run_metrics', ['id'], unique=False,
    )


def downgrade() -> None:
    """Remove evaluation_runs and evaluation_run_metrics tables."""
    op.drop_index(op.f('ix_evaluation_run_metrics_id'), table_name='evaluation_run_metrics')
    op.drop_index(op.f('ix_evaluation_run_metrics_evaluation_run_id'), table_name='evaluation_run_metrics')
    op.drop_table('evaluation_run_metrics')
    op.drop_index(op.f('ix_evaluation_runs_id'), table_name='evaluation_runs')
    op.drop_table('evaluation_runs')
