import os
from typing import List, Optional
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.vectorstores import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from app.core.config import settings
from app.core.logging import logger
from app.utils.semantic_chunker import semantic_chunker
from app.utils.enhanced_retriever import enhanced_retriever, RetrievalConfig
from app.utils.output_validator import output_validator

class RAGService:
    """
    Enhanced RAG Service with Phase 1 Optimizations.
    
    Improvements:
    - Semantic chunking with metadata
    - Advanced retrieval with re-ranking
    - Output validation
    - Better error handling and logging
    """
    
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=settings.GOOGLE_API_KEY
        )
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.2,
            convert_system_message_to_human=True
        )
        
        # Configure retrieval behavior
        self.retrieval_config = RetrievalConfig(
            initial_k=10,  # Retrieve more candidates
            final_k=5,  # Return top 5 after re-ranking
            relevance_threshold=0.7,  # Filter low-quality matches
            diversity_lambda=0.3,  # Balance relevance vs diversity
        )

    async def process_resume(self, text: str, resume_id: str) -> str:
        """
        Indexes the resume content into ChromaDB using semantic chunking.
        
        Args:
            text: Raw resume text
            resume_id: Unique identifier for the resume
            
        Returns:
            Resume ID after successful indexing
        """
        logger.info("indexing_resume", resume_id=resume_id, text_length=len(text))
        
        try:
            # Use semantic chunker instead of simple text splitter
            documents = semantic_chunker.chunk_resume(text, resume_id)
            
            logger.info(
                "chunking_complete",
                resume_id=resume_id,
                num_chunks=len(documents),
                avg_chunk_size=sum(len(d.page_content) for d in documents) // len(documents) if documents else 0
            )
            
            # Create vector database with enriched documents
            vector_db = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=os.path.join(settings.CHROMA_DB_DIR, resume_id)
            )
            vector_db.persist()
            
            logger.info("indexing_complete", resume_id=resume_id)
            return resume_id
            
        except Exception as e:
            logger.error("indexing_failed", resume_id=resume_id, error=str(e))
            raise

    async def optimize_cv(self, resume_id: str, job_description: str) -> str:
        """
        Retrieves context from the resume and generates an optimized CV.
        
        Uses enhanced retrieval with re-ranking and validates output quality.
        
        Args:
            resume_id: Unique identifier for the resume
            job_description: Target job description
            
        Returns:
            Optimized resume in markdown format
        """
        logger.info("optimizing_cv", resume_id=resume_id, jd_length=len(job_description))
        
        try:
            # Load vector database
            vector_db = Chroma(
                persist_directory=os.path.join(settings.CHROMA_DB_DIR, resume_id),
                embedding_function=self.embeddings
            )
            
            # Use enhanced retriever with re-ranking
            relevant_docs = enhanced_retriever.retrieve(
                vector_db=vector_db,
                query=job_description,
                filter_dict={"source": resume_id}
            )
            
            # Log retrieval metrics
            logger.info(
                "retrieval_complete",
                resume_id=resume_id,
                num_docs_retrieved=len(relevant_docs),
                sections_retrieved=[d.metadata.get("section_type") for d in relevant_docs]
            )
            
            # Build context from retrieved documents
            context_parts = []
            for doc in relevant_docs:
                section_type = doc.metadata.get("section_type", "unknown")
                section_title = doc.metadata.get("section_title", "")
                context_parts.append(
                    f"[{section_type.upper()}] {section_title}\n{doc.page_content}"
                )
            
            context = "\n\n---\n\n".join(context_parts)
            
            # Enhanced prompt with better instructions
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a senior career coach and elite resume strategist with 15+ years of experience.
Your goal is to perform a FULL SPECTRUM optimization of the user's resume content to perfectly align with the provided job description.

CRITICAL REQUIREMENTS:
1. **Use ONLY information from the provided resume context** - Do not invent companies, dates, or achievements
2. **Maintain factual accuracy** - All claims must be verifiable from the original content
3. **Preserve authentic voice** - Enhance, don't fabricate

STRUCTURE (Use proper Markdown):
# [Full Name]

## Professional Summary
A compelling 3-4 line branding statement that positions the candidate for THIS specific role.
Focus on unique value proposition and alignment with job requirements.

## Core Competencies
Categorized list of technical and soft skills directly mapped to the job description.
Prioritize skills mentioned in the JD. Use bullet points.

## Professional Experience
### [Job Title] | [Company] | [Dates]
- Use X-Y-Z formula: Accomplished [X] as measured by [Y], by doing [Z]
- Start each bullet with strong action verbs (Achieved, Developed, Led, etc.)
- Include quantifiable metrics wherever possible (%, $, numbers)
- Highlight results and impact, not just responsibilities
- Tailor language to match job description keywords

[Repeat for each role, prioritize most relevant experiences]

## Key Projects (if applicable)
### [Project Name]
- Brief description with technologies and impact
- Quantify results where possible

## Education
[Degree] | [Institution] | [Year]
Relevant coursework, honors, or achievements

## Certifications (if applicable)
- [Certification Name] | [Issuing Organization] | [Year]

TONE & STRATEGY:
- Use exact keywords from the Job Description naturally
- Maintain sophisticated, professional tone
- Focus on achievements and measurable impact
- Ensure ATS compatibility with clear section headers
- Keep total length between 400-800 words for optimal readability

QUALITY CHECKS:
- Every section must have substantive content
- Minimum 3 quantifiable metrics across the resume
- At least 5 different strong action verbs
- No generic phrases like "responsible for" or "duties included"
"""),
                ("human", f"""Resume Context (Retrieved Sections):
{context}

Target Job Description:
{job_description}

Generate an optimized resume that maximizes alignment with this job description while maintaining complete factual accuracy.""")
            ])
            
            # Generate optimized resume
            chain = prompt | self.llm
            response = await chain.ainvoke({})
            optimized_content = response.content
            
            # Validate output quality
            # Note: We don't have original full text here, so skip hallucination check
            validation_result = output_validator.validate(optimized_content)
            
            # Log validation results
            logger.info(
                "validation_complete",
                resume_id=resume_id,
                is_valid=validation_result.is_valid,
                quality_score=validation_result.score,
                error_count=len(validation_result.get_errors()),
                warning_count=len(validation_result.get_warnings())
            )
            
            # Log any validation issues
            for issue in validation_result.issues:
                logger.warning(
                    "validation_issue",
                    resume_id=resume_id,
                    severity=issue.severity,
                    section=issue.section,
                    message=issue.message
                )
            
            # If validation fails critically, log but still return
            # (In production, you might want to retry or return error)
            if not validation_result.is_valid:
                logger.error(
                    "validation_failed",
                    resume_id=resume_id,
                    errors=[e.message for e in validation_result.get_errors()]
                )
            
            logger.info("optimization_complete", resume_id=resume_id)
            return optimized_content
            
        except Exception as e:
            logger.error("optimization_failed", resume_id=resume_id, error=str(e))
            raise

rag_service = RAGService()
