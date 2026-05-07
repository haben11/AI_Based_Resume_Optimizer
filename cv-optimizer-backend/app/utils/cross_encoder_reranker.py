"""
Cross-Encoder Re-ranker for Improved Relevance

Implements cross-encoder based re-ranking to improve retrieval quality.
Cross-encoders jointly encode query and document, providing more accurate
relevance scores than bi-encoder (embedding) approaches.

Uses sentence-transformers cross-encoder models for efficient inference.

Author: CV Optimizer Team
Version: 2.0.0
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass
import numpy as np
from langchain.schema import Document

try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False


@dataclass
class RerankerConfig:
    """Configuration for cross-encoder re-ranker."""
    model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"  # Fast, accurate model
    batch_size: int = 32  # Batch size for inference
    top_k: int = 5  # Number of documents to return after re-ranking
    score_threshold: float = 0.0  # Minimum score to include
    normalize_scores: bool = True  # Normalize scores to 0-1 range


class CrossEncoderReranker:
    """
    Cross-encoder based re-ranker for document retrieval.
    
    Cross-encoders provide more accurate relevance scores than bi-encoders
    because they jointly encode the query and document, allowing for
    attention between query and document tokens.
    
    Trade-off: More accurate but slower than bi-encoders.
    Use for re-ranking a small set of candidates (10-20 documents).
    
    Features:
    - State-of-the-art relevance scoring
    - Batch processing for efficiency
    - Score normalization
    - Configurable thresholding
    """
    
    def __init__(self, config: Optional[RerankerConfig] = None):
        """
        Initialize cross-encoder re-ranker.
        
        Args:
            config: Re-ranker configuration
            
        Raises:
            ImportError: If sentence-transformers not installed
        """
        if not CROSS_ENCODER_AVAILABLE:
            raise ImportError(
                "sentence-transformers is required for cross-encoder re-ranking. "
                "Install with: pip install sentence-transformers"
            )
        
        self.config = config or RerankerConfig()
        self.model: Optional[CrossEncoder] = None
        self._initialized = False
    
    def _lazy_load_model(self) -> None:
        """Lazy load the cross-encoder model."""
        if not self._initialized:
            self.model = CrossEncoder(self.config.model_name)
            self._initialized = True
    
    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: Optional[int] = None
    ) -> List[Tuple[Document, float]]:
        """
        Re-rank documents using cross-encoder.
        
        Args:
            query: Search query
            documents: List of candidate documents to re-rank
            top_k: Number of top documents to return (uses config default if None)
            
        Returns:
            List of (document, score) tuples sorted by relevance
        """
        if not documents:
            return []
        
        # Lazy load model
        self._lazy_load_model()
        
        top_k = top_k or self.config.top_k
        
        # Prepare query-document pairs
        pairs = [(query, doc.page_content) for doc in documents]
        
        # Get cross-encoder scores
        scores = self.model.predict(
            pairs,
            batch_size=self.config.batch_size,
            show_progress_bar=False
        )
        
        # Normalize scores if configured
        if self.config.normalize_scores:
            scores = self._normalize_scores(scores)
        
        # Filter by threshold
        filtered_results = [
            (doc, float(score))
            for doc, score in zip(documents, scores)
            if score >= self.config.score_threshold
        ]
        
        # Sort by score
        filtered_results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k
        return filtered_results[:top_k]
    
    def _normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """
        Normalize scores to 0-1 range using min-max normalization.
        
        Args:
            scores: Raw scores from cross-encoder
            
        Returns:
            Normalized scores
        """
        if len(scores) == 0:
            return scores
        
        min_score = scores.min()
        max_score = scores.max()
        
        # Avoid division by zero
        if max_score == min_score:
            return np.ones_like(scores) * 0.5
        
        normalized = (scores - min_score) / (max_score - min_score)
        return normalized
    
    def batch_rerank(
        self,
        queries: List[str],
        document_lists: List[List[Document]],
        top_k: Optional[int] = None
    ) -> List[List[Tuple[Document, float]]]:
        """
        Re-rank multiple query-document sets in batch.
        
        Args:
            queries: List of search queries
            document_lists: List of document lists (one per query)
            top_k: Number of top documents per query
            
        Returns:
            List of re-ranked results (one per query)
        """
        if len(queries) != len(document_lists):
            raise ValueError("Number of queries must match number of document lists")
        
        results = []
        for query, documents in zip(queries, document_lists):
            reranked = self.rerank(query, documents, top_k)
            results.append(reranked)
        
        return results


class FallbackReranker:
    """
    Fallback re-ranker when cross-encoder is not available.
    
    Uses simple heuristics based on:
    - Keyword overlap
    - Document length
    - Metadata signals
    """
    
    def __init__(self, config: Optional[RerankerConfig] = None):
        """Initialize fallback re-ranker."""
        self.config = config or RerankerConfig()
    
    def rerank(
        self,
        query: str,
        documents: List[Document],
        top_k: Optional[int] = None
    ) -> List[Tuple[Document, float]]:
        """
        Re-rank using simple heuristics.
        
        Args:
            query: Search query
            documents: Candidate documents
            top_k: Number of results to return
            
        Returns:
            Re-ranked documents with scores
        """
        top_k = top_k or self.config.top_k
        
        scored_docs = []
        query_terms = set(query.lower().split())
        
        for doc in documents:
            score = self._calculate_heuristic_score(doc, query_terms)
            scored_docs.append((doc, score))
        
        # Sort by score
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        return scored_docs[:top_k]
    
    def _calculate_heuristic_score(
        self,
        doc: Document,
        query_terms: set
    ) -> float:
        """Calculate heuristic relevance score."""
        content = doc.page_content.lower()
        content_terms = set(content.split())
        
        # Keyword overlap (Jaccard similarity)
        overlap = len(query_terms & content_terms)
        union = len(query_terms | content_terms)
        jaccard = overlap / union if union > 0 else 0.0
        
        # Boost for metadata signals
        metadata = doc.metadata
        boost = 1.0
        
        if metadata.get("has_metrics", False):
            boost *= 1.2
        
        if metadata.get("section_type") == "experience":
            boost *= 1.3
        
        return jaccard * boost


def create_reranker(
    config: Optional[RerankerConfig] = None,
    use_fallback: bool = False
) -> CrossEncoderReranker:
    """
    Factory function to create appropriate re-ranker.
    
    Args:
        config: Re-ranker configuration
        use_fallback: Force use of fallback re-ranker
        
    Returns:
        Re-ranker instance (cross-encoder or fallback)
    """
    if use_fallback or not CROSS_ENCODER_AVAILABLE:
        return FallbackReranker(config)
    
    try:
        return CrossEncoderReranker(config)
    except Exception:
        # Fall back if model loading fails
        return FallbackReranker(config)


# Default instance
default_reranker = create_reranker()
