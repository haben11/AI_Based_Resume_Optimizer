from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID

class OptimizeRequest(BaseModel):
    resume_id: UUID = Field(..., description="The unique ID of the uploaded resume")
    job_description: str = Field(
        ..., 
        min_length=50, 
        max_length=10000, 
        description="The job description to optimize for (min 50 characters)"
    )

class OptimizeResponse(BaseModel):
    optimized_cv: str = Field(..., description="The optimized resume content in Markdown format")
    resume_id: UUID

class OptimizeSnippetRequest(BaseModel):
    resume_id: UUID
    job_description: str
    snippet: str = Field(..., description="The specific text (bullet/paragraph) to regenerate")
    context: str = Field(None, description="Surrounding context to maintain flow")
    instruction: str = Field(None, description="Optional instruction like 'make it more technical' or 'use more action verbs'")

class UploadResponse(BaseModel):
    resume_id: UUID
    message: str = "Resume uploaded and indexed successfully"
    
    model_config = ConfigDict(from_attributes=True)
