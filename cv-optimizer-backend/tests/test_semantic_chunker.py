"""
Unit tests for Semantic Chunker

Tests semantic chunking functionality including:
- Section identification
- Metadata extraction
- Chunk size constraints
- Sentence boundary preservation
"""

import pytest
from app.utils.semantic_chunker import SemanticChunker, SectionType


class TestSemanticChunker:
    """Test suite for SemanticChunker class."""
    
    @pytest.fixture
    def chunker(self):
        """Create a SemanticChunker instance for testing."""
        return SemanticChunker(max_chunk_size=500)
    
    @pytest.fixture
    def sample_resume(self):
        """Sample resume text for testing."""
        return """# John Doe

## Professional Summary
Experienced software engineer with 10+ years in full-stack development.
Specialized in Python, React, and cloud architecture.

## Professional Experience

### Senior Software Engineer | Tech Corp | 2020-Present
- Led development of microservices architecture serving 1M+ users
- Improved system performance by 40% through optimization
- Mentored team of 5 junior developers

### Software Engineer | StartupCo | 2018-2020
- Built RESTful APIs using Python and FastAPI
- Reduced deployment time by 60% with CI/CD automation
- Collaborated with cross-functional teams

## Skills
Python, JavaScript, React, Docker, Kubernetes, AWS, PostgreSQL, MongoDB

## Education
B.S. Computer Science | University of Technology | 2018
"""
    
    def test_chunk_resume_creates_documents(self, chunker, sample_resume):
        """Test that chunking creates Document objects."""
        documents = chunker.chunk_resume(sample_resume, "test-resume-id")
        
        assert len(documents) > 0
        assert all(hasattr(doc, 'page_content') for doc in documents)
        assert all(hasattr(doc, 'metadata') for doc in documents)
    
    def test_section_identification(self, chunker, sample_resume):
        """Test that sections are correctly identified."""
        documents = chunker.chunk_resume(sample_resume, "test-resume-id")
        
        section_types = [doc.metadata['section_type'] for doc in documents]
        
        # Should identify at least summary, experience, skills, education
        assert 'summary' in section_types or 'header' in section_types
        assert 'experience' in section_types
        assert 'skills' in section_types
        assert 'education' in section_types
    
    def test_metadata_enrichment(self, chunker, sample_resume):
        """Test that chunks have rich metadata."""
        documents = chunker.chunk_resume(sample_resume, "test-resume-id")
        
        for doc in documents:
            metadata = doc.metadata
            
            # Check required metadata fields
            assert 'section_type' in metadata
            assert 'section_title' in metadata
            assert 'chunk_index' in metadata
            assert 'total_chunks' in metadata
            assert 'char_count' in metadata
            assert 'has_dates' in metadata
            assert 'has_metrics' in metadata
            assert 'keywords' in metadata
            assert 'source' in metadata
    
    def test_date_detection(self, chunker):
        """Test that dates are correctly detected in metadata."""
        text_with_dates = """## Experience
Senior Engineer | 2020-2023
Worked on various projects from Jan 2020 to Dec 2023."""
        
        documents = chunker.chunk_resume(text_with_dates, "test-id")
        
        # At least one chunk should have dates
        assert any(doc.metadata['has_dates'] for doc in documents)
    
    def test_metrics_detection(self, chunker):
        """Test that metrics are correctly detected in metadata."""
        text_with_metrics = """## Achievements
- Increased revenue by 45%
- Reduced costs by $2.5M
- Improved performance 3x faster"""
        
        documents = chunker.chunk_resume(text_with_metrics, "test-id")
        
        # At least one chunk should have metrics
        assert any(doc.metadata['has_metrics'] for doc in documents)
    
    def test_keyword_extraction(self, chunker):
        """Test that keywords are extracted from content."""
        text = """## Skills
Python, JavaScript, AWS, Docker, Kubernetes, PostgreSQL"""
        
        documents = chunker.chunk_resume(text, "test-id")
        
        # Should extract technical keywords
        keywords = documents[0].metadata['keywords']
        assert len(keywords) > 0
        assert any('Python' in kw or 'AWS' in kw for kw in keywords)
    
    def test_chunk_size_constraints(self, chunker, sample_resume):
        """Test that chunks respect size constraints."""
        documents = chunker.chunk_resume(sample_resume, "test-id")
        
        for doc in documents:
            # No chunk should exceed max size
            assert len(doc.page_content) <= chunker.max_chunk_size
            # Metadata should reflect actual size
            assert doc.metadata['char_count'] == len(doc.page_content)
    
    def test_sentence_boundary_preservation(self, chunker):
        """Test that chunks don't split mid-sentence."""
        long_text = """## Summary
This is a very long sentence that should not be split in the middle because that would break semantic meaning. """ * 10
        
        documents = chunker.chunk_resume(long_text, "test-id")
        
        for doc in documents:
            content = doc.page_content.strip()
            # Should end with sentence-ending punctuation or be complete
            if len(content) > 0:
                # Either ends with punctuation or is the last chunk
                assert content[-1] in '.!?' or doc.metadata['chunk_index'] == doc.metadata['total_chunks'] - 1
    
    def test_empty_resume_handling(self, chunker):
        """Test handling of empty or minimal resume."""
        empty_resume = ""
        documents = chunker.chunk_resume(empty_resume, "test-id")
        
        # Should handle gracefully, possibly returning empty list or single chunk
        assert isinstance(documents, list)
    
    def test_resume_id_in_metadata(self, chunker, sample_resume):
        """Test that resume_id is included in metadata."""
        resume_id = "unique-test-id-123"
        documents = chunker.chunk_resume(sample_resume, resume_id)
        
        for doc in documents:
            assert doc.metadata['source'] == resume_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
