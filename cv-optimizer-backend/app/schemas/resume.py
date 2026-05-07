from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

# Optimization History Schemas
class OptimizationHistoryBase(BaseModel):
    job_description: str
    optimized_content: str

class OptimizationHistory(OptimizationHistoryBase):
    id: UUID
    resume_id: UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# Resume Schemas
class ResumeBase(BaseModel):
    filename: str

class ResumeCreate(ResumeBase):
    raw_text: str
    user_id: Optional[UUID] = None

class Resume(ResumeBase):
    id: UUID
    user_id: Optional[UUID]
    created_at: datetime
    # Optionally include a summary of optimizations
    optimizations: List[OptimizationHistory] = []
    
    model_config = ConfigDict(from_attributes=True)
