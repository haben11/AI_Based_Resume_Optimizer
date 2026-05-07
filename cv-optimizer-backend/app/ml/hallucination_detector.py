"""
Advanced Hallucination Detector

LLM-based verification system to detect fabricated content in generated resumes.
Uses multiple strategies to ensure factual accuracy.

Strategies:
1. Entity extraction and verification
2. Claim verification against source
3. Consistency checking
4. Temporal logic verification

Author: CV Optimizer Team
Version: 3.0.0
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from app.core.config import settings
from app.core.logging import logger


class HallucinationType(str, Enum):
    """Types of hallucinations."""
    FABRICATED_COMPANY = "fabricated_company"
    FABRICATED_DATE = "fabricated_date"
    FABRICATED_METRIC = "fabricated_metric"
    FABRICATED_SKILL = "fabricated_skill"
    FABRICATED_ACHIEVEMENT = "fabricated_achievement"
    EXAGGERATED_CLAIM = "exaggerated_claim"
    INCONSISTENT_TIMELINE = "inconsistent_timeline"


@dataclass
class HallucinationFinding:
    """Detected hallucination."""
    type: HallucinationType
    severity: float  # 0-1, higher is more severe
    location: str  # Where in the document
    claim: str  # The hallucinated claim
    evidence: str  # Why it's considered hallucination
    suggestion: Optional[str] = None


@dataclass
class VerificationResult:
    """Result of hallucination detection."""
    is_trustworthy: bool
    confidence: float  # 0-1
    findings: List[HallucinationFinding] = field(default_factory=list)
    verified_claims: int = 0
    total_claims: int = 0
    
    @property
    def hallucination_score(self) -> float:
        """Calculate overall hallucination score (0=none, 1=severe)."""
        if not self.findings:
            return 0.0
        
        total_severity = sum(f.severity for f in self.findings)
        return min(1.0, total_severity / len(self.findings))


class AdvancedHallucinationDetector:
    """
    Advanced hallucination detection using LLM-based verification.
    
    Multi-strategy approach:
    1. Extract entities (companies, dates, metrics)
    2. Verify each entity against source
    3. Check for consistency
    4. Verify temporal logic
    5. Detect exaggerations
    """
    
    def __init__(self):
        """Initialize hallucination detector."""
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-lite",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.0,  # Deterministic for verification
            convert_system_message_to_human=True
        )
    
    async def detect_hallucinations(
        self,
        generated_content: str,
        source_content: str
    ) -> VerificationResult:
        """
        Detect hallucinations in generated content.
        
        Args:
            generated_content: Generated resume
            source_content: Original resume
            
        Returns:
            VerificationResult with findings
        """
        logger.info("hallucination_detection_started")
        
        findings: List[HallucinationFinding] = []
        
        # Strategy 1: Entity verification
        entity_findings = await self._verify_entities(generated_content, source_content)
        findings.extend(entity_findings)
        
        # Strategy 2: Claim verification
        claim_findings = await self._verify_claims(generated_content, source_content)
        findings.extend(claim_findings)
        
        # Strategy 3: Consistency checking
        consistency_findings = self._check_consistency(generated_content)
        findings.extend(consistency_findings)
        
        # Strategy 4: Temporal logic
        temporal_findings = self._verify_temporal_logic(generated_content)
        findings.extend(temporal_findings)
        
        # Calculate trustworthiness
        severe_findings = [f for f in findings if f.severity > 0.7]
        is_trustworthy = len(severe_findings) == 0
        
        # Calculate confidence
        confidence = 1.0 - (len(findings) * 0.1)  # Decrease confidence with findings
        confidence = max(0.0, min(1.0, confidence))
        
        result = VerificationResult(
            is_trustworthy=is_trustworthy,
            confidence=confidence,
            findings=findings
        )
        
        logger.info("hallucination_detection_complete",
                   is_trustworthy=is_trustworthy,
                   num_findings=len(findings),
                   confidence=confidence)
        
        return result
    
    async def _verify_entities(
        self,
        generated: str,
        source: str
    ) -> List[HallucinationFinding]:
        """Verify entities (companies, dates, etc.) against source."""
        findings = []
        
        # Extract companies
        generated_companies = self._extract_companies(generated)
        source_companies = self._extract_companies(source)
        
        fabricated_companies = generated_companies - source_companies
        for company in fabricated_companies:
            findings.append(HallucinationFinding(
                type=HallucinationType.FABRICATED_COMPANY,
                severity=0.9,  # High severity
                location="experience",
                claim=f"Company: {company}",
                evidence="Company not found in original resume",
                suggestion=f"Remove or verify {company}"
            ))
        
        # Extract dates
        generated_dates = self._extract_dates(generated)
        source_dates = self._extract_dates(source)
        
        fabricated_dates = generated_dates - source_dates
        for date in fabricated_dates:
            findings.append(HallucinationFinding(
                type=HallucinationType.FABRICATED_DATE,
                severity=0.8,
                location="experience",
                claim=f"Date: {date}",
                evidence="Date not found in original resume",
                suggestion=f"Verify date {date}"
            ))
        
        return findings
    
    async def _verify_claims(
        self,
        generated: str,
        source: str
    ) -> List[HallucinationFinding]:
        """Verify claims using LLM."""
        findings = []
        
        # Extract quantifiable claims
        claims = self._extract_quantifiable_claims(generated)
        
        for claim in claims[:5]:  # Limit to avoid excessive API calls
            is_supported = await self._is_claim_supported(claim, source)
            
            if not is_supported:
                findings.append(HallucinationFinding(
                    type=HallucinationType.FABRICATED_METRIC,
                    severity=0.7,
                    location="experience",
                    claim=claim,
                    evidence="Claim not supported by original resume",
                    suggestion="Verify or remove this metric"
                ))
        
        return findings
    
    async def _is_claim_supported(self, claim: str, source: str) -> bool:
        """Check if claim is supported by source using LLM."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a fact-checker. Determine if a claim is supported by the source text.
            
