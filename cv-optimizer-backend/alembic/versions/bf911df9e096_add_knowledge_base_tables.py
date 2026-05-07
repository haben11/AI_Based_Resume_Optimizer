"""add_knowledge_base_tables

Revision ID: bf911df9e096
Revises: f01719fb1ea3
Create Date: 2026-05-04 10:48:50.223292

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY


# revision identifiers, used by Alembic.
revision: str = 'bf911df9e096'
down_revision: Union[str, None] = 'f01719fb1ea3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ATS Keywords table
    op.create_table(
        'ats_keywords',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('keyword', sa.String(255), nullable=False, index=True),
        sa.Column('category', sa.String(100), nullable=False, index=True),
        sa.Column('job_family', sa.String(100), nullable=False, index=True),
        sa.Column('frequency_score', sa.Float, default=0.0),
        sa.Column('importance_score', sa.Float, default=0.0),
        sa.Column('synonyms', ARRAY(sa.String), default=[]),
        sa.Column('related_keywords', ARRAY(sa.String), default=[]),
        sa.Column('typical_context', sa.Text, nullable=True),
        sa.Column('ats_variations', ARRAY(sa.String), default=[]),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index('idx_keyword_category', 'ats_keywords', ['keyword', 'category'])
    op.create_index('idx_job_family_category', 'ats_keywords', ['job_family', 'category'])
    
    # Industry Skills table
    op.create_table(
        'industry_skills',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('skill_name', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('skill_category', sa.String(100), nullable=False, index=True),
        sa.Column('industry', sa.String(100), nullable=False, index=True),
        sa.Column('demand_score', sa.Float, default=0.0),
        sa.Column('growth_rate', sa.Float, default=0.0),
        sa.Column('job_postings_count', sa.Integer, default=0),
        sa.Column('typical_proficiency_levels', ARRAY(sa.String), default=['beginner', 'intermediate', 'advanced', 'expert']),
        sa.Column('related_skills', ARRAY(sa.String), default=[]),
        sa.Column('common_tools', ARRAY(sa.String), default=[]),
        sa.Column('certifications', ARRAY(sa.String), default=[]),
        sa.Column('avg_salary_impact', sa.Float, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Job Title Data table
    op.create_table(
        'job_title_data',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False, index=True),
        sa.Column('normalized_title', sa.String(255), nullable=False, index=True),
        sa.Column('seniority_level', sa.String(50), nullable=False, index=True),
        sa.Column('job_family', sa.String(100), nullable=False, index=True),
        sa.Column('required_skills', ARRAY(sa.String), default=[]),
        sa.Column('preferred_skills', ARRAY(sa.String), default=[]),
        sa.Column('common_responsibilities', ARRAY(sa.Text), default=[]),
        sa.Column('salary_min', sa.Integer, nullable=True),
        sa.Column('salary_max', sa.Integer, nullable=True),
        sa.Column('salary_median', sa.Integer, nullable=True),
        sa.Column('salary_currency', sa.String(10), default='USD'),
        sa.Column('min_years_experience', sa.Integer, nullable=True),
        sa.Column('max_years_experience', sa.Integer, nullable=True),
        sa.Column('typical_education', ARRAY(sa.String), default=[]),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Action Verbs table
    op.create_table(
        'action_verbs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('verb', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('category', sa.String(100), nullable=False, index=True),
        sa.Column('impact_level', sa.String(50), nullable=False),
        sa.Column('ats_score', sa.Float, default=0.0),
        sa.Column('best_for_roles', ARRAY(sa.String), default=[]),
        sa.Column('example_usage', sa.Text, nullable=True),
        sa.Column('synonyms', ARRAY(sa.String), default=[]),
        sa.Column('stronger_alternatives', ARRAY(sa.String), default=[]),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Industry Metrics table
    op.create_table(
        'industry_metrics',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('metric_name', sa.String(255), nullable=False, index=True),
        sa.Column('metric_type', sa.String(100), nullable=False, index=True),
        sa.Column('industry', sa.String(100), nullable=False, index=True),
        sa.Column('job_family', sa.String(100), nullable=False, index=True),
        sa.Column('typical_min', sa.Float, nullable=True),
        sa.Column('typical_max', sa.Float, nullable=True),
        sa.Column('exceptional_threshold', sa.Float, nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('example_usage', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Company Data table
    op.create_table(
        'company_data',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('company_name', sa.String(255), nullable=False, index=True),
        sa.Column('normalized_name', sa.String(255), nullable=False, index=True),
        sa.Column('industry', sa.String(100), nullable=False, index=True),
        sa.Column('company_size', sa.String(50), nullable=True),
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('verification_source', sa.String(255), nullable=True),
        sa.Column('name_variations', ARRAY(sa.String), default=[]),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Certification Data table
    op.create_table(
        'certification_data',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('certification_name', sa.String(255), nullable=False, index=True),
        sa.Column('abbreviation', sa.String(50), nullable=True, index=True),
        sa.Column('issuing_organization', sa.String(255), nullable=False),
        sa.Column('industry', sa.String(100), nullable=False, index=True),
        sa.Column('job_families', ARRAY(sa.String), default=[]),
        sa.Column('demand_score', sa.Float, default=0.0),
        sa.Column('salary_impact', sa.Float, nullable=True),
        sa.Column('prerequisites', ARRAY(sa.String), default=[]),
        sa.Column('typical_cost', sa.Integer, nullable=True),
        sa.Column('validity_period', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Education Data table
    op.create_table(
        'education_data',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('institution_name', sa.String(255), nullable=False, index=True),
        sa.Column('institution_type', sa.String(100), nullable=False),
        sa.Column('country', sa.String(100), nullable=False, index=True),
        sa.Column('degree_type', sa.String(100), nullable=True, index=True),
        sa.Column('field_of_study', sa.String(255), nullable=True, index=True),
        sa.Column('is_accredited', sa.Boolean, default=True),
        sa.Column('accreditation_body', sa.String(255), nullable=True),
        sa.Column('name_variations', ARRAY(sa.String), default=[]),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('education_data')
    op.drop_table('certification_data')
    op.drop_table('company_data')
    op.drop_table('industry_metrics')
    op.drop_table('action_verbs')
    op.drop_table('job_title_data')
    op.drop_table('industry_skills')
    op.drop_index('idx_job_family_category', 'ats_keywords')
    op.drop_index('idx_keyword_category', 'ats_keywords')
    op.drop_table('ats_keywords')
