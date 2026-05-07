"""
CRUD Operations for Structured Resumes

Repository pattern for structured resume operations.

Author: CV Optimizer Team
Version: 1.0.0
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_
from app.models.structured_resume import (
    StructuredResume,
    ResumeSection,
    BulletPoint,
    OptimizationRequest,
    ResumeVersion,
    AISuggestion
)
from app.schemas.structured_resume import (
    StructuredResumeCreate,
    StructuredResumeUpdate,
    ResumeSectionCreate,
    ResumeSectionUpdate,
    BulletPointCreate,
    BulletPointUpdate
)


class StructuredResumeRepository:
    """Repository for structured resume operations."""
    
    # ========================================================================
    # Structured Resume CRUD
    # ========================================================================
    
    def create(
        self,
        db: Session,
        user_id: UUID,
        obj_in: StructuredResumeCreate
    ) -> StructuredResume:
        """Create structured resume."""
        db_resume = StructuredResume(
            user_id=user_id,
            title=obj_in.title,
            original_resume_id=obj_in.original_resume_id
        )
        db.add(db_resume)
        db.flush()  # Get ID without committing
        
        # Create sections if provided
        for idx, section_in in enumerate(obj_in.sections or []):
            section_in.order_index = idx
            self.create_section(db, db_resume.id, section_in)
        
        db.commit()
        db.refresh(db_resume)
        return db_resume
    
    def get(self, db: Session, resume_id: UUID) -> Optional[StructuredResume]:
        """Get structured resume by ID."""
        return db.query(StructuredResume).options(
            joinedload(StructuredResume.sections).joinedload(ResumeSection.bullets)
        ).filter(StructuredResume.id == resume_id).first()
    
    def get_by_user(
        self,
        db: Session,
        user_id: UUID,
        active_only: bool = True
    ) -> List[StructuredResume]:
        """Get all structured resumes for user."""
        query = db.query(StructuredResume).filter(
            StructuredResume.user_id == user_id
        )
        
        if active_only:
            query = query.filter(StructuredResume.is_active == True)
        
        return query.order_by(StructuredResume.updated_at.desc()).all()
    
    def update(
        self,
        db: Session,
        resume_id: UUID,
        obj_in: StructuredResumeUpdate
    ) -> Optional[StructuredResume]:
        """Update structured resume."""
        db_resume = self.get(db, resume_id)
        if not db_resume:
            return None
        
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_resume, field, value)
        
        db_resume.version += 1
        db.commit()
        db.refresh(db_resume)
        return db_resume
    
    def delete(self, db: Session, resume_id: UUID) -> bool:
        """Delete structured resume."""
        db_resume = self.get(db, resume_id)
        if not db_resume:
            return False
        
        db.delete(db_resume)
        db.commit()
        return True
    
    # ========================================================================
    # Section CRUD
    # ========================================================================
    
    def create_section(
        self,
        db: Session,
        resume_id: UUID,
        obj_in: ResumeSectionCreate
    ) -> ResumeSection:
        """Create resume section."""
        db_section = ResumeSection(
            resume_id=resume_id,
            section_type=obj_in.section_type,
            title=obj_in.title,
            subtitle=obj_in.subtitle,
            date_range=obj_in.date_range,
            location=obj_in.location,
            description=obj_in.description,
            order_index=obj_in.order_index,
            is_visible=obj_in.is_visible
        )
        db.add(db_section)
        db.flush()
        
        # Create bullets if provided
        for idx, bullet_in in enumerate(obj_in.bullets or []):
            bullet_in.order_index = idx
            self.create_bullet(db, db_section.id, bullet_in)
        
        db.commit()
        db.refresh(db_section)
        return db_section
    
    def get_section(self, db: Session, section_id: UUID) -> Optional[ResumeSection]:
        """Get section by ID."""
        return db.query(ResumeSection).options(
            joinedload(ResumeSection.bullets)
        ).filter(ResumeSection.id == section_id).first()
    
    def update_section(
        self,
        db: Session,
        section_id: UUID,
        obj_in: ResumeSectionUpdate
    ) -> Optional[ResumeSection]:
        """Update section."""
        db_section = self.get_section(db, section_id)
        if not db_section:
            return None
        
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_section, field, value)
        
        db.commit()
        db.refresh(db_section)
        return db_section
    
    def delete_section(self, db: Session, section_id: UUID) -> bool:
        """Delete section."""
        db_section = self.get_section(db, section_id)
        if not db_section:
            return False
        
        db.delete(db_section)
        db.commit()
        return True
    
    def reorder_sections(
        self,
        db: Session,
        resume_id: UUID,
        section_orders: List[Dict[str, Any]]
    ) -> bool:
        """Reorder sections."""
        for item in section_orders:
            section_id = item['id']
            order_index = item['order_index']
            
            db_section = self.get_section(db, section_id)
            if db_section and db_section.resume_id == resume_id:
                db_section.order_index = order_index
        
        db.commit()
        return True
    
    # ========================================================================
    # Bullet Point CRUD
    # ========================================================================
    
    def create_bullet(
        self,
        db: Session,
        section_id: UUID,
        obj_in: BulletPointCreate
    ) -> BulletPoint:
        """Create bullet point."""
        db_bullet = BulletPoint(
            section_id=section_id,
            content=obj_in.content,
            order_index=obj_in.order_index,
            is_visible=obj_in.is_visible
        )
        db.add(db_bullet)
        db.commit()
        db.refresh(db_bullet)
        return db_bullet
    
    def get_bullet(self, db: Session, bullet_id: UUID) -> Optional[BulletPoint]:
        """Get bullet by ID."""
        return db.query(BulletPoint).filter(BulletPoint.id == bullet_id).first()
    
    def update_bullet(
        self,
        db: Session,
        bullet_id: UUID,
        obj_in: BulletPointUpdate
    ) -> Optional[BulletPoint]:
        """Update bullet."""
        db_bullet = self.get_bullet(db, bullet_id)
        if not db_bullet:
            return None
        
        update_data = obj_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_bullet, field, value)
        
        db.commit()
        db.refresh(db_bullet)
        return db_bullet
    
    def delete_bullet(self, db: Session, bullet_id: UUID) -> bool:
        """Delete bullet."""
        db_bullet = self.get_bullet(db, bullet_id)
        if not db_bullet:
            return False
        
        db.delete(db_bullet)
        db.commit()
        return True
    
    def reorder_bullets(
        self,
        db: Session,
        section_id: UUID,
        bullet_orders: List[Dict[str, Any]]
    ) -> bool:
        """Reorder bullets."""
        for item in bullet_orders:
            bullet_id = item['id']
            order_index = item['order_index']
            
            db_bullet = self.get_bullet(db, bullet_id)
            if db_bullet and db_bullet.section_id == section_id:
                db_bullet.order_index = order_index
        
        db.commit()
        return True
    
    # ========================================================================
    # Optimization Requests
    # ========================================================================
    
    def create_optimization_request(
        self,
        db: Session,
        resume_id: UUID,
        level: str,
        original_content: str,
        target_id: Optional[UUID] = None,
        job_description: Optional[str] = None,
        user_instructions: Optional[str] = None
    ) -> OptimizationRequest:
        """Create optimization request."""
        db_request = OptimizationRequest(
            resume_id=resume_id,
            level=level,
            target_id=target_id,
            original_content=original_content,
            job_description=job_description,
            user_instructions=user_instructions,
            status="pending"
        )
        db.add(db_request)
        db.commit()
        db.refresh(db_request)
        return db_request
    
    def update_optimization_request(
        self,
        db: Session,
        request_id: UUID,
        optimized_content: Optional[str] = None,
        suggestions: Optional[List[Dict]] = None,
        status: Optional[str] = None,
        quality_score: Optional[int] = None
    ) -> Optional[OptimizationRequest]:
        """Update optimization request."""
        db_request = db.query(OptimizationRequest).filter(
            OptimizationRequest.id == request_id
        ).first()
        
        if not db_request:
            return None
        
        if optimized_content is not None:
            db_request.optimized_content = optimized_content
        if suggestions is not None:
            db_request.suggestions = suggestions
        if status is not None:
            db_request.status = status
        if quality_score is not None:
            db_request.quality_score = quality_score
        
        if status == "completed":
            from datetime import datetime
            db_request.completed_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_request)
        return db_request
    
    def get_optimization_request(
        self,
        db: Session,
        request_id: UUID
    ) -> Optional[OptimizationRequest]:
        """Get optimization request."""
        return db.query(OptimizationRequest).filter(
            OptimizationRequest.id == request_id
        ).first()
    
    # ========================================================================
    # Version Control
    # ========================================================================
    
    def create_version(
        self,
        db: Session,
        resume_id: UUID,
        snapshot: Dict[str, Any],
        change_summary: Optional[str] = None
    ) -> ResumeVersion:
        """Create version snapshot."""
        # Get current version number
        latest_version = db.query(ResumeVersion).filter(
            ResumeVersion.resume_id == resume_id
        ).order_by(ResumeVersion.version_number.desc()).first()
        
        version_number = (latest_version.version_number + 1) if latest_version else 1
        
        db_version = ResumeVersion(
            resume_id=resume_id,
            version_number=version_number,
            snapshot=snapshot,
            change_summary=change_summary
        )
        db.add(db_version)
        db.commit()
        db.refresh(db_version)
        return db_version
    
    def get_versions(
        self,
        db: Session,
        resume_id: UUID
    ) -> List[ResumeVersion]:
        """Get all versions for resume."""
        return db.query(ResumeVersion).filter(
            ResumeVersion.resume_id == resume_id
        ).order_by(ResumeVersion.version_number.desc()).all()
    
    # ========================================================================
    # AI Suggestions
    # ========================================================================
    
    def create_suggestion(
        self,
        db: Session,
        user_id: UUID,
        target_type: str,
        target_id: UUID,
        suggestion_type: str,
        title: str,
        description: str,
        suggested_content: Optional[str] = None,
        priority: int = 50
    ) -> AISuggestion:
        """Create AI suggestion."""
        db_suggestion = AISuggestion(
            user_id=user_id,
            target_type=target_type,
            target_id=target_id,
            suggestion_type=suggestion_type,
            title=title,
            description=description,
            suggested_content=suggested_content,
            priority=priority
        )
        db.add(db_suggestion)
        db.commit()
        db.refresh(db_suggestion)
        return db_suggestion
    
    def get_suggestions(
        self,
        db: Session,
        user_id: UUID,
        target_id: Optional[UUID] = None,
        dismissed: bool = False
    ) -> List[AISuggestion]:
        """Get AI suggestions."""
        query = db.query(AISuggestion).filter(
            AISuggestion.user_id == user_id,
            AISuggestion.dismissed == dismissed
        )
        
        if target_id:
            query = query.filter(AISuggestion.target_id == target_id)
        
        return query.order_by(AISuggestion.priority.desc()).all()
    
    def dismiss_suggestion(
        self,
        db: Session,
        suggestion_id: UUID
    ) -> bool:
        """Dismiss suggestion."""
        db_suggestion = db.query(AISuggestion).filter(
            AISuggestion.id == suggestion_id
        ).first()
        
        if not db_suggestion:
            return False
        
        db_suggestion.dismissed = True
        db.commit()
        return True


# Singleton instance
structured_resume_repo = StructuredResumeRepository()
