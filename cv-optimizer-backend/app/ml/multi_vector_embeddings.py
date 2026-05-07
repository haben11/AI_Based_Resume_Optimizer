"""
Multi-Vector Embedding System

Creates separate embeddings for different aspects of resumes:
- Skills embeddings
- Experience embeddings
- Education embeddings
- Summary embeddings

This allows for more nuanced matching and better retrieval quality.

Author: CV Optimizer Team
Version: 3.0.0
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from langchain.schema import Document
from app.core.logging import logger


class EmbeddingAspect(str, Enum):
    """Different aspects for multi-vector embeddings."""
    SKILLS = "skills"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    SUMMARY = "summary"
    PROJECTS = "projects"
    FULL_CONTENT = "full_content"


@dataclass
class MultiVectorDocument:
    """Document with multiple aspect embeddings."""
    content: str
    metadata: Dict[str, Any]
    aspect_embeddings: Dict[EmbeddingAspect, np.ndarray]
    primary_aspect: EmbeddingAspect


class MultiVectorEmbeddingSystem:
    """
    Multi-vector embedding system for nuanced resume matching.
    
    Creates separate embeddings for different resume aspects,
    allowing for aspect-specific retrieval and better matching.
    
    Example:
        When searching for "Python skills", prioritize skills embeddings.
        When searching for "5 years experience", prioritize experience embeddings.
    """
    
    def __init__(self, embedding_function):
        """
        Initialize multi-vector system.
        
        Args:
            embedding_function: Function to generate embeddings
        """
        self.embedding_function = embedding_function
        
        # Aspect-specific weights for different query types
        self.aspect_weights = {
            "skills_query": {
                EmbeddingAspect.SKILLS: 0.6,
                EmbeddingAspect.EXPERIENCE: 0.2,
                EmbeddingAspect.PROJECTS: 0.1,
                EmbeddingAspect.SUMMARY: 0.05,
                EmbeddingAspect.EDUCATION: 0.05
            },
            "experience_query": {
                EmbeddingAspect.EXPERIENCE: 0.6,
                EmbeddingAspect.PROJECTS: 0.2,
                EmbeddingAspect.SKILLS: 0.1,
                EmbeddingAspect.SUMMARY: 0.05,
                EmbeddingAspect.EDUCATION: 0.05
            },
            "education_query": {
                EmbeddingAspect.EDUCATION: 0.7,
                EmbeddingAspect.SUMMARY: 0.15,
                EmbeddingAspect.EXPERIENCE: 0.1,
                EmbeddingAspect.SKILLS: 0.05
            },
            "general_query": {
                EmbeddingAspect.SUMMARY: 0.3,
                EmbeddingAspect.EXPERIENCE: 0.3,
                EmbeddingAspect.SKILLS: 0.2,
                EmbeddingAspect.PROJECTS: 0.1,
                EmbeddingAspect.EDUCATION: 0.1
            }
        }
    
    def create_multi_vector_document(
        self,
        document: Document
    ) -> MultiVectorDocument:
        """
        Create multi-vector document from standard document.
        
        Args:
            document: Standard LangChain document
            
        Returns:
            MultiVectorDocument with aspect embeddings
        """
        content = document.page_content
        metadata = document.metadata
        
        # Determine primary aspect from metadata
        section_type = metadata.get("section_type", "unknown")
        primary_aspect = self._map_section_to_aspect(section_type)
        
        # Create embeddings for each aspect
        aspect_embeddings = {}
        
        # Always create full content embedding
        aspect_embeddings[EmbeddingAspect.FULL_CONTENT] = self._embed_text(content)
        
        # Create aspect-specific embeddings based on content
        if primary_aspect == EmbeddingAspect.SKILLS:
            aspect_embeddings[EmbeddingAspect.SKILLS] = self._embed_skills(content, metadata)
        elif primary_aspect == EmbeddingAspect.EXPERIENCE:
            aspect_embeddings[EmbeddingAspect.EXPERIENCE] = self._embed_experience(content, metadata)
        elif primary_aspect == EmbeddingAspect.EDUCATION:
            aspect_embeddings[EmbeddingAspect.EDUCATION] = self._embed_education(content, metadata)
        elif primary_aspect == EmbeddingAspect.SUMMARY:
            aspect_embeddings[EmbeddingAspect.SUMMARY] = self._embed_summary(content, metadata)
        elif primary_aspect == EmbeddingAspect.PROJECTS:
            aspect_embeddings[EmbeddingAspect.PROJECTS] = self._embed_projects(content, metadata)
        
        return MultiVectorDocument(
            content=content,
            metadata=metadata,
            aspect_embeddings=aspect_embeddings,
            primary_aspect=primary_aspect
        )
    
    def _map_section_to_aspect(self, section_type: str) -> EmbeddingAspect:
        """Map section type to embedding aspect."""
        mapping = {
            "skills": EmbeddingAspect.SKILLS,
            "experience": EmbeddingAspect.EXPERIENCE,
            "education": EmbeddingAspect.EDUCATION,
            "summary": EmbeddingAspect.SUMMARY,
            "projects": EmbeddingAspect.PROJECTS
        }
        return mapping.get(section_type, EmbeddingAspect.FULL_CONTENT)
    
    def _embed_text(self, text: str) -> np.ndarray:
        """Create standard embedding for text."""
        return self.embedding_function.embed_query(text)
    
    def _embed_skills(self, content: str, metadata: Dict) -> np.ndarray:
        """Create skills-focused embedding."""
        # Extract keywords if available
        keywords = metadata.get("keywords", [])
        
        # Enhance content with keywords for better skill matching
        if keywords:
            enhanced_content = f"{content} Key skills: {', '.join(keywords)}"
        else:
            enhanced_content = content
        
        return self._embed_text(enhanced_content)
    
    def _embed_experience(self, content: str, metadata: Dict) -> np.ndarray:
        """Create experience-focused embedding."""
        # Emphasize metrics and achievements
        has_metrics = metadata.get("has_metrics", False)
        has_dates = metadata.get("has_dates", False)
        
        prefix = ""
        if has_metrics:
            prefix += "Quantifiable achievements: "
        if has_dates:
            prefix += "Professional experience: "
        
        enhanced_content = f"{prefix}{content}"
        return self._embed_text(enhanced_content)
    
    def _embed_education(self, content: str, metadata: Dict) -> np.ndarray:
        """Create education-focused embedding."""
        enhanced_content = f"Educational background: {content}"
        return self._embed_text(enhanced_content)
    
    def _embed_summary(self, content: str, metadata: Dict) -> np.ndarray:
        """Create summary-focused embedding."""
        enhanced_content = f"Professional summary: {content}"
        return self._embed_text(enhanced_content)
    
    def _embed_projects(self, content: str, metadata: Dict) -> np.ndarray:
        """Create projects-focused embedding."""
        has_metrics = metadata.get("has_metrics", False)
        prefix = "Technical project with measurable impact: " if has_metrics else "Technical project: "
        enhanced_content = f"{prefix}{content}"
        return self._embed_text(enhanced_content)
    
    def classify_query_type(self, query: str) -> str:
        """
        Classify query to determine which aspects to prioritize.
        
        Args:
            query: Search query
            
        Returns:
            Query type (skills_query, experience_query, etc.)
        """
        query_lower = query.lower()
        
        # Skills indicators
        skills_keywords = ["skill", "proficient", "expertise", "knowledge", "technology", "tool"]
        if any(kw in query_lower for kw in skills_keywords):
            return "skills_query"
        
        # Experience indicators
        experience_keywords = ["experience", "years", "worked", "led", "managed", "developed"]
        if any(kw in query_lower for kw in experience_keywords):
            return "experience_query"
        
        # Education indicators
        education_keywords = ["degree", "education", "university", "bachelor", "master", "phd"]
        if any(kw in query_lower for kw in education_keywords):
            return "education_query"
        
        return "general_query"
    
    def compute_weighted_similarity(
        self,
        query_embedding: np.ndarray,
        document: MultiVectorDocument,
        query_type: Optional[str] = None
    ) -> float:
        """
        Compute weighted similarity between query and multi-vector document.
        
        Args:
            query_embedding: Query embedding
            document: Multi-vector document
            query_type: Type of query (determines weights)
            
        Returns:
            Weighted similarity score
        """
        if query_type is None:
            query_type = "general_query"
        
        weights = self.aspect_weights.get(query_type, self.aspect_weights["general_query"])
        
        total_similarity = 0.0
        total_weight = 0.0
        
        for aspect, weight in weights.items():
            if aspect in document.aspect_embeddings:
                aspect_embedding = document.aspect_embeddings[aspect]
                
                # Cosine similarity
                similarity = np.dot(query_embedding, aspect_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(aspect_embedding)
                )
                
                total_similarity += similarity * weight
                total_weight += weight
        
        # Normalize by total weight
        if total_weight > 0:
            return total_similarity / total_weight
        
        return 0.0
    
    def retrieve_with_multi_vector(
        self,
        query: str,
        documents: List[MultiVectorDocument],
        top_k: int = 5
    ) -> List[Tuple[MultiVectorDocument, float]]:
        """
        Retrieve documents using multi-vector similarity.
        
        Args:
            query: Search query
            documents: List of multi-vector documents
            top_k: Number of results to return
            
        Returns:
            List of (document, score) tuples
        """
        # Classify query type
        query_type = self.classify_query_type(query)
        
        logger.info("multi_vector_retrieval",
                   query_type=query_type,
                   num_documents=len(documents))
        
        # Embed query
        query_embedding = self._embed_text(query)
        
        # Compute weighted similarities
        scored_docs = []
        for doc in documents:
            score = self.compute_weighted_similarity(
                query_embedding,
                doc,
                query_type
            )
            scored_docs.append((doc, score))
        
        # Sort by score
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        return scored_docs[:top_k]
    
    def get_aspect_statistics(
        self,
        documents: List[MultiVectorDocument]
    ) -> Dict[str, Any]:
        """
        Get statistics about aspect distribution.
        
        Args:
            documents: List of multi-vector documents
            
        Returns:
            Statistics dictionary
        """
        aspect_counts = {aspect: 0 for aspect in EmbeddingAspect}
        
        for doc in documents:
            aspect_counts[doc.primary_aspect] += 1
        
        return {
            "total_documents": len(documents),
            "aspect_distribution": {
                aspect.value: count
                for aspect, count in aspect_counts.items()
            },
            "avg_aspects_per_doc": sum(
                len(doc.aspect_embeddings) for doc in documents
            ) / len(documents) if documents else 0
        }


# Factory function
def create_multi_vector_system(embedding_function) -> MultiVectorEmbeddingSystem:
    """
    Create multi-vector embedding system.
    
    Args:
        embedding_function: Embedding function to use
        
    Returns:
        MultiVectorEmbeddingSystem instance
    """
    return MultiVectorEmbeddingSystem(embedding_function)
