"""
Tests for Phase 3 RAG Service

Tests integration of all Phase 3 ML components.

Author: CV Optimizer Team
Version: 3.0.0
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from langchain.schema import Document
from app.services.rag_service_v3 import RAGServiceV3, create_rag_service_v3
from app.core.rag_config import RAGPipelineConfig
from app.ml.feedback_loop import FeedbackType


@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock()


@pytest.fixture
def rag_service_v3(mock_db):
    """Create RAG service v3 instance for testing."""
    with patch('app.services.rag_service_v3.GoogleGenerativeAIEmbeddings'), \
         patch('app.services.rag_service_v3.ChatGoogleGenerativeAI'), \
         patch('app.services.rag_service_v3.get_vector_store_manager'), \
         patch('app.services.rag_service_v3.HybridSearchEngine'), \
         patch('app.services.rag_service_v3.create_reranker'), \
         patch('app.services.rag_service_v3.create_multi_vector_system'), \
         patch('app.services.rag_service_v3.get_hallucination_detector'), \
         patch('app.services.rag_service_v3.create_feedback_loop'):
        
        service = RAGServiceV3(
            db=mock_db,
            use_fine_tuned_embeddings=False,
            enable_multi_vector=True,
            enable_hallucination_detection=True,
            enable_feedback_loop=True,
            enable_ab_testing=False
        )
        
        return service


class TestRAGServiceV3Initialization:
    """Test RAG service v3 initialization."""
    
    def test_initialization_with_defaults(self, mock_db):
        """Test initialization with default configuration."""
        with patch('app.services.rag_service_v3.GoogleGenerativeAIEmbeddings'), \
             patch('app.services.rag_service_v3.ChatGoogleGenerativeAI'), \
             patch('app.services.rag_service_v3.get_vector_store_manager'), \
             patch('app.services.rag_service_v3.HybridSearchEngine'), \
             patch('app.services.rag_service_v3.create_reranker'), \
             patch('app.services.rag_service_v3.create_multi_vector_system'), \
             patch('app.services.rag_service_v3.get_hallucination_detector'), \
             patch('app.services.rag_service_v3.create_feedback_loop'):
            
            service = RAGServiceV3(db=mock_db)
            
            assert service.config is not None
            assert service.enable_multi_vector is True
            assert service.enable_hallucination_detection is True
            assert service.enable_feedback_loop is True
    
    def test_initialization_with_custom_config(self, mock_db):
        """Test initialization with custom configuration."""
        config = RAGPipelineConfig(
            retrieval={"initial_k": 15, "final_k": 7}
        )
        
        with patch('app.services.rag_service_v3.GoogleGenerativeAIEmbeddings'), \
             patch('app.services.rag_service_v3.ChatGoogleGenerativeAI'), \
             patch('app.services.rag_service_v3.get_vector_store_manager'), \
             patch('app.services.rag_service_v3.HybridSearchEngine'), \
             patch('app.services.rag_service_v3.create_reranker'), \
             patch('app.services.rag_service_v3.create_multi_vector_system'), \
             patch('app.services.rag_service_v3.get_hallucination_detector'), \
             patch('app.services.rag_service_v3.create_feedback_loop'):
            
            service = RAGServiceV3(config=config, db=mock_db)
            
            assert service.config.retrieval.initial_k == 15
            assert service.config.retrieval.final_k == 7
    
    def test_feature_flags(self, mock_db):
        """Test feature flag configuration."""
        with patch('app.services.rag_service_v3.GoogleGenerativeAIEmbeddings'), \
             patch('app.services.rag_service_v3.ChatGoogleGenerativeAI'), \
             patch('app.services.rag_service_v3.get_vector_store_manager'), \
             patch('app.services.rag_service_v3.HybridSearchEngine'), \
             patch('app.services.rag_service_v3.create_reranker'):
            
            service = RAGServiceV3(
                db=mock_db,
                enable_multi_vector=False,
                enable_hallucination_detection=False,
                enable_feedback_loop=False
            )
            
            assert service.enable_multi_vector is False
            assert service.enable_hallucination_detection is False
            assert service.enable_feedback_loop is False


class TestResumeProcessing:
    """Test resume processing with Phase 3 enhancements."""
    
    @pytest.mark.asyncio
    async def test_process_resume_basic(self, rag_service_v3):
        """Test basic resume processing."""
        resume_text = """
        John Doe
        Software Engineer
        
        Experience:
        - Developed Python applications
        - Led team of 5 engineers
        
        Skills: Python, JavaScript, AWS
        """
        
        # Mock semantic chunker
        mock_documents = [
            Document(
                page_content="John Doe, Software Engineer",
                metadata={"section_type": "header", "resume_id": "test123"}
            ),
            Document(
                page_content="Developed Python applications. Led team of 5 engineers.",
                metadata={"section_type": "experience", "resume_id": "test123"}
            )
        ]
        
        with patch('app.services.rag_service_v3.semantic_chunker') as mock_chunker:
            mock_chunker.chunk_resume.return_value = mock_documents
            
            result = await rag_service_v3.process_resume(resume_text, "test123")
            
            assert result == "test123"
            mock_chunker.chunk_resume.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_resume_with_multi_vector(self, rag_service_v3):
        """Test resume processing with multi-vector embeddings."""
        resume_text = "Test resume content"
        
        mock_documents = [
            Document(
                page_content="Test content",
                metadata={"section_type": "skills", "resume_id": "test123"}
            )
        ]
        
        mock_mv_doc = Mock()
        mock_mv_doc.content = "Test content"
        mock_mv_doc.metadata = {"section_type": "skills"}
        
        with patch('app.services.rag_service_v3.semantic_chunker') as mock_chunker:
            mock_chunker.chunk_resume.return_value = mock_documents
            rag_service_v3.multi_vector_system.create_multi_vector_document.return_value = mock_mv_doc
            rag_service_v3.multi_vector_system.get_aspect_statistics.return_value = {
                "total_documents": 1
            }
            
            result = await rag_service_v3.process_resume(resume_text, "test123")
            
            assert result == "test123"
            assert "test123" in rag_service_v3.multi_vector_docs
            assert len(rag_service_v3.multi_vector_docs["test123"]) == 1


class TestCVOptimization:
    """Test CV optimization with Phase 3 enhancements."""
    
    @pytest.mark.asyncio
    async def test_optimize_cv_with_multi_vector(self, rag_service_v3):
        """Test CV optimization using multi-vector retrieval."""
        resume_id = "test123"
        job_description = "Looking for Python developer with 5 years experience"
        
        # Setup multi-vector documents
        mock_mv_doc = Mock()
        mock_mv_doc.content = "Python developer with 5 years experience"
        mock_mv_doc.metadata = {"section_type": "experience"}
        
        rag_service_v3.multi_vector_docs[resume_id] = [mock_mv_doc]
        
        # Mock query processor
        mock_processed_query = Mock()
        mock_processed_query.enhanced_query = job_description
        mock_processed_query.requirements = []
        mock_processed_query.key_skills = ["Python"]
        mock_processed_query.experience_years = 5
        
        # Mock multi-vector retrieval
        mock_doc = Document(
            page_content="Python developer with 5 years experience",
            metadata={"section_type": "experience"}
        )
        
        rag_service_v3.multi_vector_system.retrieve_with_multi_vector.return_value = [
            (mock_mv_doc, 0.95)
        ]
        rag_service_v3.multi_vector_system.classify_query_type.return_value = "skills_query"
        
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = "# John Doe\n\n## Professional Summary\nExperienced Python developer..."
        
        # Mock validation
        mock_validation = Mock()
        mock_validation.is_valid = True
        mock_validation.score = 85.0
        mock_validation.issues = []
        
        # Mock hallucination detection
        mock_hallucination = Mock()
        mock_hallucination.is_trustworthy = True
        mock_hallucination.confidence = 0.95
        mock_hallucination.hallucination_score = 0.05
        mock_hallucination.findings = []
        
        with patch('app.services.rag_service_v3.query_processor') as mock_qp, \
             patch('app.services.rag_service_v3.output_validator') as mock_validator, \
             patch.object(rag_service_v3.llm, 'ainvoke', new_callable=AsyncMock) as mock_llm:
            
            mock_qp.process.return_value = mock_processed_query
            mock_validator.validate.return_value = mock_validation
            rag_service_v3.hallucination_detector.detect_hallucinations = AsyncMock(
                return_value=mock_hallucination
            )
            mock_llm.return_value = mock_response
            
            result = await rag_service_v3.optimize_cv(
                resume_id=resume_id,
                job_description=job_description,
                original_resume_text="Original resume"
            )
            
            assert "optimized_content" in result
            assert "validation" in result
            assert "hallucination_check" in result
            assert result["validation"]["is_valid"] is True
            assert result["hallucination_check"]["is_trustworthy"] is True
    
    @pytest.mark.asyncio
    async def test_optimize_cv_with_hybrid_retrieval(self, rag_service_v3):
        """Test CV optimization using hybrid retrieval."""
        resume_id = "test456"
        job_description = "Senior software engineer position"
        
        # No multi-vector docs for this resume
        rag_service_v3.multi_vector_docs = {}
        
        # Mock query processor
        mock_processed_query = Mock()
        mock_processed_query.enhanced_query = job_description
        mock_processed_query.requirements = []
        mock_processed_query.key_skills = []
        mock_processed_query.experience_years = None
        
        # Mock hybrid search
        mock_doc = Document(
            page_content="Senior software engineer with expertise",
            metadata={"section_type": "experience"}
        )
        
        rag_service_v3.vector_store_manager.get_vector_store.return_value = Mock()
        rag_service_v3.hybrid_search.search.return_value = [mock_doc]
        rag_service_v3.reranker.rerank.return_value = [(mock_doc, 0.90)]
        
        # Mock LLM response
        mock_response = Mock()
        mock_response.content = "# Jane Smith\n\n## Professional Summary\nSenior engineer..."
        
        # Mock validation
        mock_validation = Mock()
        mock_validation.is_valid = True
        mock_validation.score = 80.0
        mock_validation.issues = []
        
        with patch('app.services.rag_service_v3.query_processor') as mock_qp, \
             patch('app.services.rag_service_v3.output_validator') as mock_validator, \
             patch.object(rag_service_v3.llm, 'ainvoke', new_callable=AsyncMock) as mock_llm:
            
            mock_qp.process.return_value = mock_processed_query
            mock_validator.validate.return_value = mock_validation
            mock_llm.return_value = mock_response
            
            result = await rag_service_v3.optimize_cv(
                resume_id=resume_id,
                job_description=job_description
            )
            
            assert "optimized_content" in result
            assert result["validation"]["is_valid"] is True


class TestHallucinationDetection:
    """Test hallucination detection integration."""
    
    @pytest.mark.asyncio
    async def test_hallucination_detection_enabled(self, rag_service_v3):
        """Test hallucination detection when enabled."""
        resume_id = "test123"
        job_description = "Test job"
        original_resume = "Original content"
        
        # Setup mocks
        mock_processed_query = Mock()
        mock_processed_query.enhanced_query = job_description
        mock_processed_query.requirements = []
        mock_processed_query.key_skills = []
        
        mock_doc = Document(page_content="Test", metadata={})
        mock_response = Mock()
        mock_response.content = "Generated resume"
        
        mock_validation = Mock()
        mock_validation.is_valid = True
        mock_validation.score = 85.0
        mock_validation.issues = []
        
        mock_hallucination = Mock()
        mock_hallucination.is_trustworthy = False
        mock_hallucination.confidence = 0.70
        mock_hallucination.hallucination_score = 0.30
        mock_hallucination.findings = [
            Mock(
                type=Mock(value="fabricated_company"),
                severity=0.9,
                location="experience",
                claim="Worked at FakeCompany Inc",
                evidence="Company not in original",
                suggestion="Remove"
            )
        ]
        
        rag_service_v3.multi_vector_docs = {}
        rag_service_v3.vector_store_manager.get_vector_store.return_value = Mock()
        rag_service_v3.hybrid_search.search.return_value = [mock_doc]
        rag_service_v3.reranker.rerank.return_value = [(mock_doc, 0.90)]
        
        with patch('app.services.rag_service_v3.query_processor') as mock_qp, \
             patch('app.services.rag_service_v3.output_validator') as mock_validator, \
             patch.object(rag_service_v3.llm, 'ainvoke', new_callable=AsyncMock) as mock_llm:
            
            mock_qp.process.return_value = mock_processed_query
            mock_validator.validate.return_value = mock_validation
            mock_llm.return_value = mock_response
            rag_service_v3.hallucination_detector.detect_hallucinations = AsyncMock(
                return_value=mock_hallucination
            )
            
            result = await rag_service_v3.optimize_cv(
                resume_id=resume_id,
                job_description=job_description,
                original_resume_text=original_resume
            )
            
            assert result["hallucination_check"] is not None
            assert result["hallucination_check"]["is_trustworthy"] is False
            assert len(result["hallucination_check"]["findings"]) == 1
            assert result["hallucination_check"]["findings"][0]["type"] == "fabricated_company"


class TestFeedbackLoop:
    """Test feedback loop integration."""
    
    def test_record_feedback(self, rag_service_v3):
        """Test recording user feedback."""
        rag_service_v3.feedback_loop.record_feedback = Mock()
        rag_service_v3.feedback_loop.should_trigger_retraining = Mock(return_value=False)
        
        rag_service_v3.record_feedback(
            user_id="user123",
            resume_id="resume456",
            optimization_id="opt789",
            feedback_type=FeedbackType.DOWNLOAD,
            value=1.0
        )
        
        rag_service_v3.feedback_loop.record_feedback.assert_called_once()
    
    def test_feedback_triggers_retraining(self, rag_service_v3):
        """Test feedback triggering retraining recommendation."""
        rag_service_v3.feedback_loop.record_feedback = Mock()
        rag_service_v3.feedback_loop.should_trigger_retraining = Mock(return_value=True)
        
        rag_service_v3.record_feedback(
            user_id="user123",
            resume_id="resume456",
            optimization_id="opt789",
            feedback_type=FeedbackType.REGENERATE,
            value=0.1
        )
        
        rag_service_v3.feedback_loop.should_trigger_retraining.assert_called_once()
    
    def test_get_feedback_metrics(self, rag_service_v3):
        """Test getting feedback metrics."""
        mock_metrics = Mock()
        mock_metrics.total_events = 100
        mock_metrics.positive_events = 75
        mock_metrics.negative_events = 25
        mock_metrics.avg_score = 0.75
        mock_metrics.download_rate = 0.60
        mock_metrics.edit_rate = 0.20
        mock_metrics.regenerate_rate = 0.10
        
        rag_service_v3.feedback_loop.get_metrics = Mock(return_value=mock_metrics)
        
        metrics = rag_service_v3.get_feedback_metrics(resume_id="test123", days=30)
        
        assert metrics["total_events"] == 100
        assert metrics["avg_score"] == 0.75
        assert metrics["download_rate"] == 0.60


class TestModelInfo:
    """Test model information retrieval."""
    
    def test_get_model_info_base_embeddings(self, rag_service_v3):
        """Test getting model info with base embeddings."""
        info = rag_service_v3.get_model_info()
        
        assert info["rag_version"] == "3.0.0"
        assert info["embeddings"] == "base"
        assert info["multi_vector_enabled"] is True
        assert info["hallucination_detection_enabled"] is True
        assert info["feedback_loop_enabled"] is True
    
    def test_get_model_info_fine_tuned(self, mock_db):
        """Test getting model info with fine-tuned embeddings."""
        with patch('app.services.rag_service_v3.get_embedding_manager') as mock_em, \
             patch('app.services.rag_service_v3.GoogleGenerativeAIEmbeddings'), \
             patch('app.services.rag_service_v3.ChatGoogleGenerativeAI'), \
             patch('app.services.rag_service_v3.get_vector_store_manager'), \
             patch('app.services.rag_service_v3.HybridSearchEngine'), \
             patch('app.services.rag_service_v3.create_reranker'), \
             patch('app.services.rag_service_v3.create_multi_vector_system'), \
             patch('app.services.rag_service_v3.get_hallucination_detector'), \
             patch('app.services.rag_service_v3.create_feedback_loop'):
            
            mock_manager = Mock()
            mock_manager.get_model_info.return_value = {
                "model_type": "fine_tuned",
                "version": "v1.0"
            }
            mock_em.return_value = mock_manager
            
            service = RAGServiceV3(
                db=mock_db,
                use_fine_tuned_embeddings=True
            )
            
            info = service.get_model_info()
            
            assert info["embeddings"] == "fine_tuned"
            assert "embedding_model" in info


class TestFactoryFunction:
    """Test factory function."""
    
    def test_create_rag_service_v3(self, mock_db):
        """Test creating service via factory function."""
        with patch('app.services.rag_service_v3.GoogleGenerativeAIEmbeddings'), \
             patch('app.services.rag_service_v3.ChatGoogleGenerativeAI'), \
             patch('app.services.rag_service_v3.get_vector_store_manager'), \
             patch('app.services.rag_service_v3.HybridSearchEngine'), \
             patch('app.services.rag_service_v3.create_reranker'), \
             patch('app.services.rag_service_v3.create_multi_vector_system'), \
             patch('app.services.rag_service_v3.get_hallucination_detector'), \
             patch('app.services.rag_service_v3.create_feedback_loop'):
            
            service = create_rag_service_v3(
                db=mock_db,
                enable_multi_vector=True,
                enable_hallucination_detection=True
            )
            
            assert isinstance(service, RAGServiceV3)
            assert service.enable_multi_vector is True
            assert service.enable_hallucination_detection is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
