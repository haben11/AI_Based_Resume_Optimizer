"""
RAG Configuration Module

Centralized configuration for RAG pipeline components.
Allows easy tuning of retrieval, chunking, and validation parameters.

Author: CV Optimizer Team
Version: 1.0.0
"""

from typing import Dict
from pydantic import BaseModel, Field


class ChunkingConfig(BaseModel):
    """Configuration for semantic chunking."""
    
    min_chunk_size: int = Field(
        default=200,
        description="Minimum characters per chunk",
        ge=50,
        le=500
    )
    
    max_chunk_size: int = Field(
        default=1500,
        description="Maximum characters per chunk",
        ge=500,
        le=3000
    )
    
    target_chunk_size: int = Field(
        default=800,
        description="Target/ideal chunk size",
        ge=200,
        le=2000
    )
    
    max_keywords: int = Field(
        default=10,
        description="Maximum keywords to extract per chunk",
        ge=5,
        le=20
    )


class RetrievalConfig(BaseModel):
    """Configuration for enhanced retrieval."""
    
    initial_k: int = Field(
        default=10,
        description="Number of initial candidates to retrieve",
        ge=5,
        le=20
    )
    
    final_k: int = Field(
        default=5,
        description="Final number of chunks to return after re-ranking",
        ge=3,
        le=15
    )
    
    relevance_threshold: float = Field(
        default=0.7,
        description="Minimum similarity score (0-1) for filtering",
        ge=0.0,
        le=1.0
    )
    
    diversity_lambda: float = Field(
        default=0.3,
        description="Balance between relevance (0) and diversity (1)",
        ge=0.0,
        le=1.0
    )
    
    boost_metrics: float = Field(
        default=1.2,
        description="Score multiplier for chunks containing metrics",
        ge=1.0,
        le=2.0
    )
    
    boost_dates: float = Field(
        default=1.1,
        description="Score multiplier for chunks containing dates",
        ge=1.0,
        le=2.0
    )
    
    section_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "experience": 1.5,
            "skills": 1.3,
            "projects": 1.2,
            "summary": 1.1,
            "education": 1.0,
            "certifications": 1.0,
            "achievements": 1.1,
            "header": 0.8,
            "unknown": 0.9
        },
        description="Weight multipliers by section type"
    )


class ValidationConfig(BaseModel):
    """Configuration for output validation."""
    
    min_word_counts: Dict[str, int] = Field(
        default_factory=lambda: {
            "summary": 30,
            "experience": 50,
            "skills": 10,
            "education": 5
        },
        description="Minimum word counts by section"
    )
    
    min_total_words: int = Field(
        default=200,
        description="Minimum total words for entire resume",
        ge=100,
        le=500
    )
    
    max_total_words: int = Field(
        default=1500,
        description="Maximum total words for entire resume",
        ge=1000,
        le=3000
    )
    
    min_metrics_count: int = Field(
        default=3,
        description="Minimum number of quantifiable metrics",
        ge=0,
        le=10
    )
    
    min_action_verbs: int = Field(
        default=5,
        description="Minimum number of strong action verbs",
        ge=0,
        le=15
    )
    
    enable_hallucination_check: bool = Field(
        default=True,
        description="Enable basic hallucination detection"
    )


class LLMConfig(BaseModel):
    """Configuration for LLM generation."""
    
    model_name: str = Field(
        default="gemini-2.5-flash-lite",
        description="LLM model to use for generation"
    )
    
    temperature: float = Field(
        default=0.2,
        description="Temperature for generation (0=deterministic, 1=creative)",
        ge=0.0,
        le=1.0
    )
    
    max_retries: int = Field(
        default=3,
        description="Maximum retries on generation failure",
        ge=1,
        le=5
    )
    
    timeout_seconds: int = Field(
        default=60,
        description="Timeout for LLM API calls",
        ge=10,
        le=300
    )


class SemanticCacheConfig(BaseModel):
    """Configuration for semantic caching."""
    
    enabled: bool = Field(
        default=True,
        description="Enable semantic caching"
    )
    
    similarity_threshold: float = Field(
        default=0.85,
        description="Minimum cosine similarity for cache hit (0-1)",
        ge=0.0,
        le=1.0
    )
    
    ttl_hours: int = Field(
        default=168,  # 7 days
        description="Time-to-live for cache entries in hours",
        ge=1,
        le=720  # 30 days max
    )
    
    enable_exact_match: bool = Field(
        default=True,
        description="Enable exact hash matching (fastest)"
    )
    
    enable_semantic_match: bool = Field(
        default=True,
        description="Enable semantic similarity matching"
    )
    
    max_cache_size: int = Field(
        default=10000,
        description="Maximum number of cache entries",
        ge=100,
        le=100000
    )
    
    cleanup_interval_hours: int = Field(
        default=24,
        description="Interval for automatic cache cleanup",
        ge=1,
        le=168
    )


