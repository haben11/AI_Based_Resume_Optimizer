"""
Enhanced Retriever with Re-ranking and Relevance Filtering

This module provides advanced retrieval capabilities including:
- Relevance score thresholding
- Re-ranking based on multiple signals
- Diversity optimization (MMR-like)
- Query expansion

Author: CV Optimizer Team
Version: 1.0.0
"""

from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
import re
from langchain.schema import Document
from langchain_community.vectorstores import Chroma


@dataclass
class RetrievalConfig:
    """Configuration for retrieval behavior."""
    initial_k: int = 10  # Initial number of candidates to retrieve
    final_k: int = 5  # Final number of chunks to return
    relevance_threshold: float = 0.7  # Minimum similarity score (0-1)
    diversity_lambda: float = 0.3  # Balance between relevance and diversity (0-1)
    boost_metrics: float = 1.2  # Score multiplier for chunks with metrics
    boost_dates: float = 1.1  # Score multiplier for chunks with dates
    section_weights: Dict[str, float] = None  # Weight by section type
    
    def __post_init__(self):
        """Set default section weights if not provided."""
        if self.section_weights is None:
            self.section_weights = {
                "experience": 1.5,  # Prioritize experience
                "skills": 1.3,  # Skills are important
                "projects": 1.2,  # Projects show practical application
                "summary": 1.1,  # Summary provides context
                "education": 1.0,  # Standard weight
                "certifications": 1.0,
                "achievements": 1.1,
                "header": 0.8,  # Lower priority
                "unknown": 0.9
            }


@dataclass
class ScoredDocument:
    """Document with relevance score and metadata."""
    document: Document
    base_score: float
    adjusted_score: float
    rank: int
    
    def __lt__(self, other):
        """Enable sorting by adjusted score."""
        return self.adjusted_score < other.adjusted_score


