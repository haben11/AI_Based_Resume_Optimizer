"""
Output Validator for Resume Optimization

Ensures generated resumes meet quality standards and contain all required sections.
Provides detailed validation reports and suggestions for improvement.

Author: CV Optimizer Team
Version: 1.0.0
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    ERROR = "error"  # Critical issue, output unusable
    WARNING = "warning"  # Issue that should be addressed
    INFO = "info"  # Suggestion for improvement


@dataclass
class ValidationIssue:
    """Represents a validation issue found in the output."""
    severity: ValidationSeverity
    section: str
    message: str
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of output validation."""
    is_valid: bool
    score: float  # 0-100 quality score
    issues: List[ValidationIssue] = field(default_factory=list)
    sections_found: List[str] = field(default_factory=list)
    sections_missing: List[str] = field(default_factory=list)
    word_count: int = 0
    has_metrics: bool = False
    has_action_verbs: bool = False
    
    def get_errors(self) -> List[ValidationIssue]:
        """Get all error-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]
    
    def get_warnings(self) -> List[ValidationIssue]:
        """Get all warning-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]
    
    def get_info(self) -> List[ValidationIssue]:
        """Get all info-level issues."""
        return [i for i in self.issues if i.severity == ValidationSeverity.INFO]


class OutputValidator:
    """
    Validates generated resume content for quality and completeness.
    
    Validation checks:
    - Required sections present
    - Proper markdown formatting
    - Presence of quantifiable metrics
    - Use of strong action verbs
    - Appropriate length
    - No hallucinated content (basic checks)
    """
    
    # Required sections for a complete resume
    REQUIRED_SECTIONS = [
        "summary",
        "experience",
        "skills",
        "education"
    ]
    
    # Optional but recommended sections
    RECOMMENDED_SECTIONS = [
        "projects",
        "certifications"
    ]
    
    # Strong action verbs for resume writing
    ACTION_VERBS = {
        "achieved", "improved", "increased", "decreased", "reduced",
        "developed", "created", "designed", "built", "implemented",
        "led", "managed", "directed", "coordinated", "supervised",
        "analyzed", "evaluated", "assessed", "researched", "investigated",
        "optimized", "streamlined", "enhanced", "transformed", "revolutionized",
        "launched", "established", "founded", "initiated", "pioneered",
        "delivered", "executed", "completed", "accomplished", "attained",
        "generated", "produced", "drove", "spearheaded", "orchestrated"
    }
    
    # Patterns for detecting metrics
    METRIC_PATTERNS = [
        r'\d+%',  # Percentages
        r'\$\d+(?:,\d{3})*(?:\.\d+)?[KMB]?',  # Dollar amounts
        r'\d+(?:,\d{3})*\+?\s*(?:users|customers|clients|employees)',  # User counts
        r'(?:increased|decreased|improved|reduced)\s+(?:by\s+)?\d+',  # Improvements
        r'\d+x\s+(?:faster|better|more)',  # Multipliers
    ]
    
    # Minimum word counts by section
    MIN_WORD_COUNTS = {
        "summary": 30,
        "experience": 50,
        "skills": 10,
        "education": 5
    }
    
    def __init__(self):
        """Initialize the output validator."""
        pass
    
    def validate(self, content: str, original_resume: Optional[str] = None) -> ValidationResult:
        """
        Validate generated resume content.
        
        Args:
            content: Generated resume markdown
            original_resume: Original resume text for hallucination detection
            
        Returns:
            ValidationResult with detailed findings
        """
        result = ValidationResult(is_valid=True, score=100.0)
        
        # Check 1: Section presence
        self._validate_sections(content, result)
        
        # Check 2: Markdown formatting
        self._validate_formatting(content, result)
        
        # Check 3: Content quality
        self._validate_content_quality(content, result)
        
        # Check 4: Metrics and quantification
        self._validate_metrics(content, result)
        
        # Check 5: Action verbs
        self._validate_action_verbs(content, result)
        
        # Check 6: Length appropriateness
        self._validate_length(content, result)
        
        # Check 7: Hallucination detection (if original provided)
        if original_resume:
            self._validate_factual_accuracy(content, original_resume, result)
        
        # Calculate final validity and score
        error_count = len(result.get_errors())
        warning_count = len(result.get_warnings())
        
        result.is_valid = error_count == 0
        result.score = max(0, 100 - (error_count * 20) - (warning_count * 5))
        
        return result
    
    def _validate_sections(self, content: str, result: ValidationResult) -> None:
        """Validate presence of required sections."""
        content_lower = content.lower()
        
        # Detect sections using markdown headers
        section_pattern = r'^##\s+(.+)$'
        found_sections = re.findall(section_pattern, content, re.MULTILINE)
        
        # Normalize section names
        normalized_sections = [
            self._normalize_section_name(s) for s in found_sections
        ]
        
        result.sections_found = list(set(normalized_sections))
        
        # Check required sections
        for required in self.REQUIRED_SECTIONS:
            if required not in result.sections_found:
                result.sections_missing.append(required)
                result.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    section="structure",
                    message=f"Missing required section: {required.title()}",
                    suggestion=f"Add a '## {required.title()}' section with relevant content"
                ))
        
        # Check recommended sections
        for recommended in self.RECOMMENDED_SECTIONS:
            if recommended not in result.sections_found:
                result.issues.append(ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    section="structure",
                    message=f"Consider adding section: {recommended.title()}",
                    suggestion=f"If applicable, add a '## {recommended.title()}' section"
                ))
    
    def _normalize_section_name(self, section: str) -> str:
        """Normalize section name to standard format."""
        section_lower = section.lower().strip()
        
        # Map variations to standard names
        if any(x in section_lower for x in ["summary", "profile", "about", "objective"]):
            return "summary"
        elif any(x in section_lower for x in ["experience", "work", "employment"]):
            return "experience"
        elif any(x in section_lower for x in ["skill", "competenc", "expertise"]):
            return "skills"
        elif "education" in section_lower:
            return "education"
        elif "project" in section_lower:
            return "projects"
        elif any(x in section_lower for x in ["certification", "license"]):
            return "certifications"
        elif any(x in section_lower for x in ["achievement", "award", "honor"]):
            return "achievements"
        else:
            return section_lower
    
    def _validate_formatting(self, content: str, result: ValidationResult) -> None:
        """Validate markdown formatting."""
        lines = content.split('\n')
        
        # Check for proper header hierarchy
        has_h1 = bool(re.search(r'^#\s+', content, re.MULTILINE))
        has_h2 = bool(re.search(r'^##\s+', content, re.MULTILINE))
        
        if not has_h1:
            result.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                section="formatting",
                message="Missing H1 header (name)",
                suggestion="Start resume with '# Full Name'"
            ))
        
        if not has_h2:
            result.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                section="formatting",
                message="Missing H2 section headers",
                suggestion="Use '## Section Name' for major sections"
            ))
        
        # Check for proper list formatting in experience/projects
        experience_section = self._extract_section(content, "experience")
        if experience_section:
            if not re.search(r'^[-*]\s+', experience_section, re.MULTILINE):
                result.issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    section="experience",
                    message="Experience bullets not properly formatted",
                    suggestion="Use '- ' or '* ' for bullet points"
                ))
    
    def _validate_content_quality(self, content: str, result: ValidationResult) -> None:
        """Validate content quality for each section."""
        for section_name in self.REQUIRED_SECTIONS:
            section_content = self._extract_section(content, section_name)
            
            if not section_content:
                continue
            
            # Check minimum word count
            word_count = len(section_content.split())
            min_words = self.MIN_WORD_COUNTS.get(section_name, 0)
            
            if word_count < min_words:
                result.issues.append(ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    section=section_name,
                    message=f"Section too short ({word_count} words, minimum {min_words})",
                    suggestion=f"Expand {section_name} section with more detail"
                ))
        
        # Count total words
        result.word_count = len(content.split())
    
    def _validate_metrics(self, content: str, result: ValidationResult) -> None:
        """Validate presence of quantifiable metrics."""
        metrics_found = 0
        
        for pattern in self.METRIC_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            metrics_found += len(matches)
        
        result.has_metrics = metrics_found > 0
        
        if metrics_found == 0:
            result.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                section="content",
                message="No quantifiable metrics found",
                suggestion="Add specific numbers, percentages, or measurable achievements"
            ))
        elif metrics_found < 3:
            result.issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                section="content",
                message=f"Only {metrics_found} metrics found",
                suggestion="Consider adding more quantifiable achievements"
            ))
    
    def _validate_action_verbs(self, content: str, result: ValidationResult) -> None:
        """Validate use of strong action verbs."""
        content_lower = content.lower()
        
        action_verbs_found = [
            verb for verb in self.ACTION_VERBS
            if verb in content_lower
        ]
        
        result.has_action_verbs = len(action_verbs_found) > 0
        
        if len(action_verbs_found) == 0:
            result.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                section="content",
                message="No strong action verbs found",
                suggestion="Start bullet points with action verbs like 'Achieved', 'Developed', 'Led'"
            ))
        elif len(action_verbs_found) < 5:
            result.issues.append(ValidationIssue(
                severity=ValidationSeverity.INFO,
                section="content",
                message="Limited variety of action verbs",
                suggestion="Use more diverse action verbs to strengthen impact"
            ))
    
    def _validate_length(self, content: str, result: ValidationResult) -> None:
        """Validate overall resume length."""
        word_count = len(content.split())
        
        if word_count < 200:
            result.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                section="length",
                message=f"Resume too short ({word_count} words)",
                suggestion="Expand content to at least 200 words"
            ))
        elif word_count > 1500:
            result.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                section="length",
                message=f"Resume very long ({word_count} words)",
                suggestion="Consider condensing to 800-1200 words for optimal readability"
            ))
    
    def _validate_factual_accuracy(
        self,
        content: str,
        original: str,
        result: ValidationResult
    ) -> None:
        """
        Basic hallucination detection by checking for invented content.
        
        This is a simple implementation that checks for:
        - Company names not in original
        - Dates not in original
        - Degree names not in original
        """
        content_lower = content.lower()
        original_lower = original.lower()
        
        # Extract company names (capitalized words followed by Inc, LLC, etc.)
        content_companies = set(re.findall(
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc|LLC|Corp|Ltd|Co)\b',
            content
        ))
        original_companies = set(re.findall(
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc|LLC|Corp|Ltd|Co)\b',
            original
        ))
        
        invented_companies = content_companies - original_companies
        if invented_companies:
            result.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                section="accuracy",
                message=f"Possible hallucinated company names: {', '.join(invented_companies)}",
                suggestion="Verify all company names exist in original resume"
            ))
        
        # Extract years
        content_years = set(re.findall(r'\b(19|20)\d{2}\b', content))
        original_years = set(re.findall(r'\b(19|20)\d{2}\b', original))
        
        invented_years = content_years - original_years
        if invented_years:
            result.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                section="accuracy",
                message=f"Dates not in original: {', '.join(invented_years)}",
                suggestion="Verify all dates match the original resume"
            ))
    
    def _extract_section(self, content: str, section_name: str) -> Optional[str]:
        """Extract content of a specific section."""
        # Pattern to match section and capture content until next section
        pattern = rf'##\s+(?:{section_name}|{section_name.title()}).*?\n(.*?)(?=\n##|\Z)'
        
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        
        return match.group(1).strip() if match else None


# Singleton instance
output_validator = OutputValidator()
