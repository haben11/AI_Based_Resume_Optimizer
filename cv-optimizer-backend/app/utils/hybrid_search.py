"""
Hybrid Search Engine combining Semantic and Keyword Search

Implements hybrid retrieval strategy that combines:
- Semantic search (dense embeddings via ChromaDB)
- Keyword search (sparse BM25 algorithm)
- Reciprocal Rank Fusion (RRF) for result merging

This approach captures both semantic meaning and exact keyword matches,
significantly improving retrieval quality for job-resume matching.

Author: CV Optimizer Team
Version: 2.0.0
"""

import math
from typing import List, Dict, Any, Tuple, Optional, Set
from dataclasses import dataclass
from collections import Counter, defaultdict
import re
from langchain.schema import Document
from langchain_community.vectorstores import Chroma


@dataclass
class BM25Config:
    """Configuration for BM25 algorithm."""
    k1: float = 1.5  # Term frequency saturation parameter
    b: float = 0.75  # Length normalization parameter
    epsilon: float = 0.25  # IDF floor value


@dataclass
class HybridSearchConfig:
    """Configuration for hybrid search."""
    semantic_weight: float = 0.6  # Weight for semantic search (0-1)
    keyword_weight: float = 0.4  # Weight for keyword search (0-1)
    rrf_k: int = 60  # Reciprocal Rank Fusion constant
    min_keyword_score: float = 0.1  # Minimum BM25 score to consider
    enable_query_expansion: bool = True  # Expand query with synonyms
    
    def __post_init__(self):
        """Validate weights sum to 1.0."""
        total = self.semantic_weight + self.keyword_weight
        if not math.isclose(total, 1.0, rel_tol=1e-5):
            raise ValueError(f"Weights must sum to 1.0, got {total}")


