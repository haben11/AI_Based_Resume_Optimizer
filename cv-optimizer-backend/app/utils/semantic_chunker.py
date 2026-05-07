"""
Semantic Chunker for Resume Processing

This module provides intelligent chunking of resume content that respects
semantic boundaries (sections, sentences) rather than arbitrary character limits.
Each chunk is enriched with metadata for improved retrieval accuracy.

Author: CV Optimizer Team
Version: 1.0.0
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
from langchain.schema import Document


class SectionType(str, Enum):
    """Enumeration of standard resume sections."""
    HEADER = "header"
    SUMMARY = "summary"
    EXPERIENCE = "experience"
    SKILLS = "skills"
    EDUCATION = "education"
    PROJECTS = "projects"
    CERTIFICATIONS = "certifications"
    ACHIEVEMENTS = "achievements"
    UNKNOWN = "unknown"


@dataclass
class ChunkMetadata:
    """Structured metadata for resume chunks."""
    section_type: SectionType
    section_title: str
    chunk_index: int
    total_chunks: int
    char_count: int
    has_dates: bool
    has_metrics: bool
    keywords: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for storage."""
        return {
            "section_type": self.section_type.value,
            "section_title": self.section_title,
            "chunk_index": self.chunk_index,
            "total_chunks": self.total_chunks,
            "char_count": self.char_count,
            "has_dates": self.has_dates,
            "has_metrics": self.has_metrics,
            "keywords": ", ".join(self.keywords) if self.keywords else ""  # Convert list to string
        }


