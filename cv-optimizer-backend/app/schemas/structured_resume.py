"""
Structured Resume Schemas

Pydantic models for API requests and responses.

Author: CV Optimizer Team
Version: 1.0.0
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from enum import Enum


class SectionType(str, Enum):
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


class OptimizationLevel(str, Enum):
    """Optimization granularity."""
    FULL_RESUME = "full_resume"
    SECTION = "section"
    BULLET = "bullet"
    SENTENCE = "sentence"
    SELECTION = "selection"


class SuggestionType(str, Enum):
    """Types of AI suggestions."""
    ADD_METRIC = "add_metric"
    ADD_ACTION_VERB = "add_action_verb"
    IMPROVE_CLARITY = "improve_clarity"
    ADD_KEYWORDS = "add_keywords"
    REPHRASE = "rephrase"
    EXPAND = "expand"
    CONDENSE = "condense"
    FIX_GRAMMAR = "fix_grammar"


# ============================================================================
# Bullet Point Schemas
# ============================================================================

class BulletPointBase(BaseModel):
    """Base bullet point schema."""
    content: str = Field(..., min_length=10, max_length=500)
    order_index: int = Field(default=0, ge=0)
    is_visible: bool = True


class BulletPointCreate(BulletPointBase):
    """Create bullet point."""
    pass


class BulletPointUpdate(BaseModel):
    """Update bullet point."""
    content: Optional[str] = Field(None, min_length=10, max_length=500)
    order_index: Optional[int] = Field(None, ge=0)
    is_visible: Optional[bool] = None


class BulletPointResponse(BulletPointBase):
    """Bullet point response."""
    id: UUID
    section_id: UUID
    ai_generated: bool
    ai_confidence: Optional[int]
    has_metrics: bool
    has_action_verb: bool
    optimization_suggestions: Optional[List[Dict[str, Any]]]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============================================================================
# Section Schemas
# ============================================================================

class ResumeSectionBase(BaseModel):
    """Base section schema."""
    section_type: SectionType
    title: str = Field(..., min_length=1, max_length=255)
    subtitle: Optional[str] = Field(None, max_length=255)
    date_range: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    order_index: int = Field(default=0, ge=0)
    is_visible: bool = True


class ResumeSectionCreate(ResumeSectionBase):
    """Create section."""
    bullets: Optional[List[BulletPointCreate]] = []


class ResumeSectionUpdate(BaseModel):
    """Update section."""
    section_type: Optional[SectionType] = None
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    subtitle: Optional[str] = Field(None, max_length=255)
    date_range: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    order_index: Optional[int] = Field(None, ge=0)
    is_visible: Optional[bool] = None


class ResumeSectionResponse(ResumeSectionBase):
    """Section response."""
    id: UUID
    resume_id: UUID
    ai_generated: bool
    ai_confidence: Optional[int]
    optimization_suggestions: Optional[List[Dict[str, Any]]]
    bullets: List[BulletPointResponse]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============================================================================
# Structured Resume Schemas
# ============================================================================

class StructuredResumeBase(BaseModel):
    """Base structured resume schema."""
    title: str = Field(default="My Resume", max_length=255)


class StructuredResumeCreate(StructuredResumeBase):
    """Create structured resume."""
    original_resume_id: Optional[UUID] = None
    sections: Optional[List[ResumeSectionCreate]] = []


class StructuredResumeUpdate(BaseModel):
    """Update structured resume."""
    title: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class StructuredResumeResponse(StructuredResumeBase):
    """Structured resume response."""
    id: UUID
    user_id: UUID
    original_resume_id: Optional[UUID]
    version: int
    is_active: bool
    sections: List[ResumeSectionResponse]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============================================================================
# Optimization Request Schemas
# ============================================================================

class OptimizationRequestCreate(BaseModel):
    """Request AI optimization."""
    level: OptimizationLevel
    target_id: Optional[UUID] = None  # Section or bullet ID
    job_description: Optional[str] = None
    user_instructions: Optional[str] = Field(None, max_length=1000)
    
    @validator('target_id')
    def validate_target_id(cls, v, values):
        """Validate target_id is provided for granular optimizations."""
        level = values.get('level')
        if level in [OptimizationLevel.SECTION, OptimizationLevel.BULLET] and not v:
            raise ValueError(f"target_id required for {level} optimization")
        return v


class OptimizationSuggestion(BaseModel):
    """Single optimization suggestion."""
    type: SuggestionType
    title: str
    description: str
    suggested_content: Optional[str] = None
    priority: int = Field(default=50, ge=0, le=100)
    reasoning: Optional[str] = None


class OptimizationRequestResponse(BaseModel):
    """Optimization request response."""
    id: UUID
    resume_id: UUID
    level: OptimizationLevel
    target_id: Optional[UUID]
    original_content: str
    optimized_content: Optional[str]
    suggestions: Optional[List[OptimizationSuggestion]]
    status: str
    quality_score: Optional[int]
    applied: bool
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


# ============================================================================
# AI Suggestion Schemas
# ============================================================================

class AISuggestionResponse(BaseModel):
    """AI suggestion response."""
    id: UUID
    target_type: str
    target_id: UUID
    suggestion_type: str
    title: str
    description: str
    suggested_content: Optional[str]
    priority: int
    dismissed: bool
    applied: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# Bulk Operations
# ============================================================================

class BulkReorderRequest(BaseModel):
    """Reorder sections or bullets."""
    items: List[Dict[str, Any]] = Field(..., description="Array of {id, order_index}")
    
    @validator('items')
    def validate_items(cls, v):
        """Validate items have required fields."""
        for item in v:
            if 'id' not in item or 'order_index' not in item:
                raise ValueError("Each item must have 'id' and 'order_index'")
        return v


class BulkDeleteRequest(BaseModel):
    """Delete multiple items."""
    ids: List[UUID] = Field(..., min_items=1)


class ApplyOptimizationRequest(BaseModel):
    """Apply optimization to target."""
    optimization_id: UUID
    apply_all_suggestions: bool = False
    selected_suggestions: Optional[List[int]] = None  # Indices of suggestions to apply


# ============================================================================
# Version Control
# ============================================================================

class ResumeVersionResponse(BaseModel):
    """Resume version response."""
    id: UUID
    resume_id: UUID
    version_number: int
    snapshot: Dict[str, Any]
    change_summary: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class CreateVersionRequest(BaseModel):
    """Create version snapshot."""
    change_summary: Optional[str] = Field(None, max_length=500)


class RestoreVersionRequest(BaseModel):
    """Restore from version."""
    version_id: UUID


# ============================================================================
# Real-time Suggestions
# ============================================================================

class GetSuggestionsRequest(BaseModel):
    """Request suggestions for content."""
    target_type: str = Field(..., pattern="^(section|bullet|sentence)$")
    target_id: UUID
    job_description: Optional[str] = None


class DismissSuggestionRequest(BaseModel):
    """Dismiss a suggestion."""
    suggestion_id: UUID


# ============================================================================
# Export
# ============================================================================

class ExportFormat(str, Enum):
    """Export formats."""
    JSON = "json"
    MARKDOWN = "markdown"
    PDF = "pdf"
    DOCX = "docx"


class ExportRequest(BaseModel):
    """Export resume."""
    format: ExportFormat
    template_id: Optional[str] = "modern-1-blue"
    include_hidden: bool = False
