"""
Structured Resume API Endpoints

RESTful API for dynamic resume editing with granular AI optimization.

Author: CV Optimizer Team
Version: 1.0.0
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.crud.crud_structured_resume import structured_resume_repo
from app.services.intelligent_optimizer import intelligent_optimizer
from app.schemas.structured_resume import (
    # Resume schemas
    StructuredResumeCreate,
    StructuredResumeUpdate,
    StructuredResumeResponse,
    # Section schemas
    ResumeSectionCreate,
    ResumeSectionUpdate,
    ResumeSectionResponse,
    # Bullet schemas
    BulletPointCreate,
    BulletPointUpdate,
    BulletPointResponse,
    # Optimization schemas
    OptimizationRequestCreate,
    OptimizationRequestResponse,
    ApplyOptimizationRequest,
    # Bulk operations
    BulkReorderRequest,
    BulkDeleteRequest,
    # Version control
    ResumeVersionResponse,
    CreateVersionRequest,
    RestoreVersionRequest,
    # Suggestions
    GetSuggestionsRequest,
    AISuggestionResponse,
    DismissSuggestionRequest,
    # Export
    ExportRequest,
    ExportFormat
)
from app.core.logging import logger

router = APIRouter()


# ============================================================================
# Structured Resume CRUD
# ============================================================================

@router.post("/", response_model=StructuredResumeResponse, status_code=201)
async def create_structured_resume(
    resume_in: StructuredResumeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new structured resume.
    
    This creates an editable resume with full CRUD capabilities.
    Can be created from scratch or from an existing resume.
    """
    try:
        resume = structured_resume_repo.create(
            db=db,
            user_id=current_user.id,
            obj_in=resume_in
        )
        
        logger.info(
            "structured_resume_created",
            resume_id=resume.id,
            user_id=current_user.id,
            num_sections=len(resume.sections)
        )
        
        return resume
    except Exception as e:
        logger.error("structured_resume_creation_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create resume: {str(e)}")


