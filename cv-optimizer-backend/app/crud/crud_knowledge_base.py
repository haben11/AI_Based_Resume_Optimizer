"""
CRUD Operations for Knowledge Base

Provides data access layer for external grounding data.
Prevents hallucination by fetching verified information.

Author: CV Optimizer Team
Version: 1.0.0
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.models.knowledge_base import (
    ATSKeyword,
    IndustrySkill,
    JobTitleData,
    ActionVerb,
    IndustryMetric,
    CompanyData,
    CertificationData,
    EducationData
)


class CRUDKnowledgeBase:
    """CRUD operations for knowledge base tables."""
    
    # ============ ATS Keywords ============
    
    def get_ats_keywords(
        self,
        db: Session,
        job_family: Optional[str] = None,
        category: Optional[str] = None,
        min_importance: float = 0.0,
        limit: int = 100
    ) -> List[ATSKeyword]:
        """
        Fetch ATS keywords with optional filtering.
        
        Args:
            db: Database session
            job_family: Filter by job family (e.g., 'engineering')
            category: Filter by category (e.g., 'technical')
            min_importance: Minimum importance score
            limit: Maximum results
            
        Returns:
            List of ATS keywords
        """
        query = db.query(ATSKeyword).filter(
            ATSKeyword.importance_score >= min_importance
        )
        
        if job_family:
            query = query.filter(ATSKeyword.job_family == job_family)
        
        if category:
            query = query.filter(ATSKeyword.category == category)
        
        return query.order_by(ATSKeyword.importance_score.desc()).limit(limit).all()
    
    def search_ats_keywords(
        self,
        db: Session,
        keywords: List[str],
        job_family: Optional[str] = None
    ) -> List[ATSKeyword]:
        """
        Search for specific ATS keywords.
        
        Args:
            db: Database session
            keywords: List of keywords to search for
            job_family: Optional job family filter
            
        Returns:
            Matching ATS keywords
        """
        query = db.query(ATSKeyword).filter(
            or_(
                ATSKeyword.keyword.in_(keywords),
                ATSKeyword.synonyms.overlap(keywords)
            )
        )
        
        if job_family:
            query = query.filter(ATSKeyword.job_family == job_family)
        
        return query.all()
    
    # ============ Industry Skills ============
    
    def get_industry_skills(
        self,
        db: Session,
        industry: Optional[str] = None,
        category: Optional[str] = None,
        min_demand: float = 0.0,
        limit: int = 100
    ) -> List[IndustrySkill]:
        """
        Fetch industry skills with optional filtering.
        
        Args:
            db: Database session
            industry: Filter by industry
            category: Filter by skill category
            min_demand: Minimum demand score
            limit: Maximum results
            
        Returns:
            List of industry skills
        """
        query = db.query(IndustrySkill).filter(
            IndustrySkill.demand_score >= min_demand
        )
        
        if industry:
            query = query.filter(IndustrySkill.industry == industry)
        
        if category:
            query = query.filter(IndustrySkill.skill_category == category)
        
        return query.order_by(IndustrySkill.demand_score.desc()).limit(limit).all()
    
    def search_skills(
        self,
        db: Session,
        skill_names: List[str],
        industry: Optional[str] = None
    ) -> List[IndustrySkill]:
        """
        Search for specific skills.
        
        Args:
            db: Database session
            skill_names: List of skill names to search for
            industry: Optional industry filter
            
        Returns:
            Matching skills
        """
        query = db.query(IndustrySkill).filter(
            IndustrySkill.skill_name.in_(skill_names)
        )
        
        if industry:
            query = query.filter(IndustrySkill.industry == industry)
        
        return query.all()
    
    def get_trending_skills(
        self,
        db: Session,
        industry: Optional[str] = None,
        min_growth_rate: float = 0.1,
        limit: int = 50
    ) -> List[IndustrySkill]:
        """
        Get trending skills with high growth rates.
        
        Args:
            db: Database session
            industry: Optional industry filter
            min_growth_rate: Minimum growth rate (e.g., 0.1 = 10%)
            limit: Maximum results
            
        Returns:
            List of trending skills
        """
        query = db.query(IndustrySkill).filter(
            IndustrySkill.growth_rate >= min_growth_rate
        )
        
        if industry:
            query = query.filter(IndustrySkill.industry == industry)
        
        return query.order_by(IndustrySkill.growth_rate.desc()).limit(limit).all()
    
    # ============ Job Title Data ============
    
    def get_job_title_data(
        self,
        db: Session,
        title: str,
        fuzzy_match: bool = True
    ) -> Optional[JobTitleData]:
        """
        Get data for a specific job title.
        
        Args:
            db: Database session
            title: Job title to search for
            fuzzy_match: Use fuzzy matching
            
        Returns:
            Job title data or None
        """
        if fuzzy_match:
            # Try normalized title first
            result = db.query(JobTitleData).filter(
                JobTitleData.normalized_title.ilike(f"%{title}%")
            ).first()
            
            if not result:
                # Try exact title
                result = db.query(JobTitleData).filter(
                    JobTitleData.title.ilike(f"%{title}%")
                ).first()
            
            return result
        else:
            return db.query(JobTitleData).filter(
                JobTitleData.title == title
            ).first()
    
    def get_job_titles_by_family(
        self,
        db: Session,
        job_family: str,
        seniority_level: Optional[str] = None,
        limit: int = 50
    ) -> List[JobTitleData]:
        """
        Get job titles by family and optional seniority.
        
        Args:
            db: Database session
            job_family: Job family (e.g., 'engineering')
            seniority_level: Optional seniority filter
            limit: Maximum results
            
        Returns:
            List of job titles
        """
        query = db.query(JobTitleData).filter(
            JobTitleData.job_family == job_family
        )
        
        if seniority_level:
            query = query.filter(JobTitleData.seniority_level == seniority_level)
        
        return query.limit(limit).all()
    
    # ============ Action Verbs ============
    
    def get_action_verbs(
        self,
        db: Session,
        category: Optional[str] = None,
        impact_level: Optional[str] = None,
        min_ats_score: float = 0.0,
        limit: int = 100
    ) -> List[ActionVerb]:
        """
        Fetch action verbs with optional filtering.
        
        Args:
            db: Database session
            category: Filter by category (e.g., 'leadership')
            impact_level: Filter by impact level ('high', 'medium', 'low')
            min_ats_score: Minimum ATS score
            limit: Maximum results
            
        Returns:
            List of action verbs
        """
        query = db.query(ActionVerb).filter(
            ActionVerb.ats_score >= min_ats_score
        )
        
        if category:
            query = query.filter(ActionVerb.category == category)
        
        if impact_level:
            query = query.filter(ActionVerb.impact_level == impact_level)
        
        return query.order_by(ActionVerb.ats_score.desc()).limit(limit).all()
    
    def get_action_verbs_for_role(
        self,
        db: Session,
        role: str,
        limit: int = 50
    ) -> List[ActionVerb]:
        """
        Get action verbs suitable for a specific role.
        
        Args:
            db: Database session
            role: Role name
            limit: Maximum results
            
        Returns:
            List of suitable action verbs
        """
        return db.query(ActionVerb).filter(
            ActionVerb.best_for_roles.any(role)
        ).order_by(ActionVerb.ats_score.desc()).limit(limit).all()
    
    # ============ Industry Metrics ============
    
    def get_industry_metrics(
        self,
        db: Session,
        industry: Optional[str] = None,
        job_family: Optional[str] = None,
        metric_type: Optional[str] = None,
        limit: int = 100
    ) -> List[IndustryMetric]:
        """
        Fetch industry metrics with optional filtering.
        
        Args:
            db: Database session
            industry: Filter by industry
            job_family: Filter by job family
            metric_type: Filter by metric type
            limit: Maximum results
            
        Returns:
            List of industry metrics
        """
        query = db.query(IndustryMetric)
        
        if industry:
            query = query.filter(IndustryMetric.industry == industry)
        
        if job_family:
            query = query.filter(IndustryMetric.job_family == job_family)
        
        if metric_type:
            query = query.filter(IndustryMetric.metric_type == metric_type)
        
        return query.limit(limit).all()
    
    # ============ Company Data ============
    
    def verify_company(
        self,
        db: Session,
        company_name: str
    ) -> Optional[CompanyData]:
        """
        Verify if a company exists in the database.
        
        Args:
            db: Database session
            company_name: Company name to verify
            
        Returns:
            Company data if found, None otherwise
        """
        # Try exact match first
        result = db.query(CompanyData).filter(
            CompanyData.company_name == company_name
        ).first()
        
        if not result:
            # Try normalized name
            result = db.query(CompanyData).filter(
                CompanyData.normalized_name.ilike(f"%{company_name}%")
            ).first()
        
        if not result:
            # Try name variations
            result = db.query(CompanyData).filter(
                CompanyData.name_variations.any(company_name)
            ).first()
        
        return result
    
    def get_companies_by_industry(
        self,
        db: Session,
        industry: str,
        verified_only: bool = True,
        limit: int = 100
    ) -> List[CompanyData]:
        """
        Get companies by industry.
        
        Args:
            db: Database session
            industry: Industry name
            verified_only: Only return verified companies
            limit: Maximum results
            
        Returns:
            List of companies
        """
        query = db.query(CompanyData).filter(
            CompanyData.industry == industry
        )
        
        if verified_only:
            query = query.filter(CompanyData.is_verified == True)
        
        return query.limit(limit).all()
    
    # ============ Certification Data ============
    
    def get_certifications(
        self,
        db: Session,
        industry: Optional[str] = None,
        job_family: Optional[str] = None,
        min_demand: float = 0.0,
        limit: int = 100
    ) -> List[CertificationData]:
        """
        Fetch certifications with optional filtering.
        
        Args:
            db: Database session
            industry: Filter by industry
            job_family: Filter by job family
            min_demand: Minimum demand score
            limit: Maximum results
            
        Returns:
            List of certifications
        """
        query = db.query(CertificationData).filter(
            CertificationData.demand_score >= min_demand
        )
        
        if industry:
            query = query.filter(CertificationData.industry == industry)
        
        if job_family:
            query = query.filter(CertificationData.job_families.any(job_family))
        
        return query.order_by(CertificationData.demand_score.desc()).limit(limit).all()
    
    def search_certifications(
        self,
        db: Session,
        cert_name: str
    ) -> Optional[CertificationData]:
        """
        Search for a specific certification.
        
        Args:
            db: Database session
            cert_name: Certification name or abbreviation
            
        Returns:
            Certification data if found
        """
        # Try exact name match
        result = db.query(CertificationData).filter(
            CertificationData.certification_name.ilike(f"%{cert_name}%")
        ).first()
        
        if not result:
            # Try abbreviation
            result = db.query(CertificationData).filter(
                CertificationData.abbreviation.ilike(f"%{cert_name}%")
            ).first()
        
        return result
    
    # ============ Education Data ============
    
    def verify_institution(
        self,
        db: Session,
        institution_name: str
    ) -> Optional[EducationData]:
        """
        Verify if an educational institution exists.
        
        Args:
            db: Database session
            institution_name: Institution name to verify
            
        Returns:
            Education data if found
        """
        # Try exact match
        result = db.query(EducationData).filter(
            EducationData.institution_name.ilike(f"%{institution_name}%")
        ).first()
        
        if not result:
            # Try name variations
            result = db.query(EducationData).filter(
                EducationData.name_variations.any(institution_name)
            ).first()
        
        return result
    
    def get_institutions_by_country(
        self,
        db: Session,
        country: str,
        accredited_only: bool = True,
        limit: int = 100
    ) -> List[EducationData]:
        """
        Get educational institutions by country.
        
        Args:
            db: Database session
            country: Country name
            accredited_only: Only return accredited institutions
            limit: Maximum results
            
        Returns:
            List of institutions
        """
        query = db.query(EducationData).filter(
            EducationData.country == country
        )
        
        if accredited_only:
            query = query.filter(EducationData.is_accredited == True)
        
        return query.limit(limit).all()


# Singleton instance
crud_knowledge_base = CRUDKnowledgeBase()
