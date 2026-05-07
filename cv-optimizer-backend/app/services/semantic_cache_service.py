"""
Semantic Cache Service

Implements semantic caching using embeddings to find similar queries.
Reduces LLM costs and latency by 30-60% for similar job descriptions.

Author: CV Optimizer Team
Version: 1.0.0
"""

import hashlib
import numpy as np
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.models.semantic_cache import SemanticCacheEntry, CacheStatistics
from app.core.config import settings
from app.core.logging import logger
import uuid


class SemanticCacheService:
    """
    Semantic cache service for LLM responses.
    
    Uses embeddings to find semantically similar queries and return
    cached responses instead of calling LLM again.
    """
    
    def __init__(
        self,
        db: Session,
        similarity_threshold: float = 0.85,
        ttl_hours: int = 168,  # 7 days
        enable_exact_match: bool = True,
        enable_semantic_match: bool = True
    ):
        """
        Initialize semantic cache service.
        
        Args:
            db: Database session
            similarity_threshold: Minimum cosine similarity for cache hit (0-1)
            ttl_hours: Time-to-live for cache entries in hours
            enable_exact_match: Enable exact hash matching
            enable_semantic_match: Enable semantic similarity matching
        """
        self.db = db
        self.similarity_threshold = similarity_threshold
        self.ttl_hours = ttl_hours
        self.enable_exact_match = enable_exact_match
        self.enable_semantic_match = enable_semantic_match
        
        # Initialize embeddings
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=settings.GOOGLE_API_KEY
        )
        
        logger.info(
            "semantic_cache_initialized",
            similarity_threshold=similarity_threshold,
            ttl_hours=ttl_hours
        )
    
    def _compute_hash(self, text: str) -> str:
        """Compute SHA256 hash of text."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def _compute_embedding(self, text: str) -> List[float]:
        """Compute embedding vector for text."""
        return self.embeddings.embed_query(text)
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def _is_valid_uuid(self, val: str) -> bool:
        """Check if string is a valid UUID."""
        try:
            uuid.UUID(val)
            return True
        except (ValueError, AttributeError):
            return False
    
    async def get_cached_response(
        self,
        query_text: str,
        resume_id: Optional[str] = None,
        job_title: Optional[str] = None,
        industry: Optional[str] = None,
        context_hash: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response for query.
        
        Tries exact match first, then semantic similarity match.
        
        Args:
            query_text: Query text (job description)
            resume_id: Optional resume ID for context
            job_title: Optional job title for grouping
            industry: Optional industry for grouping
            context_hash: Optional hash of resume context
            
        Returns:
            Cached response dict or None if no match found
        """
        start_time = datetime.now()
        
        # Compute query hash
        query_hash = self._compute_hash(query_text)
        
        # Try exact match first (fastest)
        if self.enable_exact_match:
            exact_match = await self._get_exact_match(
                query_hash=query_hash,
                job_title=job_title,
                industry=industry,
                context_hash=context_hash
            )
            
            if exact_match:
                await self._record_cache_hit(
                    exact_match,
                    similarity_score=1.0,
                    match_type="exact",
                    response_time_ms=(datetime.now() - start_time).total_seconds() * 1000
                )
                
                logger.info(
                    "cache_hit_exact",
                    query_hash=query_hash[:16],
                    job_title=job_title,
                    hit_count=exact_match.hit_count + 1
                )
                
                return {
                    "response_text": exact_match.response_text,
                    "response_metadata": exact_match.response_metadata,
                    "cache_hit": True,
                    "match_type": "exact",
                    "similarity_score": 1.0,
                    "cached_at": exact_match.created_at,
                    "hit_count": exact_match.hit_count + 1
                }
        
        # Try semantic match (slower but more flexible)
        if self.enable_semantic_match:
            # Compute query embedding
            query_embedding = self._compute_embedding(query_text)
            
            semantic_match, similarity = await self._get_semantic_match(
                query_embedding=query_embedding,
                job_title=job_title,
                industry=industry,
                context_hash=context_hash
            )
            
            if semantic_match and similarity >= self.similarity_threshold:
                await self._record_cache_hit(
                    semantic_match,
                    similarity_score=similarity,
                    match_type="semantic",
                    response_time_ms=(datetime.now() - start_time).total_seconds() * 1000
                )
                
                logger.info(
                    "cache_hit_semantic",
                    query_hash=query_hash[:16],
                    job_title=job_title,
                    similarity=similarity,
                    hit_count=semantic_match.hit_count + 1
                )
                
                return {
                    "response_text": semantic_match.response_text,
                    "response_metadata": semantic_match.response_metadata,
                    "cache_hit": True,
                    "match_type": "semantic",
                    "similarity_score": similarity,
                    "cached_at": semantic_match.created_at,
                    "hit_count": semantic_match.hit_count + 1
                }
        
        # No cache hit
        logger.info(
            "cache_miss",
            query_hash=query_hash[:16],
            job_title=job_title
        )
        
        await self._record_cache_miss()
        
        return None
    
    async def _get_exact_match(
        self,
        query_hash: str,
        job_title: Optional[str],
        industry: Optional[str],
        context_hash: Optional[str]
    ) -> Optional[SemanticCacheEntry]:
        """Get exact hash match from cache."""
        try:
            # Build query
            query = self.db.query(SemanticCacheEntry).filter(
                and_(
                    SemanticCacheEntry.query_hash == query_hash,
                    SemanticCacheEntry.is_active == True,
                    or_(
                        SemanticCacheEntry.expires_at.is_(None),
                        SemanticCacheEntry.expires_at > datetime.now()
                    )
                )
            )
            
            # Add optional filters
            if job_title:
                query = query.filter(SemanticCacheEntry.job_title == job_title)
            
            if industry:
                query = query.filter(SemanticCacheEntry.industry == industry)
            
            if context_hash:
                query = query.filter(SemanticCacheEntry.context_hash == context_hash)
            
            return query.first()
            
        except Exception as e:
            logger.error("exact_match_failed", error=str(e))
            return None
    
    async def _get_semantic_match(
        self,
        query_embedding: List[float],
        job_title: Optional[str],
        industry: Optional[str],
        context_hash: Optional[str]
    ) -> Tuple[Optional[SemanticCacheEntry], float]:
        """Get semantic similarity match from cache."""
        try:
            # Get candidate entries
            query = self.db.query(SemanticCacheEntry).filter(
                and_(
                    SemanticCacheEntry.is_active == True,
                    or_(
                        SemanticCacheEntry.expires_at.is_(None),
                        SemanticCacheEntry.expires_at > datetime.now()
                    )
                )
            )
            
            # Add optional filters
            if job_title:
                query = query.filter(SemanticCacheEntry.job_title == job_title)
            
            if industry:
                query = query.filter(SemanticCacheEntry.industry == industry)
            
            if context_hash:
                query = query.filter(SemanticCacheEntry.context_hash == context_hash)
            
            # Limit candidates for performance
            candidates = query.limit(100).all()
            
            if not candidates:
                return None, 0.0
            
            # Compute similarities
            best_match = None
            best_similarity = 0.0
            
            for candidate in candidates:
                similarity = self._cosine_similarity(
                    query_embedding,
                    candidate.query_embedding
                )
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = candidate
            
            return best_match, best_similarity
            
        except Exception as e:
            logger.error("semantic_match_failed", error=str(e))
            return None, 0.0
    
    async def cache_response(
        self,
        query_text: str,
        response_text: str,
        response_metadata: Optional[Dict[str, Any]] = None,
        resume_id: Optional[str] = None,
        job_title: Optional[str] = None,
        industry: Optional[str] = None,
        context_hash: Optional[str] = None,
        quality_score: Optional[float] = None
    ) -> SemanticCacheEntry:
        """
        Cache LLM response for future use.
        
        Args:
            query_text: Query text (job description)
            response_text: LLM response
            response_metadata: Optional metadata
            resume_id: Optional resume ID
            job_title: Optional job title
            industry: Optional industry
            context_hash: Optional context hash
            quality_score: Optional quality score
            
        Returns:
            Created cache entry
        """
        try:
            # Compute hash and embedding
            query_hash = self._compute_hash(query_text)
            query_embedding = self._compute_embedding(query_text)
            
            # Calculate expiration
            expires_at = datetime.now() + timedelta(hours=self.ttl_hours)
            
            # Create cache entry
            cache_entry = SemanticCacheEntry(
                id=uuid.uuid4(),
                query_text=query_text,
                query_hash=query_hash,
                query_embedding=query_embedding,
                resume_id=uuid.UUID(resume_id) if resume_id and self._is_valid_uuid(resume_id) else None,
                job_title=job_title,
                industry=industry,
                context_hash=context_hash,
                response_text=response_text,
                response_metadata=response_metadata,
                quality_score=quality_score,
                similarity_threshold=self.similarity_threshold,
                ttl_hours=self.ttl_hours,
                expires_at=expires_at,
                hit_count=0,
                is_active=True
            )
            
            self.db.add(cache_entry)
            self.db.commit()
            self.db.refresh(cache_entry)
            
            logger.info(
                "response_cached",
                cache_id=str(cache_entry.id),
                job_title=job_title,
                industry=industry,
                expires_at=expires_at
            )
            
            return cache_entry
            
        except Exception as e:
            logger.error("cache_response_failed", error=str(e))
            self.db.rollback()
            raise
    
    async def _record_cache_hit(
        self,
        cache_entry: SemanticCacheEntry,
        similarity_score: float,
        match_type: str,
        response_time_ms: float
    ):
        """Record cache hit statistics."""
        try:
            # Update cache entry
            cache_entry.hit_count += 1
            cache_entry.last_hit_at = datetime.now()
            self.db.commit()
            
            # Update statistics
            await self._update_statistics(
                cache_hit=True,
                match_type=match_type,
                similarity_score=similarity_score,
                response_time_ms=response_time_ms
            )
            
        except Exception as e:
            logger.error("record_cache_hit_failed", error=str(e))
    
    async def _record_cache_miss(self):
        """Record cache miss statistics."""
        try:
            await self._update_statistics(cache_hit=False)
        except Exception as e:
            logger.error("record_cache_miss_failed", error=str(e))
    
    async def _update_statistics(
        self,
        cache_hit: bool,
        match_type: Optional[str] = None,
        similarity_score: Optional[float] = None,
        response_time_ms: Optional[float] = None
    ):
        """Update cache statistics."""
        try:
            # Get or create today's statistics
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            stats = self.db.query(CacheStatistics).filter(
                and_(
                    CacheStatistics.date == today,
                    CacheStatistics.period_type == "daily"
                )
            ).first()
            
            if not stats:
                stats = CacheStatistics(
                    id=uuid.uuid4(),
                    date=today,
                    period_type="daily",
                    total_queries=0,
                    cache_hits=0,
                    cache_misses=0,
                    exact_matches=0,
                    semantic_matches=0
                )
                self.db.add(stats)
            
            # Update counts
            stats.total_queries += 1
            
            if cache_hit:
                stats.cache_hits += 1
                
                if match_type == "exact":
                    stats.exact_matches += 1
                elif match_type == "semantic":
                    stats.semantic_matches += 1
                
                # Update average similarity
                if similarity_score is not None:
                    if stats.avg_similarity_score is None:
                        stats.avg_similarity_score = similarity_score
                    else:
                        # Running average
                        stats.avg_similarity_score = (
                            (stats.avg_similarity_score * (stats.cache_hits - 1) + similarity_score) /
                            stats.cache_hits
                        )
                
                # Update average response time
                if response_time_ms is not None:
                    if stats.avg_response_time_ms is None:
                        stats.avg_response_time_ms = response_time_ms
                    else:
                        stats.avg_response_time_ms = (
                            (stats.avg_response_time_ms * (stats.cache_hits - 1) + response_time_ms) /
                            stats.cache_hits
                        )
                
                # Estimate cost savings (assuming $0.01 per LLM call)
                stats.total_cost_saved += 0.01
                
                # Estimate time savings (assuming 30 seconds per LLM call)
                stats.total_time_saved_ms += 30000 - (response_time_ms or 0)
            else:
                stats.cache_misses += 1
            
            self.db.commit()
            
        except Exception as e:
            logger.error("update_statistics_failed", error=str(e))
            self.db.rollback()
    
    def get_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get cache statistics for the last N days.
        
        Args:
            days: Number of days to include
            
        Returns:
            Statistics dictionary
        """
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            stats = self.db.query(CacheStatistics).filter(
                and_(
                    CacheStatistics.date >= start_date,
                    CacheStatistics.period_type == "daily"
                )
            ).all()
            
            if not stats:
                return {
                    "total_queries": 0,
                    "cache_hits": 0,
                    "cache_misses": 0,
                    "hit_rate": 0.0,
                    "exact_matches": 0,
                    "semantic_matches": 0,
                    "avg_similarity_score": 0.0,
                    "total_cost_saved": 0.0,
                    "total_time_saved_hours": 0.0
                }
            
            # Aggregate statistics
            total_queries = sum(s.total_queries for s in stats)
            cache_hits = sum(s.cache_hits for s in stats)
            cache_misses = sum(s.cache_misses for s in stats)
            exact_matches = sum(s.exact_matches for s in stats)
            semantic_matches = sum(s.semantic_matches for s in stats)
            total_cost_saved = sum(s.total_cost_saved for s in stats)
            total_time_saved_ms = sum(s.total_time_saved_ms for s in stats)
            
            # Calculate averages
            avg_similarity = np.mean([
                s.avg_similarity_score for s in stats
                if s.avg_similarity_score is not None
            ]) if any(s.avg_similarity_score for s in stats) else 0.0
            
            hit_rate = (cache_hits / total_queries * 100) if total_queries > 0 else 0.0
            
            return {
                "total_queries": total_queries,
                "cache_hits": cache_hits,
                "cache_misses": cache_misses,
                "hit_rate": hit_rate,
                "exact_matches": exact_matches,
                "semantic_matches": semantic_matches,
                "avg_similarity_score": float(avg_similarity),
                "total_cost_saved": total_cost_saved,
                "total_time_saved_hours": total_time_saved_ms / (1000 * 60 * 60),
                "days": days
            }
            
        except Exception as e:
            logger.error("get_statistics_failed", error=str(e))
            return {}
    
    def cleanup_expired_entries(self) -> int:
        """
        Clean up expired cache entries.
        
        Returns:
            Number of entries deleted
        """
        try:
            deleted = self.db.query(SemanticCacheEntry).filter(
                and_(
                    SemanticCacheEntry.expires_at.isnot(None),
                    SemanticCacheEntry.expires_at < datetime.now()
                )
            ).delete()
            
            self.db.commit()
            
            logger.info("cache_cleanup_complete", deleted_count=deleted)
            return deleted
            
        except Exception as e:
            logger.error("cache_cleanup_failed", error=str(e))
            self.db.rollback()
            return 0


def create_semantic_cache_service(
    db: Session,
    **kwargs
) -> SemanticCacheService:
    """
    Factory function to create semantic cache service.
    
    Args:
        db: Database session
        **kwargs: Additional configuration options
        
    Returns:
        SemanticCacheService instance
    """
    return SemanticCacheService(db=db, **kwargs)