class RAGPipelineConfig(BaseModel):
    """Complete RAG pipeline configuration."""
    
    chunking: ChunkingConfig = Field(default_factory=ChunkingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    cache: SemanticCacheConfig = Field(default_factory=SemanticCacheConfig)
    
    enable_validation: bool = Field(
        default=True,
        description="Enable output validation"
    )
    
    enable_detailed_logging: bool = Field(
        default=True,
        description="Enable detailed structured logging"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "chunking": {
                    "max_chunk_size": 1500,
                    "target_chunk_size": 800
                },
                "retrieval": {
                    "initial_k": 10,
                    "final_k": 5,
                    "relevance_threshold": 0.7
                },
                "validation": {
                    "min_total_words": 200,
                    "min_metrics_count": 3
                },
                "llm": {
                    "temperature": 0.2,
                    "max_retries": 3
                }
            }
        }


# Default configuration instance
default_rag_config = RAGPipelineConfig()


# Preset configurations for different use cases
class RAGPresets:
    """Predefined configuration presets."""
    
    @staticmethod
    def high_precision() -> RAGPipelineConfig:
        """
        High precision configuration.
        
        Use when: Quality is more important than coverage.
        Trade-off: May miss some relevant content.
        """
        return RAGPipelineConfig(
            retrieval=RetrievalConfig(
                initial_k=15,
                final_k=5,
                relevance_threshold=0.8,  # Higher threshold
                diversity_lambda=0.2  # More focus on relevance
            ),
            validation=ValidationConfig(
                min_metrics_count=5,  # Stricter requirements
                min_action_verbs=7
            )
        )
    
    @staticmethod
    def high_recall() -> RAGPipelineConfig:
        """
        High recall configuration.
        
        Use when: Coverage is more important than precision.
        Trade-off: May include less relevant content.
        """
        return RAGPipelineConfig(
            retrieval=RetrievalConfig(
                initial_k=15,
                final_k=8,  # Return more results
                relevance_threshold=0.6,  # Lower threshold
                diversity_lambda=0.4  # More diversity
            ),
            validation=ValidationConfig(
                min_metrics_count=2,  # Relaxed requirements
                min_action_verbs=3
            )
        )
    
    @staticmethod
    def balanced() -> RAGPipelineConfig:
        """
        Balanced configuration (default).
        
        Use when: Need good balance of precision and recall.
        """
        return default_rag_config
    
    @staticmethod
    def fast() -> RAGPipelineConfig:
        """
        Fast configuration optimized for speed.
        
        Use when: Latency is critical.
        Trade-off: Slightly lower quality.
        """
        return RAGPipelineConfig(
            chunking=ChunkingConfig(
                max_chunk_size=1000  # Smaller chunks = faster
            ),
            retrieval=RetrievalConfig(
                initial_k=8,  # Fewer candidates
                final_k=4,
                relevance_threshold=0.75
            ),
            validation=ValidationConfig(
                enable_hallucination_check=False  # Skip expensive check
            ),
            llm=LLMConfig(
                timeout_seconds=30  # Shorter timeout
            )
        )
    
    @staticmethod
    def thorough() -> RAGPipelineConfig:
        """
        Thorough configuration for maximum quality.
        
        Use when: Quality is paramount, latency is acceptable.
        Trade-off: Slower processing.
        """
        return RAGPipelineConfig(
            chunking=ChunkingConfig(
                max_chunk_size=2000,  # Larger chunks = more context
                max_keywords=15
            ),
            retrieval=RetrievalConfig(
                initial_k=15,
                final_k=7,
                relevance_threshold=0.65,
                diversity_lambda=0.35
            ),
            validation=ValidationConfig(
                min_metrics_count=5,
                min_action_verbs=8,
                enable_hallucination_check=True
            ),
            llm=LLMConfig(
                temperature=0.1,  # More deterministic
                max_retries=5,
                timeout_seconds=120
            )
        )


# Export commonly used configurations
__all__ = [
    "ChunkingConfig",
    "RetrievalConfig",
    "ValidationConfig",
    "LLMConfig",
    "SemanticCacheConfig",
    "RAGPipelineConfig",
    "RAGPresets",
    "default_rag_config"
]
