"""Add edit session tables for timeline editor

Revision ID: 002
Revises: 001
Create Date: 2026-02-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create edit session status enum
    edit_session_status_enum = postgresql.ENUM(
        'draft', 'exporting', 'completed',
        name='editsessionstatus',
        create_type=False
    )
    edit_session_status_enum.create(op.get_bind(), checkfirst=True)

    # Create edit action type enum
    edit_action_type_enum = postgresql.ENUM(
        'cut', 'mute', 'mosaic', 'telop', 'skip',
        name='editactiontype',
        create_type=False
    )
    edit_action_type_enum.create(op.get_bind(), checkfirst=True)

    # Create export job status enum
    export_job_status_enum = postgresql.ENUM(
        'pending', 'processing', 'completed', 'failed',
        name='exportjobstatus',
        create_type=False
    )
    export_job_status_enum.create(op.get_bind(), checkfirst=True)

    # Create edit_sessions table
    op.create_table(
        'edit_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', edit_session_status_enum, nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['job_id'], ['analysis_jobs.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id')
    )

    # Create edit_actions table
    op.create_table(
        'edit_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('risk_item_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('type', edit_action_type_enum, nullable=False),
        sa.Column('start_time', sa.Float(), nullable=False),
        sa.Column('end_time', sa.Float(), nullable=False),
        sa.Column('options', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['session_id'], ['edit_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['risk_item_id'], ['risk_items.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_edit_actions_session', 'edit_actions', ['session_id'])

    # Create export_jobs table
    op.create_table(
        'export_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', export_job_status_enum, nullable=False, server_default='pending'),
        sa.Column('output_path', sa.String(500), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['edit_sessions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_export_jobs_session', 'export_jobs', ['session_id'])


def downgrade() -> None:
    op.drop_index('idx_export_jobs_session', table_name='export_jobs')
    op.drop_table('export_jobs')

    op.drop_index('idx_edit_actions_session', table_name='edit_actions')
    op.drop_table('edit_actions')

    op.drop_table('edit_sessions')

    op.execute("DROP TYPE IF EXISTS exportjobstatus")
    op.execute("DROP TYPE IF EXISTS editactiontype")
    op.execute("DROP TYPE IF EXISTS editsessionstatus")
