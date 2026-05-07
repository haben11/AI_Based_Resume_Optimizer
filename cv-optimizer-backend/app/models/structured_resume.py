"""
Structured Resume Models

Granular resume data models for dynamic editing and AI optimization.
Supports CRUD operations at every level: resume → section → bullet → sentence.

Author: CV Optimizer Team
Version: 1.0.0
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from app.db.session import Base


class SectionType(str, enum.Enum):
    """Resume section types."""
    HEADER = "header"
    SUMMARY = "summary"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    SKILLS = "skills"
    PROJECTS = "projects"
    CERTIFICATIONS = "certifications"
    ACHIEVEMENTS = "achievements"
    CUSTOM = "custom"


class OptimizationLevel(str, enum.Enum):
    """Granularity level for AI optimization."""
    FULL_RESUME = "full_resume"
    SECTION = "section"
    BULLET = "bullet"
    SENTENCE = "sentence"
    SELECTION = "selection"


class StructuredResume(Base):
    """
    Structured resume with full editing capabilities.
    
    This is the editable version of a resume, allowing granular CRUD operations.
    """
    __tablename__ = "structured_resumes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    original_resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=True)
    
    # Metadata
    title = Column(String(255), nullable=False, default="My Resume")
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="structured_resumes")
    sections = relationship(
        "ResumeSection",
        back_populates="resume",
        cascade="all, delete-orphan",
        order_by="ResumeSection.order_index"
    )
    optimization_requests = relationship(
        "OptimizationRequest",
        back_populates="resume",
        cascade="all, delete-orphan"
    )
    versions = relationship(
        "ResumeVersion",
        back_populates="resume",
        cascade="all, delete-orphan"
    )


class ResumeSection(Base):
    """
    Resume section (e.g., Experience, Education, Skills).
    
    Supports nested structure and ordering.
    """
    __tablename__ = "resume_sections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("structured_resumes.id"), nullable=False)
    
    # Section details
    section_type = Column(SQLEnum(SectionType), nullable=False)
    title = Column(String(255), nullable=False)
    subtitle = Column(String(255), nullable=True)  # e.g., Company name, School name
    date_range = Column(String(100), nullable=True)  # e.g., "2020 - Present"
    location = Column(String(255), nullable=True)
    
    # Content
    description = Column(Text, nullable=True)  # Free-form text for summary sections
    
    # Ordering and visibility
    order_index = Column(Integer, nullable=False, default=0)
    is_visible = Column(Boolean, default=True)
    
    # AI metadata
    ai_generated = Column(Boolean, default=False)
    ai_confidence = Column(Integer, nullable=True)  # 0-100
    optimization_suggestions = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    resume = relationship("StructuredResume", back_populates="sections")
    bullets = relationship(
        "BulletPoint",
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="BulletPoint.order_index"
    )


class BulletPoint(Base):
    """
    Individual bullet point within a section.
    
    Represents a single achievement, responsibility, or skill.
    """
    __tablename__ = "bullet_points"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    section_id = Column(UUID(as_uuid=True), ForeignKey("resume_sections.id"), nullable=False)
    
    # Content
    content = Column(Text, nullable=False)
    
    # Ordering and visibility
    order_index = Column(Integer, nullable=False, default=0)
    is_visible = Column(Boolean, default=True)
    
    # AI metadata
    ai_generated = Column(Boolean, default=False)
    ai_confidence = Column(Integer, nullable=True)  # 0-100
    has_metrics = Column(Boolean, default=False)
    has_action_verb = Column(Boolean, default=False)
    optimization_suggestions = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    section = relationship("ResumeSection", back_populates="bullets")


class OptimizationRequest(Base):
    """
    Track AI optimization requests at any granularity level.
    
    Allows users to request optimization for entire resume, sections, or bullets.
    """
    __tablename__ = "optimization_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("structured_resumes.id"), nullable=False)
    
    # Request details
    level = Column(SQLEnum(OptimizationLevel), nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=True)  # ID of section/bullet being optimized
    
    # Input
    original_content = Column(Text, nullable=False)
    job_description = Column(Text, nullable=True)
    user_instructions = Column(Text, nullable=True)  # Custom instructions from user
    
    # Output
    optimized_content = Column(Text, nullable=True)
    suggestions = Column(JSONB, nullable=True)  # Array of suggestion objects
    
    # Metadata
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    quality_score = Column(Integer, nullable=True)  # 0-100
    applied = Column(Boolean, default=False)  # Whether user applied the optimization
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    resume = relationship("StructuredResume", back_populates="optimization_requests")


class ResumeVersion(Base):
    """
    Version control for resume changes.
    
    Allows users to track changes and rollback if needed.
    """
    __tablename__ = "resume_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("structured_resumes.id"), nullable=False)
    
    # Version details
    version_number = Column(Integer, nullable=False)
    snapshot = Column(JSONB, nullable=False)  # Complete resume state
    change_summary = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    resume = relationship("StructuredResume", back_populates="versions")


class AISuggestion(Base):
    """
    AI-generated suggestions for improvements.
    
    Real-time suggestions as user edits their resume.
    """
    __tablename__ = "ai_suggestions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Target
    target_type = Column(String(50), nullable=False)  # section, bullet, sentence
    target_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Suggestion details
    suggestion_type = Column(String(50), nullable=False)  # improve, add_metric, rephrase, etc.
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    suggested_content = Column(Text, nullable=True)
    
    # Metadata
    priority = Column(Integer, default=50)  # 0-100, higher = more important
    dismissed = Column(Boolean, default=False)
    applied = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
