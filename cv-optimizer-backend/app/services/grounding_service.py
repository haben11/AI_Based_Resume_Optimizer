"""
External Data Grounding Service

Fetches verified data from knowledge base to prevent hallucinations.
Integrates with RAG pipeline to provide real, grounded information.

This service ensures the LLM synthesizes from real data instead of inventing:
- ATS keywords from database
- Industry-specific terminology
- Salary ranges for roles
- In-demand skills by job title

Author: CV Optimizer Team
Version: 1.0.0
"""

from typing import List, Optional, Dict, Any, Set
from sqlalchemy.orm import Session
from app.crud.crud_knowledge_base import crud_knowledge_base
from app.core.logging import logger
import re


class GroundingContext:
    """
    Container for grounded data fetched from knowledge base.
    
    This data is injected into RAG prompts to prevent hallucination.
    """
    
    def __init__(self):
        self.ats_keywords: List[Dict[str, Any]] = []
        self.industry_skills: List[Dict[str, Any]] = []
        self.job_title_data: Optional[Dict[str, Any]] = None
        self.action_verbs: List[Dict[str, Any]] = []
        self.industry_metrics: List[Dict[str, Any]] = []
        self.salary_data: Optional[Dict[str, Any]] = None
        self.certifications: List[Dict[str, Any]] = []
        
    def to_prompt_context(self) -> str:
        """
        Convert grounding context to formatted string for LLM prompt.
        
        Returns:
            Formatted context string
        """
        sections = []
        
        # ATS Keywords
        if self.ats_keywords:
            keywords_text = "**VERIFIED ATS KEYWORDS** (Use these exact terms):\n"
            for kw in self.ats_keywords[:20]:  # Top 20
                keywords_text += f"- {kw['keyword']} ({kw['category']}, importance: {kw['importance']:.2f})\n"
                if kw.get('synonyms'):
                    keywords_text += f"  Synonyms: {', '.join(kw['synonyms'][:3])}\n"
            sections.append(keywords_text)
        
        # Industry Skills
        if self.industry_skills:
            skills_text = "**IN-DEMAND SKILLS** (Real market data):\n"
            for skill in self.industry_skills[:15]:  # Top 15
                skills_text += f"- {skill['name']} (demand: {skill['demand']:.2f}, growth: {skill['growth']:.1%})\n"
                if skill.get('salary_impact'):
                    skills_text += f"  Salary impact: +${skill['salary_impact']:,.0f}\n"
            sections.append(skills_text)
        
        # Job Title Data
        if self.job_title_data:
            job_text = "**TARGET ROLE DATA**:\n"
            job_text += f"Title: {self.job_title_data['title']}\n"
            job_text += f"Seniority: {self.job_title_data['seniority']}\n"
            
            if self.job_title_data.get('required_skills'):
                job_text += f"Required Skills: {', '.join(self.job_title_data['required_skills'][:10])}\n"
            
            if self.job_title_data.get('salary_range'):
                salary = self.job_title_data['salary_range']
                job_text += f"Salary Range: ${salary['min']:,} - ${salary['max']:,} (median: ${salary['median']:,})\n"
            
            if self.job_title_data.get('experience_range'):
                exp = self.job_title_data['experience_range']
                job_text += f"Experience Required: {exp['min']}-{exp['max']} years\n"
            
            sections.append(job_text)
        
        # Action Verbs
        if self.action_verbs:
            verbs_text = "**STRONG ACTION VERBS** (ATS-optimized):\n"
            by_category = {}
            for verb in self.action_verbs[:30]:  # Top 30
                category = verb['category']
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(verb['verb'])
            
            for category, verbs in by_category.items():
                verbs_text += f"- {category.title()}: {', '.join(verbs[:8])}\n"
            sections.append(verbs_text)
        
        # Industry Metrics
        if self.industry_metrics:
            metrics_text = "**INDUSTRY-STANDARD METRICS** (Use these KPIs):\n"
            for metric in self.industry_metrics[:10]:  # Top 10
                metrics_text += f"- {metric['name']} ({metric['type']})\n"
                if metric.get('typical_range'):
                    metrics_text += f"  Typical: {metric['typical_range']['min']}-{metric['typical_range']['max']}\n"
                if metric.get('exceptional'):
                    metrics_text += f"  Exceptional: >{metric['exceptional']}\n"
            sections.append(metrics_text)
        
        # Certifications
        if self.certifications:
            cert_text = "**RELEVANT CERTIFICATIONS**:\n"
            for cert in self.certifications[:10]:  # Top 10
                cert_text += f"- {cert['name']}"
                if cert.get('abbreviation'):
                    cert_text += f" ({cert['abbreviation']})"
                cert_text += f" - {cert['organization']}\n"
            sections.append(cert_text)
        
        if not sections:
            return ""
        
        header = "=" * 80 + "\n"
        header += "GROUNDED DATA (Use ONLY this verified information)\n"
        header += "DO NOT invent keywords, skills, or metrics not listed here\n"
        header += "=" * 80 + "\n\n"
        
        return header + "\n\n".join(sections)
    
    def get_summary(self) -> Dict[str, int]:
        """Get summary of grounding data."""
        return {
            "ats_keywords": len(self.ats_keywords),
            "industry_skills": len(self.industry_skills),
            "has_job_data": self.job_title_data is not None,
            "action_verbs": len(self.action_verbs),
            "industry_metrics": len(self.industry_metrics),
            "certifications": len(self.certifications)
        }


