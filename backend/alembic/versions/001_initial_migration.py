"""Initial migration - create jobs, sources, and users tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create jobs table
    op.create_table('jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('source_url', sa.String(length=500), nullable=False),
        sa.Column('title', sa.String(length=300), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('budget', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=True),
        sa.Column('job_type', sa.String(length=20), nullable=True),
        sa.Column('stack', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('posted_at', sa.DateTime(), nullable=True),
        sa.Column('raw_hash', sa.String(length=64), nullable=False),
        sa.Column('ai_score', sa.Integer(), nullable=True),
        sa.Column('ai_reason', sa.Text(), nullable=True),
        sa.Column('should_apply', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_jobs_id'), 'jobs', ['id'], unique=False)
    op.create_index(op.f('ix_jobs_source'), 'jobs', ['source'], unique=False)
    op.create_index(op.f('ix_jobs_job_type'), 'jobs', ['job_type'], unique=False)
    op.create_index(op.f('ix_jobs_raw_hash'), 'jobs', ['raw_hash'], unique=True)
    op.create_index(op.f('ix_jobs_ai_score'), 'jobs', ['ai_score'], unique=False)
    op.create_index(op.f('ix_jobs_status'), 'jobs', ['status'], unique=False)
    op.create_index(op.f('ix_jobs_created_at'), 'jobs', ['created_at'], unique=False)
    op.create_index(op.f('ix_jobs_source_url'), 'jobs', ['source_url'], unique=True)

    # Create sources table
    op.create_table('sources',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('source_type', sa.String(length=20), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('parse_interval_minutes', sa.Integer(), nullable=True),
        sa.Column('last_parsed_at', sa.DateTime(), nullable=True),
        sa.Column('total_jobs_parsed', sa.Integer(), nullable=True),
        sa.Column('config', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sources_id'), 'sources', ['id'], unique=False)
    op.create_index(op.f('ix_sources_name'), 'sources', ['name'], unique=True)

    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.String(length=50), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Integer(), nullable=True),
        sa.Column('min_score', sa.Integer(), nullable=True),
        sa.Column('preferred_sources', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('preferred_stack', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('min_budget', sa.Integer(), nullable=True),
        sa.Column('max_budget', sa.Integer(), nullable=True),
        sa.Column('preferred_job_types', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('notification_enabled', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_telegram_id'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_table('users')
    
    op.drop_index(op.f('ix_sources_name'), table_name='sources')
    op.drop_index(op.f('ix_sources_id'), table_name='sources')
    op.drop_table('sources')
    
    op.drop_index(op.f('ix_jobs_source_url'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_created_at'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_status'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_ai_score'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_raw_hash'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_job_type'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_source'), table_name='jobs')
    op.drop_index(op.f('ix_jobs_id'), table_name='jobs')
    op.drop_table('jobs')