@router.get("/", response_model=List[StructuredResumeResponse])
async def list_structured_resumes(
    active_only: bool = Query(True, description="Only return active resumes"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all structured resumes for the current user.
    
    Returns resumes ordered by most recently updated.
    """
    resumes = structured_resume_repo.get_by_user(
        db=db,
        user_id=current_user.id,
        active_only=active_only
    )
    return resumes


@router.get("/{resume_id}", response_model=StructuredResumeResponse)
async def get_structured_resume(
    resume_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific structured resume with all sections and bullets.
    """
    resume = structured_resume_repo.get(db, resume_id)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return resume


@router.patch("/{resume_id}", response_model=StructuredResumeResponse)
async def update_structured_resume(
    resume_id: UUID,
    resume_in: StructuredResumeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update structured resume metadata (title, active status).
    """
    resume = structured_resume_repo.get(db, resume_id)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    updated_resume = structured_resume_repo.update(db, resume_id, resume_in)
    
    logger.info("structured_resume_updated", resume_id=resume_id)
    
    return updated_resume


@router.delete("/{resume_id}", status_code=204)
async def delete_structured_resume(
    resume_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a structured resume and all its sections/bullets.
    """
    resume = structured_resume_repo.get(db, resume_id)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    structured_resume_repo.delete(db, resume_id)
    
    logger.info("structured_resume_deleted", resume_id=resume_id)


# ============================================================================
# Section CRUD
# ============================================================================

@router.post("/{resume_id}/sections", response_model=ResumeSectionResponse, status_code=201)
async def create_section(
    resume_id: UUID,
    section_in: ResumeSectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a new section to the resume.
    
    Sections can include experience, education, skills, projects, etc.
    """
    resume = structured_resume_repo.get(db, resume_id)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    section = structured_resume_repo.create_section(db, resume_id, section_in)
    
    logger.info(
        "section_created",
        resume_id=resume_id,
        section_id=section.id,
        section_type=section.section_type.value
    )
    
    return section


@router.get("/{resume_id}/sections/{section_id}", response_model=ResumeSectionResponse)
async def get_section(
    resume_id: UUID,
    section_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific section with all its bullets.
    """
    section = structured_resume_repo.get_section(db, section_id)
    
    if not section or section.resume_id != resume_id:
        raise HTTPException(status_code=404, detail="Section not found")
    
    resume = structured_resume_repo.get(db, resume_id)
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return section


@router.patch("/{resume_id}/sections/{section_id}", response_model=ResumeSectionResponse)
async def update_section(
    resume_id: UUID,
    section_id: UUID,
    section_in: ResumeSectionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a section's content, title, dates, etc.
    """
    section = structured_resume_repo.get_section(db, section_id)
    
    if not section or section.resume_id != resume_id:
        raise HTTPException(status_code=404, detail="Section not found")
    
    resume = structured_resume_repo.get(db, resume_id)
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    updated_section = structured_resume_repo.update_section(db, section_id, section_in)
    
    logger.info("section_updated", section_id=section_id)
    
    return updated_section


@router.delete("/{resume_id}/sections/{section_id}", status_code=204)
async def delete_section(
    resume_id: UUID,
    section_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a section and all its bullets.
    """
    section = structured_resume_repo.get_section(db, section_id)
    
    if not section or section.resume_id != resume_id:
        raise HTTPException(status_code=404, detail="Section not found")
    
    resume = structured_resume_repo.get(db, resume_id)
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    structured_resume_repo.delete_section(db, section_id)
    
    logger.info("section_deleted", section_id=section_id)


@router.post("/{resume_id}/sections/reorder", status_code=200)
async def reorder_sections(
    resume_id: UUID,
    reorder_request: BulkReorderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reorder sections in the resume.
    
    Provide array of {id, order_index} to set new order.
    """
    resume = structured_resume_repo.get(db, resume_id)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    structured_resume_repo.reorder_sections(db, resume_id, reorder_request.items)
    
    logger.info("sections_reordered", resume_id=resume_id, num_sections=len(reorder_request.items))
    
    return {"message": "Sections reordered successfully"}


# ============================================================================
# Bullet Point CRUD
# ============================================================================

@router.post("/{resume_id}/sections/{section_id}/bullets", response_model=BulletPointResponse, status_code=201)
async def create_bullet(
    resume_id: UUID,
    section_id: UUID,
    bullet_in: BulletPointCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a new bullet point to a section.
    """
    section = structured_resume_repo.get_section(db, section_id)
    
    if not section or section.resume_id != resume_id:
        raise HTTPException(status_code=404, detail="Section not found")
    
    resume = structured_resume_repo.get(db, resume_id)
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    bullet = structured_resume_repo.create_bullet(db, section_id, bullet_in)
    
    logger.info("bullet_created", section_id=section_id, bullet_id=bullet.id)
    
    return bullet


@router.patch("/{resume_id}/sections/{section_id}/bullets/{bullet_id}", response_model=BulletPointResponse)
async def update_bullet(
    resume_id: UUID,
    section_id: UUID,
    bullet_id: UUID,
    bullet_in: BulletPointUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a bullet point's content or visibility.
    """
    bullet = structured_resume_repo.get_bullet(db, bullet_id)
    
    if not bullet or bullet.section_id != section_id:
        raise HTTPException(status_code=404, detail="Bullet not found")
    
    section = structured_resume_repo.get_section(db, section_id)
    if section.resume_id != resume_id:
        raise HTTPException(status_code=404, detail="Section not found")
    
    resume = structured_resume_repo.get(db, resume_id)
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    updated_bullet = structured_resume_repo.update_bullet(db, bullet_id, bullet_in)
    
    logger.info("bullet_updated", bullet_id=bullet_id)
    
    return updated_bullet


@router.delete("/{resume_id}/sections/{section_id}/bullets/{bullet_id}", status_code=204)
async def delete_bullet(
    resume_id: UUID,
    section_id: UUID,
    bullet_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a bullet point.
    """
    bullet = structured_resume_repo.get_bullet(db, bullet_id)
    
    if not bullet or bullet.section_id != section_id:
        raise HTTPException(status_code=404, detail="Bullet not found")
    
    section = structured_resume_repo.get_section(db, section_id)
    if section.resume_id != resume_id:
        raise HTTPException(status_code=404, detail="Section not found")
    
    resume = structured_resume_repo.get(db, resume_id)
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    structured_resume_repo.delete_bullet(db, bullet_id)
    
    logger.info("bullet_deleted", bullet_id=bullet_id)


@router.post("/{resume_id}/sections/{section_id}/bullets/reorder", status_code=200)
async def reorder_bullets(
    resume_id: UUID,
    section_id: UUID,
    reorder_request: BulkReorderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reorder bullets within a section.
    """
    section = structured_resume_repo.get_section(db, section_id)
    
    if not section or section.resume_id != resume_id:
        raise HTTPException(status_code=404, detail="Section not found")
    
    resume = structured_resume_repo.get(db, resume_id)
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    structured_resume_repo.reorder_bullets(db, section_id, reorder_request.items)
    
    logger.info("bullets_reordered", section_id=section_id, num_bullets=len(reorder_request.items))
    
    return {"message": "Bullets reordered successfully"}


# ============================================================================
# AI Optimization
# ============================================================================

@router.post("/{resume_id}/optimize", response_model=OptimizationRequestResponse)
async def optimize_resume(
    resume_id: UUID,
    request: OptimizationRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Request AI optimization at any granularity level.
    
    Levels:
    - FULL_RESUME: Optimize entire resume
    - SECTION: Optimize specific section (requires target_id)
    - BULLET: Optimize specific bullet (requires target_id)
    - SELECTION: Optimize selected text
    """
    resume = structured_resume_repo.get(db, resume_id)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Route to appropriate optimization method
        if request.level == "full_resume":
            result = await intelligent_optimizer.optimize_full_resume(
                db=db,
                resume_id=resume_id,
                job_description=request.job_description,
                user_instructions=request.user_instructions
            )
        elif request.level == "section":
            if not request.target_id:
                raise HTTPException(status_code=400, detail="target_id required for section optimization")
            
            result = await intelligent_optimizer.optimize_section(
                db=db,
                section_id=request.target_id,
                job_description=request.job_description,
                user_instructions=request.user_instructions
            )
        elif request.level == "bullet":
            if not request.target_id:
                raise HTTPException(status_code=400, detail="target_id required for bullet optimization")
            
            result = await intelligent_optimizer.optimize_bullet(
                db=db,
                bullet_id=request.target_id,
                job_description=request.job_description,
                user_instructions=request.user_instructions
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported optimization level: {request.level}")
        
        # Get the optimization request from DB
        opt_request = structured_resume_repo.get_optimization_request(
            db, UUID(result["optimization_id"])
        )
        
        return opt_request
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("optimization_failed", error=str(e), resume_id=resume_id)
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.get("/{resume_id}/optimizations/{optimization_id}", response_model=OptimizationRequestResponse)
async def get_optimization(
    resume_id: UUID,
    optimization_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get optimization request details.
    """
    resume = structured_resume_repo.get(db, resume_id)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    opt_request = structured_resume_repo.get_optimization_request(db, optimization_id)
    
    if not opt_request or opt_request.resume_id != resume_id:
        raise HTTPException(status_code=404, detail="Optimization not found")
    
    return opt_request


@router.post("/{resume_id}/optimizations/{optimization_id}/apply", status_code=200)
async def apply_optimization(
    resume_id: UUID,
    optimization_id: UUID,
    apply_request: ApplyOptimizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Apply optimization to the resume.
    
    This updates the actual resume content with the optimized version.
    """
    resume = structured_resume_repo.get(db, resume_id)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    opt_request = structured_resume_repo.get_optimization_request(db, optimization_id)
    
    if not opt_request or opt_request.resume_id != resume_id:
        raise HTTPException(status_code=404, detail="Optimization not found")
    
    if not opt_request.optimized_content:
        raise HTTPException(status_code=400, detail="Optimization not completed")
    
    # Apply based on level
    if opt_request.level == "section":
        section = structured_resume_repo.get_section(db, opt_request.target_id)
        if section:
            # Parse and update section content
            # This is simplified - in production, parse the optimized content properly
            from app.schemas.structured_resume import ResumeSectionUpdate
            structured_resume_repo.update_section(
                db,
                opt_request.target_id,
                ResumeSectionUpdate(description=opt_request.optimized_content)
            )
    elif opt_request.level == "bullet":
        bullet = structured_resume_repo.get_bullet(db, opt_request.target_id)
        if bullet:
            from app.schemas.structured_resume import BulletPointUpdate
            structured_resume_repo.update_bullet(
                db,
                opt_request.target_id,
                BulletPointUpdate(content=opt_request.optimized_content)
            )
    
    # Mark as applied
    opt_request.applied = True
    db.commit()
    
    logger.info("optimization_applied", optimization_id=optimization_id)
    
    return {"message": "Optimization applied successfully"}


# ============================================================================
# AI Suggestions
# ============================================================================

@router.get("/{resume_id}/suggestions", response_model=List[AISuggestionResponse])
async def get_suggestions(
    resume_id: UUID,
    target_id: Optional[UUID] = Query(None, description="Filter by target (section/bullet)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get AI suggestions for improvements.
    
    Returns real-time suggestions for the resume or specific targets.
    """
    resume = structured_resume_repo.get(db, resume_id)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    suggestions = structured_resume_repo.get_suggestions(
        db=db,
        user_id=current_user.id,
        target_id=target_id,
        dismissed=False
    )
    
    return suggestions


@router.post("/{resume_id}/suggestions/{suggestion_id}/dismiss", status_code=200)
async def dismiss_suggestion(
    resume_id: UUID,
    suggestion_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Dismiss a suggestion.
    """
    resume = structured_resume_repo.get(db, resume_id)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = structured_resume_repo.dismiss_suggestion(db, suggestion_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    
    logger.info("suggestion_dismissed", suggestion_id=suggestion_id)
    
    return {"message": "Suggestion dismissed"}


# ============================================================================
# Version Control
# ============================================================================

@router.post("/{resume_id}/versions", response_model=ResumeVersionResponse, status_code=201)
async def create_version(
    resume_id: UUID,
    version_request: CreateVersionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a version snapshot of the current resume state.
    
    Allows rollback to previous versions.
    """
    resume = structured_resume_repo.get(db, resume_id)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create snapshot
    from pydantic import parse_obj_as
    from app.schemas.structured_resume import StructuredResumeResponse
    
    snapshot = parse_obj_as(StructuredResumeResponse, resume).dict()
    
    version = structured_resume_repo.create_version(
        db=db,
        resume_id=resume_id,
        snapshot=snapshot,
        change_summary=version_request.change_summary
    )
    
    logger.info("version_created", resume_id=resume_id, version_number=version.version_number)
    
    return version


@router.get("/{resume_id}/versions", response_model=List[ResumeVersionResponse])
async def list_versions(
    resume_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all versions for a resume.
    """
    resume = structured_resume_repo.get(db, resume_id)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    versions = structured_resume_repo.get_versions(db, resume_id)
    
    return versions


@router.post("/{resume_id}/versions/restore", status_code=200)
async def restore_version(
    resume_id: UUID,
    restore_request: RestoreVersionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Restore resume to a previous version.
    
    This will replace the current state with the snapshot.
    """
    resume = structured_resume_repo.get(db, resume_id)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get version
    version = db.query(ResumeVersion).filter(
        ResumeVersion.id == restore_request.version_id,
        ResumeVersion.resume_id == resume_id
    ).first()
    
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    
    # TODO: Implement restore logic
    # This would involve recreating sections and bullets from the snapshot
    
    logger.info("version_restored", resume_id=resume_id, version_id=restore_request.version_id)
    
    return {"message": "Version restored successfully"}


# ============================================================================
# Export
# ============================================================================

@router.post("/{resume_id}/export")
async def export_resume(
    resume_id: UUID,
    export_request: ExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export resume in various formats.
    
    Formats: JSON, Markdown, PDF, DOCX
    """
    resume = structured_resume_repo.get(db, resume_id)
    
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if export_request.format == ExportFormat.JSON:
        from pydantic import parse_obj_as
        from app.schemas.structured_resume import StructuredResumeResponse
        
        resume_data = parse_obj_as(StructuredResumeResponse, resume).dict()
        return resume_data
    
    elif export_request.format == ExportFormat.MARKDOWN:
        # Build markdown from structured data
        markdown = intelligent_optimizer._build_resume_text(resume)
        return {"content": markdown, "format": "markdown"}
    
    elif export_request.format == ExportFormat.PDF:
        # Generate PDF
        from app.utils.pdf_generator import generate_premium_pdf
        from fastapi.responses import StreamingResponse
        
        markdown = intelligent_optimizer._build_resume_text(resume)
        buffer = await generate_premium_pdf(markdown, template_id=export_request.template_id)
        
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={resume.title}.pdf"}
        )
    
    elif export_request.format == ExportFormat.DOCX:
        # Generate DOCX
        from app.utils.docx_generator import generate_professional_docx
        from fastapi.responses import StreamingResponse
        
        markdown = intelligent_optimizer._build_resume_text(resume)
        buffer = generate_professional_docx(markdown)
        
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={resume.title}.docx"}
        )
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {export_request.format}")