class BM25Retriever:
    """
    BM25 (Best Matching 25) keyword-based retrieval.
    
    BM25 is a probabilistic ranking function that scores documents
    based on term frequency and inverse document frequency.
    
    Features:
    - Term frequency saturation (k1 parameter)
    - Document length normalization (b parameter)
    - IDF calculation with smoothing
    - Efficient scoring for large document collections
    """
    
    def __init__(self, config: Optional[BM25Config] = None):
        """
        Initialize BM25 retriever.
        
        Args:
            config: BM25 configuration (uses defaults if not provided)
        """
        self.config = config or BM25Config()
        self.corpus: List[Document] = []
        self.doc_freqs: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0.0
        self.tokenized_corpus: List[List[str]] = []
        
    def index_documents(self, documents: List[Document]) -> None:
        """
        Index documents for BM25 retrieval.
        
        Args:
            documents: List of documents to index
        """
        self.corpus = documents
        self.tokenized_corpus = [self._tokenize(doc.page_content) for doc in documents]
        self.doc_lengths = [len(tokens) for tokens in self.tokenized_corpus]
        self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths) if self.doc_lengths else 0
        
        # Calculate document frequencies
        self.doc_freqs = {}
        for tokens in self.tokenized_corpus:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1
        
        # Calculate IDF scores
        num_docs = len(self.corpus)
        self.idf = {}
        for term, freq in self.doc_freqs.items():
            # IDF with smoothing to avoid division by zero
            idf = math.log((num_docs - freq + 0.5) / (freq + 0.5) + 1)
            self.idf[term] = max(idf, self.config.epsilon)
    
    def search(self, query: str, k: int = 10) -> List[Tuple[Document, float]]:
        """
        Search documents using BM25 scoring.
        
        Args:
            query: Search query
            k: Number of top results to return
            
        Returns:
            List of (document, score) tuples sorted by score
        """
        if not self.corpus:
            return []
        
        query_tokens = self._tokenize(query)
        scores = self._calculate_scores(query_tokens)
        
        # Sort by score and return top k
        scored_docs = [(self.corpus[i], scores[i]) for i in range(len(scores))]
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        return scored_docs[:k]
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into terms.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of lowercase tokens
        """
        # Convert to lowercase and split on non-alphanumeric
        tokens = re.findall(r'\b\w+\b', text.lower())
        
        # Remove very short tokens (likely not meaningful)
        tokens = [t for t in tokens if len(t) > 2]
        
        return tokens
    
    def _calculate_scores(self, query_tokens: List[str]) -> List[float]:
        """
        Calculate BM25 scores for all documents.
        
        Args:
            query_tokens: Tokenized query
            
        Returns:
            List of scores for each document
        """
        scores = [0.0] * len(self.corpus)
        
        for token in query_tokens:
            if token not in self.idf:
                continue
            
            idf_score = self.idf[token]
            
            for doc_idx, doc_tokens in enumerate(self.tokenized_corpus):
                # Term frequency in document
                tf = doc_tokens.count(token)
                
                if tf == 0:
                    continue
                
                # Document length normalization
                doc_length = self.doc_lengths[doc_idx]
                norm_factor = 1 - self.config.b + self.config.b * (doc_length / self.avg_doc_length)
                
                # BM25 score component for this term
                score = idf_score * (tf * (self.config.k1 + 1)) / (tf + self.config.k1 * norm_factor)
                scores[doc_idx] += score
        
        return scores


class HybridSearchEngine:
    """
    Hybrid search engine combining semantic and keyword search.
    
    Uses Reciprocal Rank Fusion (RRF) to merge results from:
    1. Semantic search (ChromaDB with embeddings)
    2. Keyword search (BM25 algorithm)
    
    RRF formula: score(d) = Σ 1 / (k + rank(d))
    where k is a constant (typically 60) and rank is the position in each list.
    """
    
    def __init__(
        self,
        config: Optional[HybridSearchConfig] = None,
        bm25_config: Optional[BM25Config] = None
    ):
        """
        Initialize hybrid search engine.
        
        Args:
            config: Hybrid search configuration
            bm25_config: BM25 configuration
        """
        self.config = config or HybridSearchConfig()
        self.bm25 = BM25Retriever(bm25_config)
        self._indexed = False
    
    def index_documents(self, documents: List[Document]) -> None:
        """
        Index documents for hybrid search.
        
        Args:
            documents: List of documents to index
        """
        self.bm25.index_documents(documents)
        self._indexed = True
    
    def search(
        self,
        vector_db: Chroma,
        query: str,
        k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Perform hybrid search combining semantic and keyword retrieval.
        
        Args:
            vector_db: ChromaDB vector store for semantic search
            query: Search query
            k: Number of results to return
            filter_dict: Optional metadata filters
            
        Returns:
            List of documents ranked by hybrid score
        """
        if not self._indexed:
            raise RuntimeError("Documents must be indexed before searching")
        
        # Expand query if enabled
        if self.config.enable_query_expansion:
            expanded_query = self._expand_query(query)
        else:
            expanded_query = query
        
        # 1. Semantic search
        semantic_results = self._semantic_search(
            vector_db,
            expanded_query,
            k=k * 2,  # Over-fetch for better fusion
            filter_dict=filter_dict
        )
        
        # 2. Keyword search (BM25)
        keyword_results = self.bm25.search(expanded_query, k=k * 2)
        
        # 3. Merge using Reciprocal Rank Fusion
        merged_results = self._reciprocal_rank_fusion(
            semantic_results,
            keyword_results,
            k=k
        )
        
        return merged_results
    
    def _semantic_search(
        self,
        vector_db: Chroma,
        query: str,
        k: int,
        filter_dict: Optional[Dict[str, Any]]
    ) -> List[Tuple[Document, float]]:
        """
        Perform semantic search using vector database.
        
        Args:
            vector_db: ChromaDB instance
            query: Search query
            k: Number of results
            filter_dict: Metadata filters
            
        Returns:
            List of (document, score) tuples
        """
        try:
            results = vector_db.similarity_search_with_relevance_scores(
                query,
                k=k,
                filter=filter_dict
            )
            return results
        except Exception:
            # Fallback if scores not available
            docs = vector_db.similarity_search(query, k=k, filter=filter_dict)
            return [(doc, 1.0 - (i * 0.05)) for i, doc in enumerate(docs)]
    
    def _reciprocal_rank_fusion(
        self,
        semantic_results: List[Tuple[Document, float]],
        keyword_results: List[Tuple[Document, float]],
        k: int
    ) -> List[Document]:
        """
        Merge results using Reciprocal Rank Fusion.
        
        RRF is a simple yet effective method that doesn't require
        score normalization and is robust to different scoring scales.
        
        Args:
            semantic_results: Results from semantic search
            keyword_results: Results from keyword search
            k: Number of final results
            
        Returns:
            Merged and ranked list of documents
        """
        # Create document ID mapping (use page_content hash as ID)
        doc_scores: Dict[int, float] = defaultdict(float)
        doc_map: Dict[int, Document] = {}
        
        # Process semantic results
        for rank, (doc, score) in enumerate(semantic_results, start=1):
            doc_id = hash(doc.page_content)
            doc_map[doc_id] = doc
            
            # RRF score with semantic weight
            rrf_score = self.config.semantic_weight / (self.config.rrf_k + rank)
            doc_scores[doc_id] += rrf_score
        
        # Process keyword results
        for rank, (doc, score) in enumerate(keyword_results, start=1):
            # Filter out low-scoring keyword matches
            if score < self.config.min_keyword_score:
                continue
            
            doc_id = hash(doc.page_content)
            doc_map[doc_id] = doc
            
            # RRF score with keyword weight
            rrf_score = self.config.keyword_weight / (self.config.rrf_k + rank)
            doc_scores[doc_id] += rrf_score
        
        # Sort by combined score
        sorted_doc_ids = sorted(
            doc_scores.keys(),
            key=lambda x: doc_scores[x],
            reverse=True
        )
        
        # Return top k documents
        return [doc_map[doc_id] for doc_id in sorted_doc_ids[:k]]
    
    def _expand_query(self, query: str) -> str:
        """
        Expand query with synonyms and related terms.
        
        Args:
            query: Original query
            
        Returns:
            Expanded query string
        """
        # Simple synonym expansion (could be enhanced with word embeddings)
        synonym_map = {
            "experience": ["background", "history", "expertise", "track record"],
            "skills": ["competencies", "abilities", "proficiencies", "capabilities"],
            "manage": ["lead", "oversee", "direct", "supervise"],
            "develop": ["build", "create", "design", "implement"],
            "improve": ["enhance", "optimize", "increase", "boost"],
            "responsible": ["accountable", "in charge", "overseeing"],
            "team": ["group", "squad", "crew", "unit"],
            "project": ["initiative", "program", "effort"],
            "senior": ["experienced", "advanced", "principal"],
            "junior": ["entry-level", "associate", "beginner"]
        }
        
        expanded_terms = [query]
        query_lower = query.lower()
        
        for term, synonyms in synonym_map.items():
            if term in query_lower:
                # Add first 2 synonyms to avoid query bloat
                expanded_terms.extend(synonyms[:2])
        
        return " ".join(expanded_terms)


# Singleton instance with default configuration
hybrid_search_engine = HybridSearchEngine()