class SemanticChunker:
    """
    Intelligent resume chunker that respects semantic boundaries.
    
    Features:
    - Section-aware splitting (never splits across major sections)
    - Sentence-boundary preservation
    - Metadata enrichment for each chunk
    - Adaptive chunk sizing based on content density
    """
    
    # Section header patterns (case-insensitive)
    SECTION_PATTERNS = {
        SectionType.SUMMARY: r"(?:professional\s+)?(?:summary|profile|about|objective)",
        SectionType.EXPERIENCE: r"(?:professional\s+)?(?:experience|work\s+history|employment)",
        SectionType.SKILLS: r"(?:core\s+)?(?:skills|competencies|technical\s+skills|expertise)",
        SectionType.EDUCATION: r"education(?:al\s+background)?",
        SectionType.PROJECTS: r"(?:key\s+)?projects?",
        SectionType.CERTIFICATIONS: r"certifications?|licenses?",
        SectionType.ACHIEVEMENTS: r"achievements?|awards?|honors?",
    }
    
    # Patterns for metadata extraction
    DATE_PATTERN = r"\b(?:\d{4}|\d{1,2}/\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b"
    METRIC_PATTERN = r"\b(?:\d+(?:,\d{3})*(?:\.\d+)?(?:%|k|m|b)?|\$\d+(?:,\d{3})*(?:\.\d+)?(?:k|m|b)?)\b"
    
    # Chunk size constraints
    MIN_CHUNK_SIZE = 200  # Minimum characters per chunk
    MAX_CHUNK_SIZE = 1500  # Maximum characters per chunk
    TARGET_CHUNK_SIZE = 800  # Ideal chunk size
    
    def __init__(self, max_chunk_size: int = MAX_CHUNK_SIZE):
        """
        Initialize the semantic chunker.
        
        Args:
            max_chunk_size: Maximum characters per chunk (default: 1500)
        """
        self.max_chunk_size = max_chunk_size
        
    def chunk_resume(self, text: str, resume_id: str) -> List[Document]:
        """
        Split resume text into semantic chunks with rich metadata.
        
        Args:
            text: Raw resume text
            resume_id: Unique identifier for the resume
            
        Returns:
            List of LangChain Document objects with content and metadata
        """
        # Step 1: Identify and extract sections
        sections = self._extract_sections(text)
        
        # Step 2: Process each section into chunks
        all_chunks: List[Document] = []
        
        for section in sections:
            section_chunks = self._chunk_section(
                section["content"],
                section["type"],
                section["title"],
                resume_id
            )
            all_chunks.extend(section_chunks)
        
        # Step 3: Update total_chunks count in metadata
        total_chunks = len(all_chunks)
        for doc in all_chunks:
            doc.metadata["total_chunks"] = total_chunks
            
        return all_chunks
    
    def _extract_sections(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract resume sections based on header patterns.
        
        Args:
            text: Raw resume text
            
        Returns:
            List of dictionaries containing section metadata and content
        """
        sections = []
        lines = text.split('\n')
        current_section = {
            "type": SectionType.HEADER,
            "title": "Header",
            "content": "",
            "start_line": 0
        }
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Check if line is a section header
            section_type = self._identify_section_type(line_stripped)
            
            if section_type != SectionType.UNKNOWN:
                # Save previous section if it has content
                if current_section["content"].strip():
                    sections.append(current_section)
                
                # Start new section
                current_section = {
                    "type": section_type,
                    "title": line_stripped,
                    "content": "",
                    "start_line": i
                }
            else:
                # Add line to current section
                current_section["content"] += line + "\n"
        
        # Add the last section
        if current_section["content"].strip():
            sections.append(current_section)
        
        return sections
    
    def _identify_section_type(self, line: str) -> SectionType:
        """
        Identify the type of section based on header text.
        
        Args:
            line: Header line text
            
        Returns:
            SectionType enum value
        """
        # Check if line looks like a header (short, possibly with markdown)
        if len(line) > 50 or not line:
            return SectionType.UNKNOWN
        
        # Remove markdown symbols
        clean_line = re.sub(r'^#+\s*', '', line).lower()
        
        # Match against section patterns
        for section_type, pattern in self.SECTION_PATTERNS.items():
            if re.search(pattern, clean_line, re.IGNORECASE):
                return section_type
        
        return SectionType.UNKNOWN
    
    def _chunk_section(
        self,
        content: str,
        section_type: SectionType,
        section_title: str,
        resume_id: str
    ) -> List[Document]:
        """
        Split a section into appropriately-sized chunks.
        
        Args:
            content: Section content
            section_type: Type of section
            section_title: Title of the section
            resume_id: Resume identifier
            
        Returns:
            List of Document objects
        """
        content = content.strip()
        
        # If content is small enough, return as single chunk
        if len(content) <= self.max_chunk_size:
            metadata = self._extract_metadata(
                content, section_type, section_title, 0, 1, resume_id
            )
            return [Document(page_content=content, metadata=metadata)]
        
        # Split into sentences for intelligent chunking
        sentences = self._split_into_sentences(content)
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            # Check if adding this sentence would exceed max size
            if len(current_chunk) + len(sentence) > self.max_chunk_size and current_chunk:
                # Save current chunk
                metadata = self._extract_metadata(
                    current_chunk,
                    section_type,
                    section_title,
                    chunk_index,
                    0,  # Will be updated later
                    resume_id
                )
                chunks.append(Document(page_content=current_chunk.strip(), metadata=metadata))
                chunk_index += 1
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add the last chunk
        if current_chunk.strip():
            metadata = self._extract_metadata(
                current_chunk,
                section_type,
                section_title,
                chunk_index,
                0,  # Will be updated later
                resume_id
            )
            chunks.append(Document(page_content=current_chunk.strip(), metadata=metadata))
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences while preserving context.
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        # Handle common abbreviations that shouldn't trigger sentence breaks
        text = re.sub(r'\bDr\.', 'Dr', text)
        text = re.sub(r'\bMr\.', 'Mr', text)
        text = re.sub(r'\bMs\.', 'Ms', text)
        text = re.sub(r'\bMrs\.', 'Mrs', text)
        text = re.sub(r'\bInc\.', 'Inc', text)
        text = re.sub(r'\bLtd\.', 'Ltd', text)
        
        # Split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        
        return [s.strip() for s in sentences if s.strip()]
    
    def _extract_metadata(
        self,
        content: str,
        section_type: SectionType,
        section_title: str,
        chunk_index: int,
        total_chunks: int,
        resume_id: str
    ) -> Dict[str, Any]:
        """
        Extract rich metadata from chunk content.
        
        Args:
            content: Chunk content
            section_type: Type of section
            section_title: Section title
            chunk_index: Index of this chunk within the section
            total_chunks: Total number of chunks (0 if not yet known)
            resume_id: Resume identifier
            
        Returns:
            Dictionary of metadata
        """
        # Detect dates
        has_dates = bool(re.search(self.DATE_PATTERN, content, re.IGNORECASE))
        
        # Detect metrics/numbers
        has_metrics = bool(re.search(self.METRIC_PATTERN, content, re.IGNORECASE))
        
        # Extract keywords (simple approach: capitalized words and technical terms)
        keywords = self._extract_keywords(content)
        
        metadata = ChunkMetadata(
            section_type=section_type,
            section_title=section_title,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            char_count=len(content),
            has_dates=has_dates,
            has_metrics=has_metrics,
            keywords=keywords
        )
        
        # Add resume_id to metadata dict
        metadata_dict = metadata.to_dict()
        metadata_dict["source"] = resume_id
        
        return metadata_dict
    
    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract important keywords from text.
        
        Args:
            text: Text to analyze
            max_keywords: Maximum number of keywords to extract
            
        Returns:
            List of keywords
        """
        # Extract capitalized words (likely proper nouns, technologies, etc.)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        # Extract acronyms (2+ capital letters)
        acronyms = re.findall(r'\b[A-Z]{2,}\b', text)
        
        # Extract technical terms (words with numbers, dots, or hyphens)
        technical = re.findall(r'\b[A-Za-z]+[0-9]+[A-Za-z0-9]*\b|\b[A-Za-z]+\.[A-Za-z]+\b', text)
        
        # Combine and deduplicate
        all_keywords = list(set(capitalized + acronyms + technical))
        
        # Sort by frequency in text and return top N
        keyword_freq = [(kw, text.count(kw)) for kw in all_keywords]
        keyword_freq.sort(key=lambda x: x[1], reverse=True)
        
        return [kw for kw, _ in keyword_freq[:max_keywords]]


# Singleton instance for easy import
semantic_chunker = SemanticChunker()
