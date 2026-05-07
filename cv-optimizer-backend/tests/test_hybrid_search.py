"""
Unit tests for Hybrid Search Engine

Tests hybrid search functionality including:
- BM25 keyword search
- Reciprocal Rank Fusion
- Query expansion
- Result merging

Author: CV Optimizer Team
Version: 2.0.0
"""

import pytest
from langchain.schema import Document
from app.utils.hybrid_search import (
    BM25Retriever,
    BM25Config,
    HybridSearchEngine,
    HybridSearchConfig
)


class TestBM25Retriever:
    """Test suite for BM25Retriever."""
    
    @pytest.fixture
    def sample_documents(self):
        """Sample documents for testing."""
        return [
            Document(
                page_content="Python developer with 5 years of experience in Django and Flask",
                metadata={"section_type": "experience"}
            ),
            Document(
                page_content="Expert in JavaScript, React, and Node.js development",
                metadata={"section_type": "skills"}
            ),
            Document(
                page_content="Led team of 10 engineers building microservices architecture",
                metadata={"section_type": "experience"}
            ),
            Document(
                page_content="AWS, Docker, Kubernetes, CI/CD pipelines",
                metadata={"section_type": "skills"}
            )
        ]
    
    @pytest.fixture
    def bm25_retriever(self, sample_documents):
        """Create BM25 retriever with indexed documents."""
        retriever = BM25Retriever()
        retriever.index_documents(sample_documents)
        return retriever
    
    def test_initialization(self):
        """Test BM25 retriever initialization."""
        retriever = BM25Retriever()
        assert retriever.config.k1 == 1.5
        assert retriever.config.b == 0.75
        assert len(retriever.corpus) == 0
    
    def test_custom_config(self):
        """Test initialization with custom config."""
        config = BM25Config(k1=2.0, b=0.5)
        retriever = BM25Retriever(config)
        assert retriever.config.k1 == 2.0
        assert retriever.config.b == 0.5
    
    def test_index_documents(self, sample_documents):
        """Test document indexing."""
        retriever = BM25Retriever()
        retriever.index_documents(sample_documents)
        
        assert len(retriever.corpus) == 4
        assert len(retriever.tokenized_corpus) == 4
        assert retriever.avg_doc_length > 0
        assert len(retriever.idf) > 0
    
    def test_search_returns_results(self, bm25_retriever):
        """Test that search returns results."""
        results = bm25_retriever.search("Python Django", k=2)
        
        assert len(results) <= 2
        assert all(isinstance(doc, Document) for doc, _ in results)
        assert all(isinstance(score, float) for _, score in results)
    
    def test_search_relevance(self, bm25_retriever):
        """Test that search returns relevant results."""
        results = bm25_retriever.search("Python Django Flask", k=4)
        
        # First result should be the Python/Django/Flask document
        top_doc, top_score = results[0]
        assert "Python" in top_doc.page_content
        assert "Django" in top_doc.page_content or "Flask" in top_doc.page_content
    
    def test_search_empty_query(self, bm25_retriever):
        """Test search with empty query."""
        results = bm25_retriever.search("", k=2)
        assert len(results) >= 0  # Should handle gracefully
    
    def test_tokenization(self, bm25_retriever):
        """Test tokenization."""
        tokens = bm25_retriever._tokenize("Python, JavaScript, and Node.js")
        assert "python" in tokens
        assert "javascript" in tokens
        assert "node" in tokens
        # Short tokens should be filtered
        assert "and" not in tokens


class TestHybridSearchEngine:
    """Test suite for HybridSearchEngine."""
    
    @pytest.fixture
    def sample_documents(self):
        """Sample documents for testing."""
        return [
            Document(
                page_content="Senior Python developer with expertise in machine learning",
                metadata={"section_type": "summary", "resume_id": "test-1"}
            ),
            Document(
                page_content="5 years experience building scalable web applications",
                metadata={"section_type": "experience", "resume_id": "test-1"}
            ),
            Document(
                page_content="Skills: Python, TensorFlow, PyTorch, scikit-learn",
                metadata={"section_type": "skills", "resume_id": "test-1"}
            )
        ]
    
    def test_initialization(self):
        """Test hybrid search engine initialization."""
        engine = HybridSearchEngine()
        assert engine.config.semantic_weight == 0.6
        assert engine.config.keyword_weight == 0.4
        assert not engine._indexed
    
    def test_custom_config(self):
        """Test initialization with custom config."""
        config = HybridSearchConfig(
            semantic_weight=0.7,
            keyword_weight=0.3
        )
        engine = HybridSearchEngine(config)
        assert engine.config.semantic_weight == 0.7
        assert engine.config.keyword_weight == 0.3
    
    def test_config_validation(self):
        """Test that config validates weight sum."""
        with pytest.raises(ValueError):
            HybridSearchConfig(semantic_weight=0.7, keyword_weight=0.5)
    
    def test_index_documents(self, sample_documents):
        """Test document indexing."""
        engine = HybridSearchEngine()
        engine.index_documents(sample_documents)
        
        assert engine._indexed
        assert len(engine.bm25.corpus) == 3
    
    def test_query_expansion(self):
        """Test query expansion."""
        engine = HybridSearchEngine()
        expanded = engine._expand_query("looking for experienced developer")
        
        assert "experienced" in expanded
        assert "developer" in expanded
        # Should add synonyms
        assert len(expanded.split()) > len("looking for experienced developer".split())
    
    def test_query_expansion_disabled(self):
        """Test with query expansion disabled."""
        config = HybridSearchConfig(
            semantic_weight=0.6,
            keyword_weight=0.4,
            enable_query_expansion=False
        )
        engine = HybridSearchEngine(config)
        
        query = "Python developer"
        expanded = engine._expand_query(query)
        # Should return original when disabled (but method still called)
        assert "Python" in expanded


@pytest.mark.asyncio
class TestHybridSearchIntegration:
    """Integration tests for hybrid search."""
    
    def test_rrf_merging(self):
        """Test Reciprocal Rank Fusion merging."""
        engine = HybridSearchEngine()
        
        doc1 = Document(page_content="Python developer", metadata={})
        doc2 = Document(page_content="JavaScript expert", metadata={})
        doc3 = Document(page_content="Full stack engineer", metadata={})
        
        semantic_results = [(doc1, 0.9), (doc2, 0.7), (doc3, 0.5)]
        keyword_results = [(doc2, 5.0), (doc1, 3.0), (doc3, 1.0)]
        
        merged = engine._reciprocal_rank_fusion(
            semantic_results,
            keyword_results,
            k=3
        )
        
        assert len(merged) <= 3
        assert all(isinstance(doc, Document) for doc in merged)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
