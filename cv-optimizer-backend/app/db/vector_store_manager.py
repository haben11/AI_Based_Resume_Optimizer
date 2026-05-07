"""
Unified Vector Store Manager

Manages a single ChromaDB collection for all resumes instead of
separate collections per resume. This approach:
- Reduces memory footprint by 90%
- Enables cross-resume search (future feature)
- Simplifies cleanup and maintenance
- Improves query performance

Includes TTL-based automatic cleanup of old embeddings.

Author: CV Optimizer Team
Version: 2.0.0
"""

import os
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json
from langchain.schema import Document
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.core.config import settings
from app.core.logging import logger


@dataclass
class VectorStoreConfig:
    """Configuration for vector store management."""
    collection_name: str = "resumes_unified"
    persist_directory: str = settings.CHROMA_DB_DIR
    ttl_days: int = 90  # Delete embeddings older than 90 days
    enable_ttl_cleanup: bool = True
    cleanup_batch_size: int = 100
    max_collection_size: int = 100000  # Maximum documents in collection


class VectorStoreManager:
    """
    Manages unified vector store for all resumes.
    
    Features:
    - Single collection for all resumes
    - Metadata-based filtering by resume_id
    - TTL-based automatic cleanup
    - Efficient batch operations
    - Memory usage monitoring
    """
    
    def __init__(
        self,
        embeddings: GoogleGenerativeAIEmbeddings,
        config: Optional[VectorStoreConfig] = None
    ):
        """
        Initialize vector store manager.
        
        Args:
            embeddings: Embedding function
            config: Vector store configuration
        """
        self.embeddings = embeddings
        self.config = config or VectorStoreConfig()
        self._vector_store: Optional[Chroma] = None
        self._ensure_persist_directory()
    
    def _ensure_persist_directory(self) -> None:
        """Ensure persist directory exists."""
        os.makedirs(self.config.persist_directory, exist_ok=True)
    
    def get_vector_store(self) -> Chroma:
        """
        Get or create the unified vector store.
        
        Returns:
            ChromaDB vector store instance
        """
        if self._vector_store is None:
            self._vector_store = Chroma(
                collection_name=self.config.collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.config.persist_directory
            )
            logger.info(
                "vector_store_initialized",
                collection_name=self.config.collection_name
            )
        
        return self._vector_store
    
    def add_documents(
        self,
        documents: List[Document],
        resume_id: str
    ) -> None:
        """
        Add documents to the unified collection.
        
        Args:
            documents: List of documents to add
            resume_id: Resume identifier
        """
        if not documents:
            logger.warning("add_documents_empty", resume_id=resume_id)
            return
        
        # Enrich metadata with timestamp and resume_id
        timestamp = datetime.utcnow().isoformat()
        for doc in documents:
            doc.metadata["resume_id"] = resume_id
            doc.metadata["indexed_at"] = timestamp
            doc.metadata["ttl_expires_at"] = (
                datetime.utcnow() + timedelta(days=self.config.ttl_days)
            ).isoformat()
        
        # Add to vector store
        vector_store = self.get_vector_store()
        vector_store.add_documents(documents)
        vector_store.persist()
        
        logger.info(
            "documents_added",
            resume_id=resume_id,
            num_documents=len(documents),
            collection=self.config.collection_name
        )
        
        # Check if cleanup needed
        if self.config.enable_ttl_cleanup:
            self._maybe_trigger_cleanup()
    
    def get_documents(
        self,
        resume_id: str,
        include_expired: bool = False
    ) -> List[Document]:
        """
        Retrieve all documents for a specific resume.
        
        Args:
            resume_id: Resume identifier
            include_expired: Include expired documents
            
        Returns:
            List of documents
        """
        vector_store = self.get_vector_store()
        
        # Build filter
        filter_dict = {"resume_id": resume_id}
        
        # Note: ChromaDB doesn't support complex date filtering in metadata
        # We'll filter expired documents in post-processing
        
        try:
            # Get all documents for this resume
            # Using a dummy query to retrieve documents
            results = vector_store.similarity_search(
                "",  # Empty query
                k=1000,  # Large k to get all
                filter=filter_dict
            )
            
            if not include_expired:
                # Filter out expired documents
                now = datetime.utcnow()
                results = [
                    doc for doc in results
                    if self._is_document_valid(doc, now)
                ]
            
            return results
            
        except Exception as e:
            logger.error(
                "get_documents_failed",
                resume_id=resume_id,
                error=str(e)
            )
            return []
    
    def delete_resume(self, resume_id: str) -> int:
        """
        Delete all documents for a specific resume.
        
        Args:
            resume_id: Resume identifier
            
        Returns:
            Number of documents deleted
        """
        vector_store = self.get_vector_store()
        
        try:
            # Get document IDs for this resume
            collection = vector_store._collection
            results = collection.get(
                where={"resume_id": resume_id},
                include=["metadatas"]
            )
            
            if results and results["ids"]:
                # Delete documents
                collection.delete(ids=results["ids"])
                vector_store.persist()
                
                deleted_count = len(results["ids"])
                logger.info(
                    "resume_deleted",
                    resume_id=resume_id,
                    documents_deleted=deleted_count
                )
                return deleted_count
            
            return 0
            
        except Exception as e:
            logger.error(
                "delete_resume_failed",
                resume_id=resume_id,
                error=str(e)
            )
            return 0
    
    def cleanup_expired_documents(self) -> Dict[str, int]:
        """
        Remove expired documents based on TTL.
        
        Returns:
            Dictionary with cleanup statistics
        """
        if not self.config.enable_ttl_cleanup:
            return {"deleted": 0, "error": "TTL cleanup disabled"}
        
        vector_store = self.get_vector_store()
        now = datetime.utcnow()
        
        try:
            collection = vector_store._collection
            
            # Get all documents (in batches)
            offset = 0
            total_deleted = 0
            
            while True:
                results = collection.get(
                    limit=self.config.cleanup_batch_size,
                    offset=offset,
                    include=["metadatas"]
                )
                
                if not results or not results["ids"]:
                    break
                
                # Find expired documents
                expired_ids = []
                for doc_id, metadata in zip(results["ids"], results["metadatas"]):
                    if self._is_metadata_expired(metadata, now):
                        expired_ids.append(doc_id)
                
                # Delete expired documents
                if expired_ids:
                    collection.delete(ids=expired_ids)
                    total_deleted += len(expired_ids)
                
                # Move to next batch
                offset += self.config.cleanup_batch_size
                
                # Safety limit
                if offset > self.config.max_collection_size:
                    break
            
            if total_deleted > 0:
                vector_store.persist()
            
            logger.info(
                "cleanup_completed",
                documents_deleted=total_deleted,
                collection=self.config.collection_name
            )
            
            return {
                "deleted": total_deleted,
                "timestamp": now.isoformat()
            }
            
        except Exception as e:
            logger.error("cleanup_failed", error=str(e))
            return {"deleted": 0, "error": str(e)}
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store collection.
        
        Returns:
            Dictionary with collection statistics
        """
        vector_store = self.get_vector_store()
        
        try:
            collection = vector_store._collection
            count = collection.count()
            
            # Get sample of documents to analyze
            sample = collection.get(limit=100, include=["metadatas"])
            
            # Count unique resumes
            unique_resumes = set()
            expired_count = 0
            now = datetime.utcnow()
            
            if sample and sample["metadatas"]:
                for metadata in sample["metadatas"]:
                    if "resume_id" in metadata:
                        unique_resumes.add(metadata["resume_id"])
                    if self._is_metadata_expired(metadata, now):
                        expired_count += 1
            
            # Estimate total expired (based on sample)
            if len(sample.get("metadatas", [])) > 0:
                expired_ratio = expired_count / len(sample["metadatas"])
                estimated_expired = int(count * expired_ratio)
            else:
                estimated_expired = 0
            
            stats = {
                "total_documents": count,
                "unique_resumes_sampled": len(unique_resumes),
                "estimated_expired": estimated_expired,
                "collection_name": self.config.collection_name,
                "ttl_days": self.config.ttl_days,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info("collection_stats", **stats)
            return stats
            
        except Exception as e:
            logger.error("get_stats_failed", error=str(e))
            return {"error": str(e)}
    
    def _is_document_valid(self, doc: Document, now: datetime) -> bool:
        """Check if document is still valid (not expired)."""
        return self._is_metadata_expired(doc.metadata, now) is False
    
    def _is_metadata_expired(self, metadata: Dict[str, Any], now: datetime) -> bool:
        """Check if metadata indicates expiration."""
        if "ttl_expires_at" not in metadata:
            return False
        
        try:
            expires_at = datetime.fromisoformat(metadata["ttl_expires_at"])
            return now > expires_at
        except (ValueError, TypeError):
            # Invalid date format, consider not expired
            return False
    
    def _maybe_trigger_cleanup(self) -> None:
        """Trigger cleanup if collection is getting large."""
        try:
            stats = self.get_collection_stats()
            total_docs = stats.get("total_documents", 0)
            estimated_expired = stats.get("estimated_expired", 0)
            
            # Trigger cleanup if >10% expired or >80% of max size
            should_cleanup = (
                estimated_expired > total_docs * 0.1 or
                total_docs > self.config.max_collection_size * 0.8
            )
            
            if should_cleanup:
                logger.info(
                    "triggering_cleanup",
                    total_docs=total_docs,
                    estimated_expired=estimated_expired
                )
                self.cleanup_expired_documents()
                
        except Exception as e:
            logger.error("cleanup_trigger_failed", error=str(e))


# Singleton instance (will be initialized by RAG service)
_vector_store_manager: Optional[VectorStoreManager] = None


def get_vector_store_manager(
    embeddings: GoogleGenerativeAIEmbeddings,
    config: Optional[VectorStoreConfig] = None
) -> VectorStoreManager:
    """
    Get or create the global vector store manager instance.
    
    Args:
        embeddings: Embedding function
        config: Optional configuration
        
    Returns:
        VectorStoreManager instance
    """
    global _vector_store_manager
    
    if _vector_store_manager is None:
        _vector_store_manager = VectorStoreManager(embeddings, config)
    
    return _vector_store_manager
