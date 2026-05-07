"""
Knowledge Base Models

External data sources for grounding RAG optimization.
Prevents hallucination by providing verified data.

Author: CV Optimizer Team
Version: 1.0.0
"""

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.session import Base


class ATSKeyword(Base):
    """
    ATS (Applicant Tracking System) keywords database.
    
    Verified keywords that ATS systems scan for.
    Prevents inventing keywords that don't exist.
    """
    __tablename__ = "ats_keywords"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Keyword details
    keyword = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)  # technical, soft_skill, certification, etc.
    job_family = Column(String(100), nullable=False, index=True)  # engineering, marketing, finance, etc.
    
    # Metadata
    frequency_score = Column(Float, default=0.0)  # How often it appears in job postings
    importance_score = Column(Float, default=0.0)  # How critical it is (0-1)
    synonyms = Column(ARRAY(String), default=[])
    related_keywords = Column(ARRAY(String), default=[])
    
    # Context
    typical_context = Column(Text, nullable=True)  # Example usage
    ats_variations = Column(ARRAY(String), default=[])  # Different ways ATS might scan for it
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes for fast lookup
    __table_args__ = (
        Index('idx_keyword_category', 'keyword', 'category'),
        Index('idx_job_family_category', 'job_family', 'category'),
    )


class IndustrySkill(Base):
    """
    Industry-verified skills database.
    
    Real skills with demand data, not invented ones.
    """
    __tablename__ = "industry_skills"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Skill details
    skill_name = Column(String(255), nullable=False, unique=True, index=True)
    skill_category = Column(String(100), nullable=False, index=True)  # programming, design, management, etc.
    industry = Column(String(100), nullable=False, index=True)
    
    # Demand metrics
    demand_score = Column(Float, default=0.0)  # Market demand (0-1)
    growth_rate = Column(Float, default=0.0)  # Year-over-year growth
    job_postings_count = Column(Integer, default=0)  # Number of postings requiring this skill
    
    # Proficiency levels
    typical_proficiency_levels = Column(ARRAY(String), default=['beginner', 'intermediate', 'advanced', 'expert'])
    
    # Related data
    related_skills = Column(ARRAY(String), default=[])
    common_tools = Column(ARRAY(String), default=[])
    certifications = Column(ARRAY(String), default=[])
    
    # Salary impact
    avg_salary_impact = Column(Float, nullable=True)  # Average salary increase for having this skill
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class JobTitleData(Base):
    """
    Job title reference data.
    
    Standardized job titles with associated data.
    """
    __tablename__ = "job_title_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Title details
    title = Column(String(255), nullable=False, index=True)
    normalized_title = Column(String(255), nullable=False, index=True)  # Standardized version
    seniority_level = Column(String(50), nullable=False, index=True)  # entry, mid, senior, lead, executive
    job_family = Column(String(100), nullable=False, index=True)
    
    # Required skills
    required_skills = Column(ARRAY(String), default=[])
    preferred_skills = Column(ARRAY(String), default=[])
    
    # Typical responsibilities
    common_responsibilities = Column(ARRAY(Text), default=[])
    
    # Salary data
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    salary_median = Column(Integer, nullable=True)
    salary_currency = Column(String(10), default='USD')
    
    # Experience requirements
    min_years_experience = Column(Integer, nullable=True)
    max_years_experience = Column(Integer, nullable=True)
    
    # Education requirements
    typical_education = Column(ARRAY(String), default=[])
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class ActionVerb(Base):
    """
    Verified action verbs for resume writing.
    
    Strong, ATS-friendly action verbs categorized by impact.
    """
    __tablename__ = "action_verbs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Verb details
    verb = Column(String(100), nullable=False, unique=True, index=True)
    category = Column(String(100), nullable=False, index=True)  # leadership, technical, creative, analytical, etc.
    
    # Impact metrics
    impact_level = Column(String(50), nullable=False)  # high, medium, low
    ats_score = Column(Float, default=0.0)  # How well ATS systems respond to it
    
    # Usage context
    best_for_roles = Column(ARRAY(String), default=[])
    example_usage = Column(Text, nullable=True)
    
    # Alternatives
    synonyms = Column(ARRAY(String), default=[])
    stronger_alternatives = Column(ARRAY(String), default=[])
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class IndustryMetric(Base):
    """
    Industry-standard metrics and KPIs.
    
    Real metrics used in different industries/roles.
    """
    __tablename__ = "industry_metrics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Metric details
    metric_name = Column(String(255), nullable=False, index=True)
    metric_type = Column(String(100), nullable=False, index=True)  # percentage, dollar, count, ratio, etc.
    industry = Column(String(100), nullable=False, index=True)
    job_family = Column(String(100), nullable=False, index=True)
    
    # Typical ranges
    typical_min = Column(Float, nullable=True)
    typical_max = Column(Float, nullable=True)
    exceptional_threshold = Column(Float, nullable=True)  # What's considered exceptional
    
    # Context
    description = Column(Text, nullable=True)
    example_usage = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class CompanyData(Base):
    """
    Verified company information.
    
    Prevents hallucination of company names/details.
    """
    __tablename__ = "company_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Company details
    company_name = Column(String(255), nullable=False, index=True)
    normalized_name = Column(String(255), nullable=False, index=True)
    industry = Column(String(100), nullable=False, index=True)
    company_size = Column(String(50), nullable=True)  # startup, small, medium, large, enterprise
    
    # Verification
    is_verified = Column(Boolean, default=False)
    verification_source = Column(String(255), nullable=True)
    
    # Common variations
    name_variations = Column(ARRAY(String), default=[])
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class CertificationData(Base):
    """
    Verified professional certifications.
    
    Real certifications with issuing organizations.
    """
    __tablename__ = "certification_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Certification details
    certification_name = Column(String(255), nullable=False, index=True)
    abbreviation = Column(String(50), nullable=True, index=True)
    issuing_organization = Column(String(255), nullable=False)
    
    # Relevance
    industry = Column(String(100), nullable=False, index=True)
    job_families = Column(ARRAY(String), default=[])
    
    # Value metrics
    demand_score = Column(Float, default=0.0)
    salary_impact = Column(Float, nullable=True)
    
    # Requirements
    prerequisites = Column(ARRAY(String), default=[])
    typical_cost = Column(Integer, nullable=True)
    validity_period = Column(String(50), nullable=True)  # e.g., "3 years", "lifetime"
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class EducationData(Base):
    """
    Verified educational institutions and degrees.
    
    Prevents hallucination of degrees/universities.
    """
    __tablename__ = "education_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Institution details
    institution_name = Column(String(255), nullable=False, index=True)
    institution_type = Column(String(100), nullable=False)  # university, college, bootcamp, online
    country = Column(String(100), nullable=False, index=True)
    
    # Degree details
    degree_type = Column(String(100), nullable=True, index=True)  # bachelor, master, phd, certificate
    field_of_study = Column(String(255), nullable=True, index=True)
    
    # Verification
    is_accredited = Column(Boolean, default=True)
    accreditation_body = Column(String(255), nullable=True)
    
    # Common variations
    name_variations = Column(ARRAY(String), default=[])
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