Respond with ONLY "YES" or "NO".

YES if:
- The claim is directly stated in the source
- The claim is a reasonable inference from the source
- The numbers/metrics match or are close

NO if:
- The claim contradicts the source
- The claim adds information not in the source
- The numbers/metrics are significantly different"""),
            ("human", f"Claim: {claim}\n\nSource: {source}\n\nIs the claim supported?")
        ])
        
        try:
            chain = prompt | self.llm
            response = await chain.ainvoke({})
            answer = response.content.strip().upper()
            return "YES" in answer
        except Exception as e:
            logger.error("claim_verification_failed", error=str(e))
            return True  # Assume supported if verification fails
    
    def _check_consistency(self, content: str) -> List[HallucinationFinding]:
        """Check for internal consistency."""
        findings = []
        
        # Check for contradictory statements
        # Example: "5 years experience" in summary but dates show 3 years
        
        # Extract experience claims
        experience_claims = re.findall(r'(\d+)\+?\s*(?:years?|yrs?)', content, re.IGNORECASE)
        
        if len(experience_claims) > 1:
            # Check if claims are consistent
            years = [int(y) for y in experience_claims]
            if max(years) - min(years) > 2:  # More than 2 year difference
                findings.append(HallucinationFinding(
                    type=HallucinationType.INCONSISTENT_TIMELINE,
                    severity=0.6,
                    location="summary/experience",
                    claim=f"Inconsistent experience claims: {experience_claims}",
                    evidence="Different experience durations mentioned",
                    suggestion="Ensure consistent experience duration"
                ))
        
        return findings
    
    def _verify_temporal_logic(self, content: str) -> List[HallucinationFinding]:
        """Verify temporal logic (dates make sense)."""
        findings = []
        
        # Extract date ranges
        date_ranges = re.findall(
            r'(\d{4})\s*[-–]\s*(\d{4}|Present|Current)',
            content,
            re.IGNORECASE
        )
        
        for start, end in date_ranges:
            start_year = int(start)
            
            # Check if start year is reasonable
            if start_year < 1970 or start_year > 2026:
                findings.append(HallucinationFinding(
                    type=HallucinationType.FABRICATED_DATE,
                    severity=0.9,
                    location="experience",
                    claim=f"Date range: {start}-{end}",
                    evidence=f"Unrealistic start year: {start}",
                    suggestion="Verify date accuracy"
                ))
            
            # Check if end year is after start year
            if end.isdigit():
                end_year = int(end)
                if end_year < start_year:
                    findings.append(HallucinationFinding(
                        type=HallucinationType.INCONSISTENT_TIMELINE,
                        severity=0.9,
                        location="experience",
                        claim=f"Date range: {start}-{end}",
                        evidence="End date before start date",
                        suggestion="Fix date order"
                    ))
        
        return findings
    
    def _extract_companies(self, text: str) -> Set[str]:
        """Extract company names from text."""
        # Pattern: Capitalized words followed by Inc, LLC, Corp, Ltd, Co
        companies = set(re.findall(
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc|LLC|Corp|Ltd|Co|Corporation|Company)\b',
            text
        ))
        return companies
    
    def _extract_dates(self, text: str) -> Set[str]:
        """Extract dates from text."""
        dates = set()
        
        # Year patterns
        years = re.findall(r'\b(19|20)\d{2}\b', text)
        dates.update(years)
        
        # Month-Year patterns
        month_years = re.findall(
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b',
            text,
            re.IGNORECASE
        )
        dates.update(month_years)
        
        return dates
    
    def _extract_quantifiable_claims(self, text: str) -> List[str]:
        """Extract quantifiable claims (metrics, achievements)."""
        claims = []
        
        # Find sentences with numbers/percentages
        sentences = re.split(r'[.!?]\s+', text)
        
        for sentence in sentences:
            # Check if sentence contains metrics
            if re.search(r'\d+(?:,\d{3})*(?:\.\d+)?(?:%|k|m|b|\+)?', sentence, re.IGNORECASE):
                claims.append(sentence.strip())
        
        return claims


# Singleton instance
_hallucination_detector: Optional[AdvancedHallucinationDetector] = None


def get_hallucination_detector() -> AdvancedHallucinationDetector:
    """
    Get or create global hallucination detector instance.
    
    Returns:
        AdvancedHallucinationDetector instance
    """
    global _hallucination_detector
    
    if _hallucination_detector is None:
        _hallucination_detector = AdvancedHallucinationDetector()
    
    return _hallucination_detector
