"""
Streaming RAG Service

Provides real-time streaming responses for resume optimization.
Uses Server-Sent Events (SSE) to stream progress updates and generated tokens.

Author: CV Optimizer Team
Version: 1.0.0
"""

import json
import asyncio
from typing import AsyncGenerator, Optional, Dict, Any
from sqlalchemy.orm import Session
from langchain_google_genai import ChatGoogleGenerativeAI
from app.services.rag_service_v3 import RAGServiceV3
from app.core.config import settings
from app.core.logging import logger
from app.utils.pii_scrubber import pii_scrubber


class StreamingRAGService(RAGServiceV3):
    """
    Streaming version of RAG Service.
    
    Extends RAGServiceV3 to support streaming responses with progress updates.
    """
    
    async def optimize_cv_stream(
        self,
        resume_id: str,
        job_description: str,
        original_resume_text: Optional[str] = None,
        user_id: Optional[str] = None,
        optimization_id: Optional[str] = None,
        job_title: Optional[str] = None,
        industry: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        """
        Optimize resume with streaming progress updates and caching.
        
        Yields SSE-formatted messages with progress updates and generated tokens.
        
        Args:
            resume_id: Resume identifier
            job_description: Target job description
            original_resume_text: Original resume for hallucination detection
            user_id: User identifier
            optimization_id: Optimization identifier
            job_title: Target job title
            industry: Target industry
            
        Yields:
            SSE-formatted messages (event: data\ndata: json\n\n)
        """
        try:
            # Stage 1: Initialization
            yield self._format_sse_message("progress", {
                "stage": "initialization",
                "message": "Starting optimization...",
                "progress": 0
            })
            
            await asyncio.sleep(0.1)  # Small delay for UI update
            
            # Stage 1.5: Check cache
            if self.enable_cache and self.cache_service:
                yield self._format_sse_message("progress", {
                    "stage": "cache_check",
                    "message": "Checking cache for similar optimizations...",
                    "progress": 5
                })
                
                import hashlib
                context_hash = hashlib.sha256(resume_id.encode()).hexdigest()
                
                cache_hit = await self.cache_service.get_cached_response(
                    query_text=job_description,
                    resume_id=resume_id,
                    job_title=job_title,
                    industry=industry,
                    context_hash=context_hash
                )
                
                if cache_hit:
                    logger.info(
                        "cache_hit_streaming",
                        resume_id=resume_id,
                        match_type=cache_hit["match_type"],
                        similarity=cache_hit["similarity_score"]
                    )
                    
                    # Stream cached response with simulated progress
                    yield self._format_sse_message("progress", {
                        "stage": "cache_hit",
                        "message": f"Found cached result ({cache_hit['match_type']} match, {cache_hit['similarity_score']:.2%} similar)",
                        "progress": 10,
                        "data": {
                            "match_type": cache_hit["match_type"],
                            "similarity": cache_hit["similarity_score"],
                            "hit_count": cache_hit["hit_count"]
                        }
                    })
                    
                    # Stream the cached content token by token for better UX
                    cached_content = cache_hit["response_text"]
                    tokens = cached_content.split()
                    
                    yield self._format_sse_message("progress", {
                        "stage": "streaming_cached",
                        "message": "Streaming cached result...",
                        "progress": 15
                    })
                    
                    for i, token in enumerate(tokens):
                        yield self._format_sse_message("token", {
                            "token": token + " ",
                            "progress": min(15 + int((i / len(tokens)) * 70), 85)
                        })
                        await asyncio.sleep(0.01)  # Small delay for streaming effect
                    
                    # Complete with cached metadata
                    result = {
                        "optimized_content": cached_content,
                        "validation": cache_hit["response_metadata"].get("validation"),
                        "hallucination_check": cache_hit["response_metadata"].get("hallucination_check"),
                        "cache_hit": True,
                        "cache_metadata": {
                            "match_type": cache_hit["match_type"],
                            "similarity_score": cache_hit["similarity_score"],
                            "cached_at": cache_hit["cached_at"].isoformat(),
                            "hit_count": cache_hit["hit_count"]
                        }
                    }
                    
                    yield self._format_sse_message("complete", {
                        "stage": "complete",
                        "message": "Optimization complete (from cache)!",
                        "progress": 100,
                        "result": result
                    })
                    
                    return
            
            # Stage 2: Fetch grounding data
            yield self._format_sse_message("progress", {
                "stage": "grounding",
                "message": "Fetching verified data (keywords, skills, metrics)...",
                "progress": 10
            })
            
            grounding_context = None
            if self.enable_grounding and self.dynamic_grounding_service:
                grounding_context = self.dynamic_grounding_service.fetch_dynamic_grounding_data(
                    job_description=job_description,
                    job_title=job_title,
                    industry=industry
                )
                
                summary = grounding_context.get_summary()
                yield self._format_sse_message("progress", {
                    "stage": "grounding",
                    "message": f"Fetched {summary['ats_keywords']} keywords, {summary['industry_skills']} skills",
                    "progress": 20,
                    "data": summary
                })
            
            # Stage 3: Query processing
            yield self._format_sse_message("progress", {
                "stage": "query_processing",
                "message": "Analyzing job requirements...",
                "progress": 25
            })
            
            from app.utils.query_processor import query_processor
            processed_query = query_processor.process(job_description)
            
            yield self._format_sse_message("progress", {
                "stage": "query_processing",
                "message": f"Identified {len(processed_query.requirements)} key requirements",
                "progress": 30
            })
            
            # Stage 4: Retrieval
            yield self._format_sse_message("progress", {
                "stage": "retrieval",
                "message": "Retrieving relevant resume sections...",
                "progress": 35
            })
            
            if self.enable_multi_vector and resume_id in self.multi_vector_docs:
                results = await self._multi_vector_retrieval(
                    resume_id,
                    job_description,
                    processed_query
                )
            else:
                results = await self._hybrid_retrieval(
                    resume_id,
                    job_description,
                    processed_query,
                    None
                )
            
            yield self._format_sse_message("progress", {
                "stage": "retrieval",
                "message": f"Retrieved {len(results)} relevant sections",
                "progress": 45
            })
            
            # Stage 5: Build context
            yield self._format_sse_message("progress", {
                "stage": "context_building",
                "message": "Building optimization context...",
                "progress": 50
            })
            
            context = self._build_context(results)
            
            # Stage 5.5: Compliance - PII Scrubbing
            # Mask sensitive data before sending to external LLM provider
            user_info = {}
            if self.db and user_id:
                from app.models.user import User
                user = self.db.query(User).filter(User.id == user_id).first()
                if user:
                    user_info = {"full_name": user.full_name, "email": user.email}
            
            scrubbing_result = pii_scrubber.scrub(context, user_info=user_info)
            scrubbed_context = scrubbing_result.scrubbed_text
            
            # Stage 6: Generate optimized resume (streaming)
            yield self._format_sse_message("progress", {
                "stage": "generation",
                "message": "Generating optimized resume...",
                "progress": 55
            })
            
            # Build prompt
            prompt = self._build_enhanced_prompt(processed_query, grounding_context)
            
            # Build prompt inputs
            prompt_inputs = {
                "context": scrubbed_context,
                "job_description": job_description,
                "key_requirements": self._format_requirements(processed_query.requirements[:5])
            }
            
            if grounding_context:
                prompt_inputs["grounding_data"] = grounding_context.to_prompt_context()
            
            # Create streaming LLM
            streaming_llm = ChatGoogleGenerativeAI(
                model=self.config.llm.model_name,
                google_api_key=settings.GOOGLE_API_KEY,
                temperature=self.config.llm.temperature,
                streaming=True,  # Enable streaming
                convert_system_message_to_human=True
            )
            
            chain = prompt | streaming_llm
            
            # Stream tokens
            optimized_content = ""
            token_count = 0
            
            async for chunk in chain.astream(prompt_inputs):
                if hasattr(chunk, 'content'):
                    token = chunk.content
                    optimized_content += token
                    token_count += 1
                    
                    # Send token to client
                    yield self._format_sse_message("token", {
                        "token": token,
                        "progress": min(55 + (token_count // 10), 85)  # Progress 55-85%
                    })
            
            # Stage 6.5: Compliance - PII Descrubbing
            # Restore original values (names, emails, etc.) for the final result
            optimized_content = pii_scrubber.descrub(
                optimized_content, 
                scrubbing_result.placeholders
            )
            
            # Stage 7: Validation
            yield self._format_sse_message("progress", {
                "stage": "validation",
                "message": "Validating output quality...",
                "progress": 90
            })
            
            from app.utils.output_validator import output_validator
            validation_result = output_validator.validate(
                optimized_content,
                original_resume=original_resume_text
            )
            
            yield self._format_sse_message("progress", {
                "stage": "validation",
                "message": f"Quality score: {validation_result.score:.2f}",
                "progress": 95,
                "data": {
                    "is_valid": validation_result.is_valid,
                    "score": validation_result.score,
                    "issue_count": len(validation_result.get_errors())
                }
            })
            
            # Stage 8: Hallucination detection (if enabled)
            hallucination_result = None
            if self.enable_hallucination_detection and original_resume_text:
                yield self._format_sse_message("progress", {
                    "stage": "hallucination_check",
                    "message": "Checking for hallucinations...",
                    "progress": 97
                })
                
                hallucination_result = await self.hallucination_detector.detect_hallucinations(
                    generated_content=optimized_content,
                    source_content=original_resume_text
                )
                
                yield self._format_sse_message("progress", {
                    "stage": "hallucination_check",
                    "message": f"Trustworthy: {hallucination_result.is_trustworthy}",
                    "progress": 99,
                    "data": {
                        "is_trustworthy": hallucination_result.is_trustworthy,
                        "confidence": hallucination_result.confidence,
                        "finding_count": len(hallucination_result.findings)
                    }
                })
            
            # Stage 9: Complete
            result = {
                "optimized_content": optimized_content,
                "validation": {
                    "is_valid": validation_result.is_valid,
                    "quality_score": validation_result.score,
                    "issues": [
                        {
                            "severity": issue.severity,
                            "message": issue.message,
                            "suggestion": issue.suggestion
                        }
                        for issue in validation_result.issues
                    ]
                },
                "hallucination_check": None,
                "cache_hit": False
            }
            
            if hallucination_result:
                result["hallucination_check"] = {
                    "is_trustworthy": hallucination_result.is_trustworthy,
                    "confidence": hallucination_result.confidence,
                    "hallucination_score": hallucination_result.hallucination_score,
                    "findings": [
                        {
                            "type": finding.type.value,
                            "severity": finding.severity,
                            "location": finding.location,
                            "claim": finding.claim,
                            "evidence": finding.evidence,
                            "suggestion": finding.suggestion
                        }
                        for finding in hallucination_result.findings
                    ]
                }
            
            # Cache the response for future use
            if self.enable_cache and self.cache_service:
                import hashlib
                context_hash = hashlib.sha256(resume_id.encode()).hexdigest()
                
                cache_metadata = {
                    "validation": result["validation"],
                    "hallucination_check": result["hallucination_check"]
                }
                
                quality_score = validation_result.score
                if hallucination_result:
                    quality_score = quality_score * hallucination_result.confidence
                
                try:
                    await self.cache_service.cache_response(
                        query_text=job_description,
                        response_text=optimized_content,
                        response_metadata=cache_metadata,
                        resume_id=resume_id,
                        job_title=job_title,
                        industry=industry,
                        context_hash=context_hash,
                        quality_score=quality_score
                    )
                    
                    logger.info(
                        "streaming_response_cached",
                        resume_id=resume_id,
                        quality_score=quality_score
                    )
                except Exception as cache_error:
                    logger.error(
                        "streaming_cache_storage_failed",
                        resume_id=resume_id,
                        error=str(cache_error)
                    )
            
            yield self._format_sse_message("complete", {
                "stage": "complete",
                "message": "Optimization complete!",
                "progress": 100,
                "result": result
            })
            
            logger.info("streaming_optimization_complete", resume_id=resume_id)
            
        except Exception as e:
            logger.error("streaming_optimization_failed", resume_id=resume_id, error=str(e))
            yield self._format_sse_message("error", {
                "stage": "error",
                "message": f"Optimization failed: {str(e)}",
                "error": str(e)
            })
    
    def _format_sse_message(self, event: str, data: Dict[str, Any]) -> str:
        """
        Format message as Server-Sent Event.
        
        Args:
            event: Event type (progress, token, complete, error)
            data: Event data
            
        Returns:
            SSE-formatted string
        """
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def create_streaming_rag_service(
    db: Optional[Session] = None,
    **kwargs
) -> StreamingRAGService:
    """
    Create streaming RAG service instance.
    
    Args:
        db: Database session
        **kwargs: Additional configuration options
        
    Returns:
        StreamingRAGService instance
    """
    return StreamingRAGService(db=db, **kwargs)
