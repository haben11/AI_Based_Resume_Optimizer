import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    raw_text = Column(Text, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="resumes")
    optimizations = relationship("OptimizationHistory", back_populates="resume")

class OptimizationHistory(Base):
    __tablename__ = "optimization_histories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False)
    job_description = Column(Text, nullable=False)
    optimized_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    resume = relationship("Resume", back_populates="optimizations")