class EnhancedRetriever:
    """
    Advanced retriever with re-ranking and filtering capabilities.
    
    Features:
    - Multi-stage retrieval (over-fetch then re-rank)
    - Relevance score thresholding
    - Metadata-based score boosting
    - Diversity optimization
    - Query expansion
    """
    
    def __init__(self, config: Optional[RetrievalConfig] = None):
        """
        Initialize the enhanced retriever.
        
        Args:
            config: Retrieval configuration (uses defaults if not provided)
        """
        self.config = config or RetrievalConfig()
    
    def retrieve(
        self,
        vector_db: Chroma,
        query: str,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Retrieve and re-rank documents from vector database.
        
        Args:
            vector_db: ChromaDB vector store
            query: Search query (typically job description)
            filter_dict: Optional metadata filters
            
        Returns:
            List of top-k most relevant documents after re-ranking
        """
        # Step 1: Expand query with key terms
        expanded_query = self._expand_query(query)
        
        # Step 2: Initial retrieval with over-fetching
        candidates = self._initial_retrieval(
            vector_db,
            expanded_query,
            filter_dict
        )
        
        if not candidates:
            # Fallback: try original query if expansion failed
            candidates = self._initial_retrieval(
                vector_db,
                query,
                filter_dict
            )
        
        # Step 3: Filter by relevance threshold
        filtered_candidates = self._filter_by_relevance(candidates)
        
        # Step 4: Re-rank based on metadata signals
        reranked_candidates = self._rerank_documents(filtered_candidates, query)
        
        # Step 5: Apply diversity optimization
        final_documents = self._optimize_diversity(
            reranked_candidates,
            self.config.final_k
        )
        
        return final_documents
    
    def _expand_query(self, query: str) -> str:
        """
        Expand query with extracted key terms and synonyms.
        
        Args:
            query: Original query text
            
        Returns:
            Expanded query string
        """
        # Extract key technical terms, skills, and requirements
        # This is a simple implementation; could be enhanced with NLP
        
        # Extract capitalized terms (likely important)
        key_terms = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', query)
        
        # Extract acronyms
        acronyms = re.findall(r'\b[A-Z]{2,}\b', query)
        
        # Extract technical terms
        technical = re.findall(
            r'\b[A-Za-z]+[0-9]+[A-Za-z0-9]*\b|\b[A-Za-z]+\.[A-Za-z]+\b',
            query
        )
        
        # Extract quoted phrases (explicit requirements)
        quoted = re.findall(r'"([^"]+)"', query)
        
        # Combine all extracted terms
        expanded_terms = set(key_terms + acronyms + technical + quoted)
        
        # Add common synonyms for key terms (simple mapping)
        synonym_map = {
            "experience": ["background", "history", "expertise"],
            "skills": ["competencies", "abilities", "proficiencies"],
            "manage": ["lead", "oversee", "direct"],
            "develop": ["build", "create", "design"],
            "improve": ["enhance", "optimize", "increase"]
        }
        
        expanded = [query]  # Start with original query
        
        for term in expanded_terms:
            term_lower = term.lower()
            if term_lower in synonym_map:
                expanded.extend(synonym_map[term_lower])
        
        return " ".join(expanded)
    
    def _initial_retrieval(
        self,
        vector_db: Chroma,
        query: str,
        filter_dict: Optional[Dict[str, Any]]
    ) -> List[Tuple[Document, float]]:
        """
        Perform initial retrieval with similarity scores.
        
        Args:
            vector_db: Vector database
            query: Search query
            filter_dict: Metadata filters
            
        Returns:
            List of (document, score) tuples
        """
        try:
            # Retrieve with scores
            results = vector_db.similarity_search_with_relevance_scores(
                query,
                k=self.config.initial_k,
                filter=filter_dict
            )
            return results
        except Exception as e:
            # Fallback to regular similarity search if scores not available
            docs = vector_db.similarity_search(
                query,
                k=self.config.initial_k,
                filter=filter_dict
            )
            # Assign dummy scores (decreasing by rank)
            return [(doc, 1.0 - (i * 0.05)) for i, doc in enumerate(docs)]
    
    def _filter_by_relevance(
        self,
        candidates: List[Tuple[Document, float]]
    ) -> List[Tuple[Document, float]]:
        """
        Filter candidates by relevance threshold.
        
        Args:
            candidates: List of (document, score) tuples
            
        Returns:
            Filtered list of candidates above threshold
        """
        filtered = [
            (doc, score) for doc, score in candidates
            if score >= self.config.relevance_threshold
        ]
        
        # If filtering is too aggressive, relax threshold
        if len(filtered) < 3 and len(candidates) >= 3:
            # Take top 3 regardless of threshold
            sorted_candidates = sorted(
                candidates,
                key=lambda x: x[1],
                reverse=True
            )
            filtered = sorted_candidates[:3]
        
        return filtered
    
    def _rerank_documents(
        self,
        candidates: List[Tuple[Document, float]],
        query: str
    ) -> List[ScoredDocument]:
        """
        Re-rank documents based on metadata signals.
        
        Args:
            candidates: List of (document, score) tuples
            query: Original query for keyword matching
            
        Returns:
            List of ScoredDocument objects sorted by adjusted score
        """
        scored_docs = []
        query_lower = query.lower()
        
        for doc, base_score in candidates:
            adjusted_score = base_score
            metadata = doc.metadata
            
            # Boost 1: Section type weight
            section_type = metadata.get("section_type", "unknown")
            section_weight = self.config.section_weights.get(section_type, 1.0)
            adjusted_score *= section_weight
            
            # Boost 2: Has metrics (quantifiable achievements)
            if metadata.get("has_metrics", False):
                adjusted_score *= self.config.boost_metrics
            
            # Boost 3: Has dates (temporal context)
            if metadata.get("has_dates", False):
                adjusted_score *= self.config.boost_dates
            
            # Boost 4: Keyword overlap with query
            keywords = metadata.get("keywords", [])
            keyword_overlap = sum(
                1 for kw in keywords
                if kw.lower() in query_lower
            )
            if keyword_overlap > 0:
                # Boost by 5% per matching keyword, max 30%
                keyword_boost = min(1.0 + (keyword_overlap * 0.05), 1.3)
                adjusted_score *= keyword_boost
            
            scored_docs.append(ScoredDocument(
                document=doc,
                base_score=base_score,
                adjusted_score=adjusted_score,
                rank=0  # Will be set after sorting
            ))
        
        # Sort by adjusted score
        scored_docs.sort(key=lambda x: x.adjusted_score, reverse=True)
        
        # Update ranks
        for i, scored_doc in enumerate(scored_docs):
            scored_doc.rank = i + 1
        
        return scored_docs
    
    def _optimize_diversity(
        self,
        scored_docs: List[ScoredDocument],
        k: int
    ) -> List[Document]:
        """
        Select diverse set of documents using MMR-like approach.
        
        Maximal Marginal Relevance balances relevance with diversity
        to avoid redundant information.
        
        Args:
            scored_docs: Ranked documents with scores
            k: Number of documents to select
            
        Returns:
            List of k diverse documents
        """
        if len(scored_docs) <= k:
            return [sd.document for sd in scored_docs]
        
        selected = []
        remaining = scored_docs.copy()
        
        # Always select the top-ranked document first
        selected.append(remaining.pop(0))
        
        # Select remaining documents balancing relevance and diversity
        while len(selected) < k and remaining:
            best_score = -1
            best_idx = 0
            
            for i, candidate in enumerate(remaining):
                # Relevance component (normalized)
                relevance = candidate.adjusted_score
                
                # Diversity component: penalize similarity to already selected
                diversity_penalty = self._calculate_diversity_penalty(
                    candidate.document,
                    [sd.document for sd in selected]
                )
                
                # Combined score using lambda parameter
                combined_score = (
                    self.config.diversity_lambda * relevance +
                    (1 - self.config.diversity_lambda) * diversity_penalty
                )
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_idx = i
            
            selected.append(remaining.pop(best_idx))
        
        return [sd.document for sd in selected]
    
    def _calculate_diversity_penalty(
        self,
        candidate: Document,
        selected: List[Document]
    ) -> float:
        """
        Calculate diversity penalty based on section overlap.
        
        Args:
            candidate: Candidate document
            selected: Already selected documents
            
        Returns:
            Diversity score (higher is more diverse)
        """
        candidate_section = candidate.metadata.get("section_type", "unknown")
        
        # Count how many selected docs are from the same section
        same_section_count = sum(
            1 for doc in selected
            if doc.metadata.get("section_type") == candidate_section
        )
        
        # Penalize if many docs from same section already selected
        # Returns value between 0 (not diverse) and 1 (very diverse)
        diversity_score = 1.0 / (1.0 + same_section_count)
        
        return diversity_score


# Singleton instance with default configuration
enhanced_retriever = EnhancedRetriever()
