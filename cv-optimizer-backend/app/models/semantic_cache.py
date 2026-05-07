"""
Semantic Cache Models

Database models for semantic caching of LLM responses.
Uses embeddings to find similar queries and return cached responses.

Author: CV Optimizer Team
Version: 1.0.0
"""

from sqlalchemy import Column, String, Text, Integer, Float, DateTime, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func
import uuid
from app.db.session import Base


class SemanticCacheEntry(Base):
    """
    Semantic cache entry for LLM responses.
    
    Stores query embeddings and responses to enable semantic similarity search.
    When a similar query is detected, returns cached response instead of
    calling LLM again.
    """
    __tablename__ = "semantic_cache_entries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Query information
    query_text = Column(Text, nullable=False)  # Original query text
    query_hash = Column(String(64), nullable=False, index=True)  # SHA256 hash for exact match
    query_embedding = Column(ARRAY(Float), nullable=False)  # Embedding vector for semantic search
    
    # Context information (for cache key)
    resume_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Optional resume context
    job_title = Column(String(255), nullable=True, index=True)  # Job title for grouping
    industry = Column(String(100), nullable=True, index=True)  # Industry for grouping
    context_hash = Column(String(64), nullable=True, index=True)  # Hash of resume context
    
    # Response information
    response_text = Column(Text, nullable=False)  # Cached LLM response
    response_metadata = Column(JSONB, nullable=True)  # Additional metadata (validation, etc.)
    
    # Cache statistics
    hit_count = Column(Integer, default=0)  # Number of times this cache was hit
    last_hit_at = Column(DateTime(timezone=True), nullable=True)  # Last cache hit time
    
    # Quality metrics
    quality_score = Column(Float, nullable=True)  # Quality score of cached response
    similarity_threshold = Column(Float, default=0.85)  # Minimum similarity for cache hit
    
    # Cache management
    is_active = Column(Boolean, default=True)  # Whether cache entry is active
    ttl_hours = Column(Integer, default=168)  # Time-to-live in hours (default 7 days)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Expiration timestamp
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_cache_job_title_industry', 'job_title', 'industry'),
        Index('idx_cache_expires_at', 'expires_at'),
        Index('idx_cache_active', 'is_active'),
    )


class CacheStatistics(Base):
    """
    Cache statistics for monitoring and optimization.
    
    Tracks cache performance metrics over time.
    """
    __tablename__ = "cache_statistics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Time period
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), nullable=False)  # hourly, daily, weekly
    
    # Cache metrics
    total_queries = Column(Integer, default=0)  # Total queries in period
    cache_hits = Column(Integer, default=0)  # Number of cache hits
    cache_misses = Column(Integer, default=0)  # Number of cache misses
    exact_matches = Column(Integer, default=0)  # Exact hash matches
    semantic_matches = Column(Integer, default=0)  # Semantic similarity matches
    
    # Performance metrics
    avg_similarity_score = Column(Float, nullable=True)  # Average similarity for hits
    avg_response_time_ms = Column(Float, nullable=True)  # Average response time
    total_cost_saved = Column(Float, default=0.0)  # Estimated cost savings
    total_time_saved_ms = Column(Float, default=0.0)  # Total time saved
    
    # Popular queries
    top_job_titles = Column(JSONB, nullable=True)  # Most cached job titles
    top_industries = Column(JSONB, nullable=True)  # Most cached industries
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        Index('idx_stats_date_period', 'date', 'period_type'),
    )
