from sqlalchemy.orm import Session
from fastapi import UploadFile
from uuid import UUID
from app.crud.crud_resume import resume_repo, optimization_repo
from app.services.rag_service_v3 import create_rag_service_v3
from app.utils.file_parser import FileParser
from app.utils.text_cleaner import TextCleaner
from app.schemas.resume import ResumeCreate
from app.core.logging import logger
from app.ml.feedback_loop import FeedbackType

class ResumeService:
    def __init__(self):
        """Initialize resume service with RAG v3."""
        # Create RAG service v3 with Phase 3 enhancements
        self.rag_service = None  # Will be initialized per request with DB session
    
    def _get_rag_service(self, db: Session):
        """Get or create RAG service v3 instance with DB session."""
        # Create new instance with DB session for feedback loop
        return create_rag_service_v3(
            db=db,
            use_fine_tuned_embeddings=False,  # Set to True when fine-tuned model is ready
            enable_multi_vector=True,
            enable_hallucination_detection=True,
            enable_feedback_loop=True,
            enable_ab_testing=False  # Enable when ready for A/B testing
        )
    
    async def process_and_save_resume(
        self, 
        db: Session, 
        file: UploadFile, 
        user_id: UUID
    ) -> str:
        """
        Process and save resume with RAG v3.
        
        Args:
            db: Database session
            file: Uploaded file
            user_id: User identifier
            
        Returns:
            Resume ID
        """
        text = await FileParser.parse_file(file)
        
        # Save to DB via Repository
        resume_in = ResumeCreate(filename=file.filename, raw_text=text)
        db_resume = resume_repo.create_with_user(db, obj_in=resume_in, user_id=user_id)
        
        # Index in RAG Service v3
        rag_service = self._get_rag_service(db)
        await rag_service.process_resume(
            text=text,
            resume_id=str(db_resume.id),
            user_id=str(user_id)
        )
        
        logger.info(
            "resume_processed_v3",
            resume_id=str(db_resume.id),
            user_id=str(user_id),
            filename=file.filename
        )
        
        return str(db_resume.id)

    async def optimize_and_log(
        self, 
        db: Session, 
        resume_id: UUID, 
        job_description: str,
        user_id: UUID = None
    ) -> str:
        """
        Optimize resume and log with RAG v3 enhancements.
        
        Args:
            db: Database session
            resume_id: Resume identifier
            job_description: Target job description
            user_id: User identifier (optional, for feedback tracking)
            
        Returns:
            Optimized resume text
        """
        # Sanitize dirty text from copy-paste
        clean_job_desc = TextCleaner.clean_text(job_description)
        
        # Get original resume text for hallucination detection
        db_resume = resume_repo.get(db, id=resume_id)
        original_text = db_resume.raw_text if db_resume else None
        
        # Business logic: optimization with RAG v3
        rag_service = self._get_rag_service(db)
        
        result = await rag_service.optimize_cv(
            resume_id=str(resume_id),
            job_description=clean_job_desc,
            original_resume_text=original_text,
            user_id=str(user_id) if user_id else None,
            optimization_id=None  # Will be set after creating history
        )
        
        # Extract optimized content
        optimized_text = result["optimized_content"]
        validation = result["validation"]
        hallucination_check = result.get("hallucination_check")
        
        # Log validation results
        logger.info(
            "optimization_complete_v3",
            resume_id=str(resume_id),
            quality_score=validation["quality_score"],
            is_valid=validation["is_valid"],
            is_trustworthy=hallucination_check["is_trustworthy"] if hallucination_check else None,
            confidence=hallucination_check["confidence"] if hallucination_check else None
        )
        
        # Log validation issues
        if validation["issues"]:
            for issue in validation["issues"]:
                logger.warning(
                    "validation_issue",
                    resume_id=str(resume_id),
                    severity=issue["severity"],
                    message=issue["message"]
                )
        
        # Log hallucination findings
        if hallucination_check and hallucination_check["findings"]:
            for finding in hallucination_check["findings"]:
                logger.warning(
                    "hallucination_finding",
                    resume_id=str(resume_id),
                    type=finding["type"],
                    severity=finding["severity"],
                    claim=finding["claim"][:100]
                )
        
        # Log to DB via Repository (save the cleaned version)
        optimization_history = optimization_repo.create_history(
            db, 
            resume_id=resume_id, 
            job_description=clean_job_desc, 
            optimized_content=optimized_text
        )
        
        logger.info(
            "optimization_logged",
            resume_id=str(resume_id),
            optimization_id=str(optimization_history.id)
        )
        
        return optimized_text
    
    async def record_user_feedback(
        self,
        db: Session,
        user_id: UUID,
        resume_id: UUID,
        optimization_id: UUID,
        feedback_type: FeedbackType,
        value: float = None
    ):
        """
        Record user feedback for continuous learning.
        
        Args:
            db: Database session
            user_id: User identifier
            resume_id: Resume identifier
            optimization_id: Optimization identifier
            feedback_type: Type of feedback
            value: Feedback value (0-1)
        """
        rag_service = self._get_rag_service(db)
        
        await rag_service.record_feedback(
            user_id=str(user_id),
            resume_id=str(resume_id),
            optimization_id=str(optimization_id),
            feedback_type=feedback_type,
            value=value
        )
        
        logger.info(
            "feedback_recorded",
            user_id=str(user_id),
            resume_id=str(resume_id),
            feedback_type=feedback_type.value
        )
    
    def get_feedback_metrics(
        self,
        db: Session,
        resume_id: UUID = None,
        days: int = 30
    ) -> dict:
        """
        Get feedback metrics.
        
        Args:
            db: Database session
            resume_id: Optional resume filter
            days: Number of days to look back
            
        Returns:
            Feedback metrics dictionary
        """
        rag_service = self._get_rag_service(db)
        return rag_service.get_feedback_metrics(
            resume_id=str(resume_id) if resume_id else None,
            days=days
        )
    
    def get_model_info(self, db: Session) -> dict:
        """
        Get RAG model information.
        
        Args:
            db: Database session
            
        Returns:
            Model information dictionary
        """
        rag_service = self._get_rag_service(db)
        return rag_service.get_model_info()

    async def optimize_snippet(
        self,
        db: Session,
        resume_id: UUID,
        job_description: str,
        snippet: str,
        context: str = None,
        instruction: str = None
    ) -> str:
        """
        Regenerate a specific snippet of the CV.
        """
        rag_service = self._get_rag_service(db)
        return await rag_service.optimize_snippet(
            resume_id=str(resume_id),
            job_description=job_description,
            snippet=snippet,
            context=context,
            instruction=instruction
        )

resume_service = ResumeService()

