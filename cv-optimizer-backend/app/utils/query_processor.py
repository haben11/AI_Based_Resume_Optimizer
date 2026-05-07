"""
Advanced Query Processor

Processes and enhances job description queries for better retrieval.
Includes:
- Key requirement extraction
- Skill identification
- Query structuring
- Importance weighting

Author: CV Optimizer Team
Version: 2.0.0
"""

import re
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum


class RequirementType(str, Enum):
    """Types of job requirements."""
    MUST_HAVE = "must_have"
    NICE_TO_HAVE = "nice_to_have"
    PREFERRED = "preferred"
    REQUIRED = "required"


@dataclass
class JobRequirement:
    """Structured job requirement."""
    text: str
    type: RequirementType
    category: str  # technical, soft_skill, experience, education
    importance: float  # 0-1 score
    keywords: List[str] = field(default_factory=list)


@dataclass
class ProcessedQuery:
    """Processed and structured query."""
    original_query: str
    requirements: List[JobRequirement]
    key_skills: List[str]
    experience_years: Optional[int]
    education_level: Optional[str]
    enhanced_query: str
    importance_weights: Dict[str, float]


class QueryProcessor:
    """
    Advanced query processor for job descriptions.
    
    Extracts structured information from job descriptions to
    improve retrieval and matching quality.
    """
    
    # Technical skills patterns
    TECH_SKILLS = {
        "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "go",
        "rust", "php", "swift", "kotlin", "scala", "r", "matlab",
        "react", "angular", "vue", "node", "django", "flask", "spring",
        "aws", "azure", "gcp", "docker", "kubernetes", "terraform",
        "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "git", "jenkins", "ci/cd", "agile", "scrum", "devops",
        "machine learning", "deep learning", "ai", "nlp", "computer vision",
        "data science", "analytics", "big data", "hadoop", "spark"
    }
    
    # Soft skills patterns
    SOFT_SKILLS = {
        "leadership", "communication", "teamwork", "problem solving",
        "critical thinking", "creativity", "adaptability", "time management",
        "collaboration", "mentoring", "presentation", "negotiation"
    }
    
    # Experience patterns
    EXPERIENCE_PATTERN = r'(\d+)\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)'
    
    # Education levels
    EDUCATION_LEVELS = {
        "phd": 5, "doctorate": 5,
        "master": 4, "masters": 4, "ms": 4, "mba": 4,
        "bachelor": 3, "bachelors": 3, "bs": 3, "ba": 3,
        "associate": 2,
        "high school": 1, "diploma": 1
    }
    
    def __init__(self):
        """Initialize query processor."""
        pass
    
    def process(self, job_description: str) -> ProcessedQuery:
        """
        Process job description into structured format.
        
        Args:
            job_description: Raw job description text
            
        Returns:
            ProcessedQuery with extracted information
        """
        # Extract requirements
        requirements = self._extract_requirements(job_description)
        
        # Extract key skills
        key_skills = self._extract_skills(job_description)
        
        # Extract experience requirement
        experience_years = self._extract_experience(job_description)
        
        # Extract education requirement
        education_level = self._extract_education(job_description)
        
        # Build enhanced query
        enhanced_query = self._build_enhanced_query(
            job_description,
            requirements,
            key_skills
        )
        
        # Calculate importance weights
        importance_weights = self._calculate_importance_weights(requirements)
        
        return ProcessedQuery(
            original_query=job_description,
            requirements=requirements,
            key_skills=key_skills,
            experience_years=experience_years,
            education_level=education_level,
            enhanced_query=enhanced_query,
            importance_weights=importance_weights
        )
    
    def _extract_requirements(self, text: str) -> List[JobRequirement]:
        """Extract structured requirements from text."""
        requirements = []
        text_lower = text.lower()
        
        # Split into sentences
        sentences = re.split(r'[.!?\n]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Determine requirement type
            req_type = self._classify_requirement_type(sentence)
            
            # Determine category
            category = self._classify_requirement_category(sentence)
            
            # Calculate importance
            importance = self._calculate_requirement_importance(sentence, req_type)
            
            # Extract keywords
            keywords = self._extract_keywords_from_sentence(sentence)
            
            if keywords:  # Only add if we found meaningful keywords
                requirements.append(JobRequirement(
                    text=sentence,
                    type=req_type,
                    category=category,
                    importance=importance,
                    keywords=keywords
                ))
        
        return requirements
    
    def _classify_requirement_type(self, sentence: str) -> RequirementType:
        """Classify requirement as must-have, nice-to-have, etc."""
        sentence_lower = sentence.lower()
        
        if any(word in sentence_lower for word in ["required", "must have", "must-have", "essential"]):
            return RequirementType.REQUIRED
        elif any(word in sentence_lower for word in ["preferred", "ideal", "bonus"]):
            return RequirementType.PREFERRED
        elif any(word in sentence_lower for word in ["nice to have", "nice-to-have", "plus"]):
            return RequirementType.NICE_TO_HAVE
        else:
            return RequirementType.MUST_HAVE
    
    def _classify_requirement_category(self, sentence: str) -> str:
        """Classify requirement category."""
        sentence_lower = sentence.lower()
        
        # Check for technical skills
        if any(skill in sentence_lower for skill in self.TECH_SKILLS):
            return "technical"
        
        # Check for soft skills
        if any(skill in sentence_lower for skill in self.SOFT_SKILLS):
            return "soft_skill"
        
        # Check for experience
        if re.search(self.EXPERIENCE_PATTERN, sentence_lower, re.IGNORECASE):
            return "experience"
        
        # Check for education
        if any(edu in sentence_lower for edu in self.EDUCATION_LEVELS.keys()):
            return "education"
        
        return "general"
    
    def _calculate_requirement_importance(
        self,
        sentence: str,
        req_type: RequirementType
    ) -> float:
        """Calculate importance score for requirement."""
        # Base score from requirement type
        type_scores = {
            RequirementType.REQUIRED: 1.0,
            RequirementType.MUST_HAVE: 0.9,
            RequirementType.PREFERRED: 0.7,
            RequirementType.NICE_TO_HAVE: 0.5
        }
        
        base_score = type_scores.get(req_type, 0.8)
        
        # Boost for specific keywords
        sentence_lower = sentence.lower()
        if "critical" in sentence_lower or "essential" in sentence_lower:
            base_score = min(1.0, base_score * 1.2)
        
        return base_score
    
    def _extract_keywords_from_sentence(self, sentence: str) -> List[str]:
        """Extract meaningful keywords from sentence."""
        keywords = []
        sentence_lower = sentence.lower()
        
        # Extract technical skills
        for skill in self.TECH_SKILLS:
            if skill in sentence_lower:
                keywords.append(skill)
        
        # Extract soft skills
        for skill in self.SOFT_SKILLS:
            if skill in sentence_lower:
                keywords.append(skill)
        
        # Extract capitalized terms (likely technologies/tools)
        capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', sentence)
        keywords.extend(capitalized[:3])  # Limit to avoid noise
        
        # Extract acronyms
        acronyms = re.findall(r'\b[A-Z]{2,}\b', sentence)
        keywords.extend(acronyms)
        
        return list(set(keywords))  # Remove duplicates
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract all skills mentioned in job description."""
        text_lower = text.lower()
        skills = []
        
        # Technical skills
        for skill in self.TECH_SKILLS:
            if skill in text_lower:
                skills.append(skill)
        
        # Soft skills
        for skill in self.SOFT_SKILLS:
            if skill in text_lower:
                skills.append(skill)
        
        return skills
    
    def _extract_experience(self, text: str) -> Optional[int]:
        """Extract years of experience requirement."""
        match = re.search(self.EXPERIENCE_PATTERN, text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None
    
    def _extract_education(self, text: str) -> Optional[str]:
        """Extract education level requirement."""
        text_lower = text.lower()
        
        # Find highest education level mentioned
        highest_level = None
        highest_score = 0
        
        for edu, score in self.EDUCATION_LEVELS.items():
            if edu in text_lower and score > highest_score:
                highest_level = edu
                highest_score = score
        
        return highest_level
    
    def _build_enhanced_query(
        self,
        original: str,
        requirements: List[JobRequirement],
        skills: List[str]
    ) -> str:
        """Build enhanced query with weighted terms."""
        # Start with original
        enhanced_parts = [original]
        
        # Add high-importance requirements
        high_importance_reqs = [
            req for req in requirements
            if req.importance >= 0.8
        ]
        
        for req in high_importance_reqs[:5]:  # Top 5
            enhanced_parts.extend(req.keywords)
        
        # Add skills (with repetition for emphasis)
        for skill in skills[:10]:  # Top 10 skills
            enhanced_parts.append(skill)
            enhanced_parts.append(skill)  # Repeat for emphasis
        
        return " ".join(enhanced_parts)
    
    def _calculate_importance_weights(
        self,
        requirements: List[JobRequirement]
    ) -> Dict[str, float]:
        """Calculate importance weights by category."""
        category_weights = {
            "technical": 0.0,
            "soft_skill": 0.0,
            "experience": 0.0,
            "education": 0.0,
            "general": 0.0
        }
        
        category_counts = {cat: 0 for cat in category_weights.keys()}
        
        # Sum importance scores by category
        for req in requirements:
            category_weights[req.category] += req.importance
            category_counts[req.category] += 1
        
        # Average by count
        for category in category_weights:
            if category_counts[category] > 0:
                category_weights[category] /= category_counts[category]
        
        # Normalize to sum to 1.0
        total = sum(category_weights.values())
        if total > 0:
            category_weights = {
                cat: weight / total
                for cat, weight in category_weights.items()
            }
        
        return category_weights


# Singleton instance
query_processor = QueryProcessor()
