"""add_semantic_cache_tables

Revision ID: 65a2cfd668da
Revises: bf911df9e096
Create Date: 2026-05-04 11:22:59.066254

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY


# revision identifiers, used by Alembic.
revision: str = '65a2cfd668da'
down_revision: Union[str, None] = 'bf911df9e096'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Semantic Cache Entries table
    op.create_table(
        'semantic_cache_entries',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('query_text', sa.Text, nullable=False),
        sa.Column('query_hash', sa.String(64), nullable=False, index=True),
        sa.Column('query_embedding', ARRAY(sa.Float), nullable=False),
        sa.Column('resume_id', UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('job_title', sa.String(255), nullable=True, index=True),
        sa.Column('industry', sa.String(100), nullable=True, index=True),
        sa.Column('context_hash', sa.String(64), nullable=True, index=True),
        sa.Column('response_text', sa.Text, nullable=False),
        sa.Column('response_metadata', JSONB, nullable=True),
        sa.Column('hit_count', sa.Integer, default=0),
        sa.Column('last_hit_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('quality_score', sa.Float, nullable=True),
        sa.Column('similarity_threshold', sa.Float, default=0.85),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('ttl_hours', sa.Integer, default=168),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Indexes
    op.create_index('idx_cache_job_title_industry', 'semantic_cache_entries', ['job_title', 'industry'])
    op.create_index('idx_cache_expires_at', 'semantic_cache_entries', ['expires_at'])
    op.create_index('idx_cache_active', 'semantic_cache_entries', ['is_active'])
    
    # Cache Statistics table
    op.create_table(
        'cache_statistics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('period_type', sa.String(20), nullable=False),
        sa.Column('total_queries', sa.Integer, default=0),
        sa.Column('cache_hits', sa.Integer, default=0),
        sa.Column('cache_misses', sa.Integer, default=0),
        sa.Column('exact_matches', sa.Integer, default=0),
        sa.Column('semantic_matches', sa.Integer, default=0),
        sa.Column('avg_similarity_score', sa.Float, nullable=True),
        sa.Column('avg_response_time_ms', sa.Float, nullable=True),
        sa.Column('total_cost_saved', sa.Float, default=0.0),
        sa.Column('total_time_saved_ms', sa.Float, default=0.0),
        sa.Column('top_job_titles', JSONB, nullable=True),
        sa.Column('top_industries', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    op.create_index('idx_stats_date_period', 'cache_statistics', ['date', 'period_type'])


def downgrade() -> None:
    op.drop_index('idx_stats_date_period', 'cache_statistics')
    op.drop_table('cache_statistics')
    
    op.drop_index('idx_cache_active', 'semantic_cache_entries')
    op.drop_index('idx_cache_expires_at', 'semantic_cache_entries')
    op.drop_index('idx_cache_job_title_industry', 'semantic_cache_entries')
    op.drop_table('semantic_cache_entries')
