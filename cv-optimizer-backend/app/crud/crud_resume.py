from typing import List, Any
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.repository import CRUDBase
from app.models.resume import Resume, OptimizationHistory
from app.schemas.resume import ResumeCreate, OptimizationHistoryBase

class CRUDResume(CRUDBase[Resume, ResumeCreate, Any]):
    def get_by_user(self, db: Session, *, user_id: UUID) -> List[Resume]:
        return db.query(Resume).filter(Resume.user_id == user_id).all()
        
    def create_with_user(self, db: Session, *, obj_in: ResumeCreate, user_id: UUID) -> Resume:
        db_obj = Resume(
            filename=obj_in.filename,
            raw_text=obj_in.raw_text,
            user_id=user_id
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

class CRUDOptimization(CRUDBase[OptimizationHistory, OptimizationHistoryBase, Any]):
    def create_history(self, db: Session, *, resume_id: UUID, job_description: str, optimized_content: str) -> OptimizationHistory:
        db_obj = OptimizationHistory(
            resume_id=resume_id,
            job_description=job_description,
            optimized_content=optimized_content
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

resume_repo = CRUDResume(Resume)
optimization_repo = CRUDOptimization(OptimizationHistory)