class GroundingService:
    """
    Service for fetching grounded data from knowledge base.
    
    Prevents hallucination by providing verified, real-world data
    that the LLM can synthesize from.
    """
    
    def __init__(self, db: Session):
        """
        Initialize grounding service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.crud = crud_knowledge_base
    
    def fetch_grounding_data(
        self,
        job_description: str,
        job_title: Optional[str] = None,
        industry: Optional[str] = None,
        job_family: Optional[str] = None
    ) -> GroundingContext:
        """
        Fetch comprehensive grounding data for a job.
        
        Args:
            job_description: Full job description text
            job_title: Extracted job title
            industry: Industry name
            job_family: Job family (e.g., 'engineering', 'marketing')
            
        Returns:
            GroundingContext with all fetched data
        """
        logger.info(
            "fetching_grounding_data",
            job_title=job_title,
            industry=industry,
            job_family=job_family
        )
        
        context = GroundingContext()
        
        # Extract entities from job description if not provided
        if not job_title:
            job_title = self._extract_job_title(job_description)
        
        if not industry:
            industry = self._extract_industry(job_description)
        
        if not job_family:
            job_family = self._infer_job_family(job_title, job_description)
        
        # Fetch ATS keywords
        context.ats_keywords = self._fetch_ats_keywords(
            job_family=job_family,
            job_description=job_description
        )
        
        # Fetch industry skills
        context.industry_skills = self._fetch_industry_skills(
            industry=industry,
            job_description=job_description
        )
        
        # Fetch job title data
        if job_title:
            context.job_title_data = self._fetch_job_title_data(job_title)
            
            # Extract salary data
            if context.job_title_data:
                context.salary_data = {
                    "min": context.job_title_data.get("salary_min"),
                    "max": context.job_title_data.get("salary_max"),
                    "median": context.job_title_data.get("salary_median"),
                    "currency": context.job_title_data.get("salary_currency", "USD")
                }
        
        # Fetch action verbs
        context.action_verbs = self._fetch_action_verbs(
            job_family=job_family,
            job_title=job_title
        )
        
        # Fetch industry metrics
        context.industry_metrics = self._fetch_industry_metrics(
            industry=industry,
            job_family=job_family
        )
        
        # Fetch relevant certifications
        context.certifications = self._fetch_certifications(
            industry=industry,
            job_family=job_family
        )
        
        summary = context.get_summary()
        logger.info("grounding_data_fetched", **summary)
        
        return context
    
    def _fetch_ats_keywords(
        self,
        job_family: Optional[str],
        job_description: str
    ) -> List[Dict[str, Any]]:
        """Fetch relevant ATS keywords."""
        try:
            # Get keywords for job family
            keywords = self.crud.get_ats_keywords(
                db=self.db,
                job_family=job_family,
                min_importance=0.5,  # Only high-importance keywords
                limit=50
            )
            
            # Convert to dict format
            result = []
            for kw in keywords:
                result.append({
                    "keyword": kw.keyword,
                    "category": kw.category,
                    "importance": kw.importance_score,
                    "synonyms": kw.synonyms or [],
                    "context": kw.typical_context
                })
            
            logger.info("ats_keywords_fetched", count=len(result), job_family=job_family)
            return result
            
        except Exception as e:
            logger.error("ats_keywords_fetch_failed", error=str(e))
            return []
    
    def _fetch_industry_skills(
        self,
        industry: Optional[str],
        job_description: str
    ) -> List[Dict[str, Any]]:
        """Fetch in-demand industry skills."""
        try:
            # Get high-demand skills
            skills = self.crud.get_industry_skills(
                db=self.db,
                industry=industry,
                min_demand=0.6,  # Only high-demand skills
                limit=30
            )
            
            # Also get trending skills
            trending = self.crud.get_trending_skills(
                db=self.db,
                industry=industry,
                min_growth_rate=0.1,  # 10% growth
                limit=20
            )
            
            # Combine and deduplicate
            all_skills = {skill.skill_name: skill for skill in skills}
            for skill in trending:
                if skill.skill_name not in all_skills:
                    all_skills[skill.skill_name] = skill
            
            # Convert to dict format
            result = []
            for skill in all_skills.values():
                result.append({
                    "name": skill.skill_name,
                    "category": skill.skill_category,
                    "demand": skill.demand_score,
                    "growth": skill.growth_rate,
                    "salary_impact": skill.avg_salary_impact,
                    "related_skills": skill.related_skills or []
                })
            
            # Sort by demand
            result.sort(key=lambda x: x["demand"], reverse=True)
            
            logger.info("industry_skills_fetched", count=len(result), industry=industry)
            return result
            
        except Exception as e:
            logger.error("industry_skills_fetch_failed", error=str(e))
            return []
    
    def _fetch_job_title_data(self, job_title: str) -> Optional[Dict[str, Any]]:
        """Fetch data for specific job title."""
        try:
            job_data = self.crud.get_job_title_data(
                db=self.db,
                title=job_title,
                fuzzy_match=True
            )
            
            if not job_data:
                logger.warning("job_title_not_found", title=job_title)
                return None
            
            result = {
                "title": job_data.title,
                "normalized_title": job_data.normalized_title,
                "seniority": job_data.seniority_level,
                "job_family": job_data.job_family,
                "required_skills": job_data.required_skills or [],
                "preferred_skills": job_data.preferred_skills or [],
                "responsibilities": job_data.common_responsibilities or [],
                "salary_min": job_data.salary_min,
                "salary_max": job_data.salary_max,
                "salary_median": job_data.salary_median,
                "salary_currency": job_data.salary_currency,
                "experience_min": job_data.min_years_experience,
                "experience_max": job_data.max_years_experience,
                "education": job_data.typical_education or []
            }
            
            # Format salary range
            if result["salary_min"] and result["salary_max"]:
                result["salary_range"] = {
                    "min": result["salary_min"],
                    "max": result["salary_max"],
                    "median": result["salary_median"]
                }
            
            # Format experience range
            if result["experience_min"] is not None:
                result["experience_range"] = {
                    "min": result["experience_min"],
                    "max": result["experience_max"] or result["experience_min"] + 5
                }
            
            logger.info("job_title_data_fetched", title=job_title)
            return result
            
        except Exception as e:
            logger.error("job_title_data_fetch_failed", error=str(e), title=job_title)
            return None
    
    def _fetch_action_verbs(
        self,
        job_family: Optional[str],
        job_title: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Fetch strong action verbs."""
        try:
            # Get high-impact verbs
            verbs = self.crud.get_action_verbs(
                db=self.db,
                impact_level="high",
                min_ats_score=0.7,
                limit=50
            )
            
            # If job title provided, get role-specific verbs
            if job_title:
                role_verbs = self.crud.get_action_verbs_for_role(
                    db=self.db,
                    role=job_title,
                    limit=30
                )
                
                # Combine and deduplicate
                all_verbs = {verb.verb: verb for verb in verbs}
                for verb in role_verbs:
                    if verb.verb not in all_verbs:
                        all_verbs[verb.verb] = verb
                
                verbs = list(all_verbs.values())
            
            # Convert to dict format
            result = []
            for verb in verbs:
                result.append({
                    "verb": verb.verb,
                    "category": verb.category,
                    "impact": verb.impact_level,
                    "ats_score": verb.ats_score,
                    "example": verb.example_usage
                })
            
            # Sort by ATS score
            result.sort(key=lambda x: x["ats_score"], reverse=True)
            
            logger.info("action_verbs_fetched", count=len(result))
            return result
            
        except Exception as e:
            logger.error("action_verbs_fetch_failed", error=str(e))
            return []
    
    def _fetch_industry_metrics(
        self,
        industry: Optional[str],
        job_family: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Fetch industry-standard metrics."""
        try:
            metrics = self.crud.get_industry_metrics(
                db=self.db,
                industry=industry,
                job_family=job_family,
                limit=20
            )
            
            # Convert to dict format
            result = []
            for metric in metrics:
                metric_dict = {
                    "name": metric.metric_name,
                    "type": metric.metric_type,
                    "description": metric.description,
                    "example": metric.example_usage
                }
                
                if metric.typical_min is not None and metric.typical_max is not None:
                    metric_dict["typical_range"] = {
                        "min": metric.typical_min,
                        "max": metric.typical_max
                    }
                
                if metric.exceptional_threshold is not None:
                    metric_dict["exceptional"] = metric.exceptional_threshold
                
                result.append(metric_dict)
            
            logger.info("industry_metrics_fetched", count=len(result))
            return result
            
        except Exception as e:
            logger.error("industry_metrics_fetch_failed", error=str(e))
            return []
    
    def _fetch_certifications(
        self,
        industry: Optional[str],
        job_family: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Fetch relevant certifications."""
        try:
            certs = self.crud.get_certifications(
                db=self.db,
                industry=industry,
                job_family=job_family,
                min_demand=0.5,
                limit=15
            )
            
            # Convert to dict format
            result = []
            for cert in certs:
                result.append({
                    "name": cert.certification_name,
                    "abbreviation": cert.abbreviation,
                    "organization": cert.issuing_organization,
                    "demand": cert.demand_score,
                    "salary_impact": cert.salary_impact
                })
            
            logger.info("certifications_fetched", count=len(result))
            return result
            
        except Exception as e:
            logger.error("certifications_fetch_failed", error=str(e))
            return []
    
    # ============ Helper Methods ============
    
    def _extract_job_title(self, job_description: str) -> Optional[str]:
        """Extract job title from job description."""
        # Simple extraction - look for common patterns
        patterns = [
            r"(?:position|role|title):\s*([^\n]+)",
            r"(?:hiring|seeking)\s+(?:a|an)\s+([^\n]+)",
            r"^([A-Z][^\n]{10,50})\s*(?:\n|$)"  # Title at start
        ]
        
        for pattern in patterns:
            match = re.search(pattern, job_description, re.IGNORECASE | re.MULTILINE)
            if match:
                title = match.group(1).strip()
                # Clean up
                title = re.sub(r'\s+', ' ', title)
                return title[:100]  # Limit length
        
        return None
    
    def _extract_industry(self, job_description: str) -> Optional[str]:
        """Extract industry from job description."""
        # Common industry keywords
        industries = {
            "technology": ["software", "tech", "IT", "computer", "digital"],
            "finance": ["finance", "banking", "investment", "fintech"],
            "healthcare": ["healthcare", "medical", "hospital", "clinical"],
            "retail": ["retail", "e-commerce", "sales"],
            "manufacturing": ["manufacturing", "production", "industrial"],
            "education": ["education", "academic", "university", "school"],
            "marketing": ["marketing", "advertising", "brand"],
            "consulting": ["consulting", "advisory", "strategy"]
        }
        
        jd_lower = job_description.lower()
        
        for industry, keywords in industries.items():
            if any(keyword in jd_lower for keyword in keywords):
                return industry
        
        return None
    
    def _infer_job_family(
        self,
        job_title: Optional[str],
        job_description: str
    ) -> Optional[str]:
        """Infer job family from title and description."""
        text = f"{job_title or ''} {job_description}".lower()
        
        # Job family keywords
        families = {
            "engineering": ["engineer", "developer", "programmer", "software", "technical"],
            "marketing": ["marketing", "brand", "campaign", "content", "social media"],
            "sales": ["sales", "account executive", "business development"],
            "design": ["designer", "UX", "UI", "creative", "visual"],
            "product": ["product manager", "product owner", "PM"],
            "data": ["data scientist", "analyst", "data engineer", "ML", "AI"],
            "operations": ["operations", "logistics", "supply chain"],
            "hr": ["HR", "human resources", "recruiter", "talent"],
            "finance": ["accountant", "financial", "CFO", "controller"]
        }
        
        for family, keywords in families.items():
            if any(keyword in text for keyword in keywords):
                return family
        
        return None
    
    def verify_company(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Verify if a company exists in the database.
        
        Args:
            company_name: Company name to verify
            
        Returns:
            Company data if verified, None otherwise
        """
        try:
            company = self.crud.verify_company(self.db, company_name)
            
            if not company:
                return None
            
            return {
                "name": company.company_name,
                "normalized_name": company.normalized_name,
                "industry": company.industry,
                "size": company.company_size,
                "is_verified": company.is_verified,
                "verification_source": company.verification_source
            }
            
        except Exception as e:
            logger.error("company_verification_failed", error=str(e), company=company_name)
            return None
    
    def verify_institution(self, institution_name: str) -> Optional[Dict[str, Any]]:
        """
        Verify if an educational institution exists.
        
        Args:
            institution_name: Institution name to verify
            
        Returns:
            Institution data if verified, None otherwise
        """
        try:
            institution = self.crud.verify_institution(self.db, institution_name)
            
            if not institution:
                return None
            
            return {
                "name": institution.institution_name,
                "type": institution.institution_type,
                "country": institution.country,
                "is_accredited": institution.is_accredited,
                "accreditation_body": institution.accreditation_body
            }
            
        except Exception as e:
            logger.error("institution_verification_failed", error=str(e), institution=institution_name)
            return None


def create_grounding_service(db: Session) -> GroundingService:
    """
    Factory function to create grounding service.
    
    Args:
        db: Database session
        
    Returns:
        GroundingService instance
    """
    return GroundingService(db)
