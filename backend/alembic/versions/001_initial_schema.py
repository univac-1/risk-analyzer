"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-01-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('videos',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('original_name', sa.String(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('duration', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    job_status_enum = postgresql.ENUM('pending', 'processing', 'completed', 'failed', name='jobstatus', create_type=False)
    job_status_enum.create(op.get_bind(), checkfirst=True)

    platform_enum = postgresql.ENUM('twitter', 'instagram', 'youtube', 'tiktok', 'other', name='platform', create_type=False)
    platform_enum.create(op.get_bind(), checkfirst=True)

    risk_level_enum = postgresql.ENUM('high', 'medium', 'low', 'none', name='risklevel', create_type=False)
    risk_level_enum.create(op.get_bind(), checkfirst=True)

    risk_category_enum = postgresql.ENUM('aggressiveness', 'discrimination', 'misleading', name='riskcategory', create_type=False)
    risk_category_enum.create(op.get_bind(), checkfirst=True)

    risk_source_enum = postgresql.ENUM('audio', 'ocr', 'video', name='risksource', create_type=False)
    risk_source_enum.create(op.get_bind(), checkfirst=True)

    op.create_table('analysis_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('video_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', job_status_enum, nullable=True),
        sa.Column('purpose', sa.String(), nullable=False),
        sa.Column('platform', platform_enum, nullable=False),
        sa.Column('target_audience', sa.String(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('risk_level', risk_level_enum, nullable=True),
        sa.Column('transcription_result', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ocr_result', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('video_analysis_result', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('risk_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.Float(), nullable=False),
        sa.Column('end_timestamp', sa.Float(), nullable=False),
        sa.Column('category', risk_category_enum, nullable=False),
        sa.Column('subcategory', sa.String(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('level', risk_level_enum, nullable=False),
        sa.Column('rationale', sa.String(), nullable=False),
        sa.Column('source', risk_source_enum, nullable=False),
        sa.Column('evidence', sa.String(), nullable=False),
        sa.ForeignKeyConstraint(['job_id'], ['analysis_jobs.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('risk_items')
    op.drop_table('analysis_jobs')
    op.drop_table('videos')

    op.execute("DROP TYPE IF EXISTS risksource")
    op.execute("DROP TYPE IF EXISTS riskcategory")
    op.execute("DROP TYPE IF EXISTS risklevel")
    op.execute("DROP TYPE IF EXISTS platform")
    op.execute("DROP TYPE IF EXISTS jobstatus")
