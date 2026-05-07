from typing import List
from uuid import UUID
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.resume import OptimizationHistory
from app.crud.crud_resume import resume_repo
from app.services.resume_service import resume_service
from app.schemas.optimizer import OptimizeRequest, OptimizeResponse, UploadResponse, OptimizeSnippetRequest
from app.schemas.resume import Resume as ResumeSchema
from app.core.logging import logger
from app.utils.pdf_generator import generate_premium_pdf
from app.utils.docx_generator import generate_professional_docx
from app.services.streaming_rag_service import create_streaming_rag_service

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        resume_id = await resume_service.process_and_save_resume(
            db, file, current_user.id
        )
        return UploadResponse(resume_id=resume_id)
    except Exception as e:
        logger.error("upload_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to process resume: {str(e)}")

@router.post("/optimize", response_model=OptimizeResponse)
async def optimize_resume(
    request: OptimizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        # Validate ownership via Repo
        db_resume = resume_repo.get(db, id=request.resume_id)
        if not db_resume or db_resume.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Resume not found or access denied")

        # Business logic via Service (with RAG v3)
        optimized_text = await resume_service.optimize_and_log(
            db, 
            request.resume_id, 
            request.job_description,
            user_id=current_user.id
        )
        
        # Convert Markdown to plain text for display
        from app.utils.markdown_converter import markdown_converter
        plain_text = markdown_converter.to_plain_text(optimized_text)
        
        return OptimizeResponse(
            optimized_cv=plain_text,  # Return clean plain text for display
            resume_id=request.resume_id
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("optimization_failed", resume_id=request.resume_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")

@router.post("/optimize/snippet", response_model=OptimizeResponse)
async def optimize_snippet(
    request: OptimizeSnippetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Regenerate a specific section, bullet, or sentence."""
    try:
        # Validate ownership
        db_resume = resume_repo.get(db, id=request.resume_id)
        if not db_resume or db_resume.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Resume not found or access denied")

        optimized_snippet = await resume_service.optimize_snippet(
            db,
            request.resume_id,
            request.job_description,
            request.snippet,
            request.context,
            request.instruction
        )
        
        return OptimizeResponse(
            optimized_cv=optimized_snippet,
            resume_id=request.resume_id
        )
    except Exception as e:
        logger.error("snippet_optimization_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Snippet optimization failed: {str(e)}")


@router.post("/optimize/stream")
async def optimize_resume_stream(
    request: OptimizeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Stream resume optimization with real-time progress updates.
    
    Returns Server-Sent Events (SSE) with:
    - Progress updates for each stage
    - Generated tokens as they're produced
    - Final result with validation
    
    Event types:
    - progress: Stage progress updates
    - token: Generated text tokens
    - complete: Final result
    - error: Error occurred
    """
    try:
        # Validate ownership
        db_resume = resume_repo.get(db, id=request.resume_id)
        if not db_resume or db_resume.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Resume not found or access denied")
        
        # Create streaming RAG service
        streaming_service = create_streaming_rag_service(
            db=db,
            enable_grounding=True,
            enable_hallucination_detection=False,  # Optional, can be slow
            enable_multi_vector=False,
            enable_feedback_loop=False
        )
        
        # Index resume if not already indexed
        if db_resume.raw_text:
            await streaming_service.process_resume(
                text=db_resume.raw_text,
                resume_id=str(request.resume_id),
                user_id=str(current_user.id)
            )
        
        # Stream optimization
        optimized_content = None
        
        async def event_generator():
            nonlocal optimized_content
            
            async for message in streaming_service.optimize_cv_stream(
                resume_id=str(request.resume_id),
                job_description=request.job_description,
                original_resume_text=db_resume.raw_text,
                user_id=str(current_user.id),
                job_title=getattr(request, 'job_title', None),
                industry=getattr(request, 'industry', None)
            ):
                # Capture the final result
                if "event: complete" in message:
                    try:
                        import json
                        # Extract the result from the SSE message
                        data_line = message.split("data: ")[1].split("\n")[0]
                        data = json.loads(data_line)
                        if "result" in data and "optimized_content" in data["result"]:
                            optimized_content = data["result"]["optimized_content"]
                    except Exception as e:
                        logger.error("failed_to_extract_result", error=str(e))
                
                yield message
            
            # Save to database after streaming completes
            if optimized_content:
                try:
                    from app.models.resume import OptimizationHistory
                    import uuid
                    
                    optimization = OptimizationHistory(
                        id=uuid.uuid4(),
                        resume_id=request.resume_id,
                        job_description=request.job_description,
                        optimized_content=optimized_content
                    )
                    db.add(optimization)
                    db.commit()
                    
                    logger.info(
                        "streaming_optimization_saved",
                        resume_id=str(request.resume_id),
                        optimization_id=str(optimization.id)
                    )
                except Exception as e:
                    logger.error(
                        "failed_to_save_optimization",
                        resume_id=str(request.resume_id),
                        error=str(e)
                    )
                    db.rollback()
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("streaming_optimization_failed", resume_id=request.resume_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Streaming optimization failed: {str(e)}")

@router.get("/history", response_model=List[ResumeSchema])
async def get_optimization_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all resumes via Repository."""
    return resume_repo.get_by_user(db, user_id=current_user.id)

@router.get("/resume/{resume_id}", response_model=ResumeSchema)
async def get_resume_details(
    resume_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get details via Repository."""
    resume = resume_repo.get(db, id=resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume
@router.get("/resume/{resume_id}/preview")
async def get_resume_preview(
    resume_id: UUID,
    optimization_id: UUID = None,
    template_id: str = "modern-1-blue",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the rendered HTML preview of the optimized resume."""
    resume = resume_repo.get(db, id=resume_id)
    if not resume or resume.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if optimization_id:
        opt = db.query(OptimizationHistory).filter(
            OptimizationHistory.id == optimization_id,
            OptimizationHistory.resume_id == resume_id
        ).first()
    else:
        opt = db.query(OptimizationHistory).filter(
            OptimizationHistory.resume_id == resume_id
        ).order_by(OptimizationHistory.created_at.desc()).first()
        
    if not opt:
        logger.warning("optimization_not_found", resume_id=resume_id)
        raise HTTPException(status_code=404, detail="No optimization found. Please optimize your resume first.")
        
    try:
        from app.utils.cv_parser import parse_optimized_cv
        from app.utils.template_factory import template_factory
        
        # Log content snippet for debugging
        logger.info("rendering_preview", resume_id=resume_id, template_id=template_id)
        
        structured_data = parse_optimized_cv(opt.optimized_content)
        
        # Ensure name fallback
        if structured_data.get("full_name") == "Applicant Name":
            # Try to get from resume filename or metadata
            structured_data["full_name"] = resume.filename.rsplit('.', 1)[0].replace('_', ' ').title()

        html_content = template_factory.render(template_id, structured_data)
        
        return {"html": html_content}
    except Exception as e:
        import traceback
        logger.error("preview_generation_failed", error=str(e), stack=traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Rendering Error: {str(e)}")

@router.get("/resume/{resume_id}/download")
async def download_optimized_pdf(
    resume_id: UUID,
    optimization_id: UUID = None,
    template_id: str = "modern-1-blue",
    format: str = "pdf",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download the optimized resume as a premium PDF or DOCX."""
    try:
        resume = resume_repo.get(db, id=resume_id)
        if not resume or resume.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        if optimization_id:
            opt = db.query(OptimizationHistory).filter(
                OptimizationHistory.id == optimization_id,
                OptimizationHistory.resume_id == resume_id
            ).first()
        else:
            opt = db.query(OptimizationHistory).filter(
                OptimizationHistory.resume_id == resume_id
            ).order_by(OptimizationHistory.created_at.desc()).first()
            
        if not opt:
            raise HTTPException(status_code=404, detail="No optimization found for this resume")
            
        logger.info("generating_download", resume_id=resume_id, format=format, template_id=template_id)
        
        if format.lower() == "docx":
            buffer = generate_professional_docx(opt.optimized_content)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ext = "docx"
        else:
            buffer = await generate_premium_pdf(opt.optimized_content, template_id=template_id)
            media_type = "application/pdf"
            ext = "pdf"
        
        filename = f"Optimized_{resume.filename.rsplit('.', 1)[0]}.{ext}"
        
        logger.info("download_successful", resume_id=resume_id, format=format, filename=filename)
        
        # Record download feedback (Phase 3)
        try:
            from app.ml.feedback_loop import FeedbackType
            await resume_service.record_user_feedback(
                db=db,
                user_id=current_user.id,
                resume_id=resume_id,
                optimization_id=opt.id,
                feedback_type=FeedbackType.DOWNLOAD,
                value=1.0
            )
        except Exception as e:
            logger.warning("feedback_recording_failed", error=str(e))
        
        return StreamingResponse(
            buffer,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("download_failed", resume_id=resume_id, format=format, error=str(e))
        import traceback
        logger.error("download_traceback", traceback=traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to generate {format.upper()}: {str(e)}")

@router.get("/metrics/feedback")
async def get_feedback_metrics(
    resume_id: UUID = None,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get feedback metrics (Phase 3 feature)."""
    try:
        # Validate resume ownership if resume_id provided
        if resume_id:
            resume = resume_repo.get(db, id=resume_id)
            if not resume or resume.user_id != current_user.id:
                raise HTTPException(status_code=404, detail="Resume not found")
        
        metrics = resume_service.get_feedback_metrics(
            db=db,
            resume_id=resume_id,
            days=days
        )
        
        return metrics
    except HTTPException:
        raise
    except Exception as e:
        logger.error("metrics_fetch_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch metrics: {str(e)}")

@router.get("/model/info")
async def get_model_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get RAG model information (Phase 3 feature)."""
    try:
        info = resume_service.get_model_info(db=db)
        return info
    except Exception as e:
        logger.error("model_info_fetch_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch model info: {str(e)}")


# Cache Management Endpoints (Phase 4)

@router.get("/cache/statistics")
async def get_cache_statistics(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get semantic cache statistics.
    
    Shows cache performance metrics including:
    - Hit rate
    - Cost savings
    - Time savings
    - Match type distribution
    
    Args:
        days: Number of days to include in statistics (default: 7)
    """
    try:
        from app.services.semantic_cache_service import create_semantic_cache_service
        
        cache_service = create_semantic_cache_service(db=db)
        stats = cache_service.get_statistics(days=days)
        
        logger.info("cache_statistics_fetched", user_id=current_user.id, days=days)
        
        return {
            "success": True,
            "statistics": stats,
            "period_days": days
        }
    except Exception as e:
        logger.error("cache_statistics_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch cache statistics: {str(e)}")


@router.post("/cache/cleanup")
async def cleanup_cache(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger cache cleanup.
    
    Removes expired cache entries based on TTL.
    This is normally done automatically, but can be triggered manually.
    """
    try:
        from app.services.semantic_cache_service import create_semantic_cache_service
        
        cache_service = create_semantic_cache_service(db=db)
        deleted_count = cache_service.cleanup_expired_entries()
        
        logger.info("cache_cleanup_triggered", user_id=current_user.id, deleted=deleted_count)
        
        return {
            "success": True,
            "message": f"Cleaned up {deleted_count} expired cache entries",
            "deleted_count": deleted_count
        }
    except Exception as e:
        logger.error("cache_cleanup_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Cache cleanup failed: {str(e)}")


@router.delete("/cache/clear")
async def clear_cache(
    confirm: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Clear all cache entries.
    
    WARNING: This will delete ALL cached responses.
    Requires confirmation parameter to be set to true.
    
    Args:
        confirm: Must be true to proceed with clearing cache
    """
    try:
        if not confirm:
            raise HTTPException(
                status_code=400,
                detail="Cache clear requires confirmation. Set confirm=true to proceed."
            )
        
        from app.models.semantic_cache import SemanticCacheEntry
        
        # Delete all cache entries
        deleted_count = db.query(SemanticCacheEntry).delete()
        db.commit()
        
        logger.warning("cache_cleared", user_id=current_user.id, deleted=deleted_count)
        
        return {
            "success": True,
            "message": f"Cleared {deleted_count} cache entries",
            "deleted_count": deleted_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("cache_clear_failed", error=str(e))
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Cache clear failed: {str(e)}")
