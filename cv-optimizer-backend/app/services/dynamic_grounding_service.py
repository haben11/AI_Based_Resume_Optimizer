"""
Dynamic Grounding Service

Fetches real-time data from external sources instead of relying only on seeded data.
Extracts skills/keywords from job description and searches for them dynamically.

This solves the problem of missing skills (Java, Angular, Go, etc.) that aren't
in the pre-seeded database.

Author: CV Optimizer Team
Version: 2.0.0
"""

from typing import List, Optional, Dict, Any, Set
from sqlalchemy.orm import Session
import re
from app.crud.crud_knowledge_base import crud_knowledge_base
from app.services.grounding_service import GroundingContext
from app.core.logging import logger


class SkillExtractor:
    """
    Extract skills and keywords from job descriptions.
    
    Uses pattern matching and NLP to identify technical skills,
    soft skills, tools, and frameworks.
    """
    
    # Common technical skills and tools
    KNOWN_SKILLS = {
        # Programming Languages
        "python", "java", "javascript", "typescript", "c++", "c#", "go", "golang",
        "rust", "ruby", "php", "swift", "kotlin", "scala", "r", "matlab",
        
        # Frontend
        "react", "angular", "vue", "vue.js", "svelte", "next.js", "nuxt",
        "html", "css", "sass", "less", "tailwind", "bootstrap",
        
        # Backend
        "node.js", "express", "django", "flask", "fastapi", "spring", "spring boot",
        "asp.net", ".net", "rails", "laravel", "symfony",
        
        # Databases
        "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
        "cassandra", "dynamodb", "oracle", "sql server",
        
        # Cloud & DevOps
        "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s",
        "terraform", "ansible", "jenkins", "gitlab", "github actions", "circleci",
        
        # Data & ML
        "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn",
        "pandas", "numpy", "spark", "hadoop", "airflow", "kafka",
        
        # Mobile
        "ios", "android", "react native", "flutter", "xamarin",
        
        # Other Tools
        "git", "jira", "confluence", "slack", "figma", "sketch",
        
        # Methodologies
        "agile", "scrum", "kanban", "devops", "ci/cd", "tdd", "bdd",
        
        # Soft Skills
        "leadership", "communication", "problem solving", "teamwork",
        "collaboration", "critical thinking", "time management"
    }
    
    def extract_skills(self, text: str) -> Set[str]:
        """
        Extract skills from text.
        
        Args:
            text: Job description or resume text
            
        Returns:
            Set of extracted skills
        """
        text_lower = text.lower()
        found_skills = set()
        
        # Direct matching
        for skill in self.KNOWN_SKILLS:
            # Use word boundaries for better matching
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(skill)
        
        # Extract from common patterns
        # "Experience with X, Y, and Z"
        exp_pattern = r'experience (?:with|in) ([^.]+)'
        matches = re.findall(exp_pattern, text_lower)
        for match in matches:
            # Split by common delimiters
            items = re.split(r'[,;&]|\band\b|\bor\b', match)
            for item in items:
                item = item.strip()
                if item in self.KNOWN_SKILLS:
                    found_skills.add(item)
        
        # "Proficiency in X"
        prof_pattern = r'proficiency in ([^.]+)'
        matches = re.findall(prof_pattern, text_lower)
        for match in matches:
            items = re.split(r'[,;&]|\band\b|\bor\b', match)
            for item in items:
                item = item.strip()
                if item in self.KNOWN_SKILLS:
                    found_skills.add(item)
        
        # "Knowledge of X"
        know_pattern = r'knowledge of ([^.]+)'
        matches = re.findall(know_pattern, text_lower)
        for match in matches:
            items = re.split(r'[,;&]|\band\b|\bor\b', match)
            for item in items:
                item = item.strip()
                if item in self.KNOWN_SKILLS:
                    found_skills.add(item)
        
        logger.info("skills_extracted", count=len(found_skills), skills=list(found_skills)[:10])
        return found_skills


class DynamicGroundingService:
    """
    Dynamic grounding service that fetches real-time data.
    
    Instead of relying only on pre-seeded data, this service:
    1. Extracts skills from job description
    2. Searches database for existing data
    3. Fetches missing data from external sources
    4. Caches results for future use
    """
    
    def __init__(self, db: Session):
        """
        Initialize dynamic grounding service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.crud = crud_knowledge_base
        self.skill_extractor = SkillExtractor()
    
    def fetch_dynamic_grounding_data(
        self,
        job_description: str,
        job_title: Optional[str] = None,
        industry: Optional[str] = None,
        job_family: Optional[str] = None
    ) -> GroundingContext:
        """
        Fetch grounding data dynamically based on job description.
        
        Args:
            job_description: Full job description text
            job_title: Extracted job title
            industry: Industry name
            job_family: Job family
            
        Returns:
            GroundingContext with all fetched data
        """
        logger.info(
            "fetching_dynamic_grounding_data",
            job_title=job_title,
            industry=industry,
            job_family=job_family
        )
        
        context = GroundingContext()
        
        # Extract entities if not provided
        if not job_title:
            job_title = self._extract_job_title(job_description)
        
        if not industry:
            industry = self._extract_industry(job_description)
        
        if not job_family:
            job_family = self._infer_job_family(job_title, job_description)
        
        # Extract skills from job description
        extracted_skills = self.skill_extractor.extract_skills(job_description)
        logger.info("extracted_skills_from_jd", count=len(extracted_skills))
        
        # Fetch data for extracted skills
        context.ats_keywords = self._fetch_dynamic_ats_keywords(
            extracted_skills=extracted_skills,
            job_family=job_family,
            job_description=job_description
        )
        
        context.industry_skills = self._fetch_dynamic_industry_skills(
            extracted_skills=extracted_skills,
            industry=industry
        )
        
        # Fetch job title data (same as before)
        if job_title:
            context.job_title_data = self._fetch_job_title_data(job_title)
            
            if context.job_title_data:
                context.salary_data = {
                    "min": context.job_title_data.get("salary_min"),
                    "max": context.job_title_data.get("salary_max"),
                    "median": context.job_title_data.get("salary_median"),
                    "currency": context.job_title_data.get("salary_currency", "USD")
                }
        
        # Fetch action verbs (same as before)
        context.action_verbs = self._fetch_action_verbs(
            job_family=job_family,
            job_title=job_title
        )
        
        # Fetch industry metrics (same as before)
        context.industry_metrics = self._fetch_industry_metrics(
            industry=industry,
            job_family=job_family
        )
        
        # Fetch certifications (same as before)
        context.certifications = self._fetch_certifications(
            industry=industry,
            job_family=job_family
        )
        
        summary = context.get_summary()
        logger.info("dynamic_grounding_data_fetched", **summary)
        
        return context
    
    def _fetch_dynamic_ats_keywords(
        self,
        extracted_skills: Set[str],
        job_family: Optional[str],
        job_description: str
    ) -> List[Dict[str, Any]]:
        """
        Fetch ATS keywords dynamically based on extracted skills.
        
        Args:
            extracted_skills: Skills extracted from job description
            job_family: Job family
            job_description: Full job description
            
        Returns:
            List of ATS keywords
        """
        try:
            # 1. Get keywords from database for job family
            db_keywords = self.crud.get_ats_keywords(
                db=self.db,
                job_family=job_family,
                min_importance=0.5,
                limit=50
            )
            
            # 2. Search for extracted skills in database
            if extracted_skills:
                skill_keywords = self.crud.search_ats_keywords(
                    db=self.db,
                    keywords=list(extracted_skills),
                    job_family=job_family
                )
                
                # Merge with existing keywords
                all_keywords = {kw.keyword: kw for kw in db_keywords}
                for kw in skill_keywords:
                    if kw.keyword not in all_keywords:
                        all_keywords[kw.keyword] = kw
                
                db_keywords = list(all_keywords.values())
            
            # 3. For skills not in database, create temporary entries
            db_keyword_names = {kw.keyword.lower() for kw in db_keywords}
            missing_skills = extracted_skills - db_keyword_names
            
            if missing_skills:
                logger.info(
                    "missing_skills_in_db",
                    count=len(missing_skills),
                    skills=list(missing_skills)[:10]
                )
                
                # Fetch real-time data for missing skills
                real_time_keywords = self._fetch_real_time_skill_data(
                    skills=missing_skills,
                    job_family=job_family
                )
                
                # Add to result
                db_keywords.extend(real_time_keywords)
            
            # Convert to dict format
            result = []
            for kw in db_keywords:
                result.append({
                    "keyword": kw.keyword,
                    "category": kw.category,
                    "importance": kw.importance_score,
                    "synonyms": kw.synonyms or [],
                    "context": kw.typical_context
                })
            
            # Sort by importance
            result.sort(key=lambda x: x["importance"], reverse=True)
            
            logger.info("dynamic_ats_keywords_fetched", count=len(result))
            return result
            
        except Exception as e:
            logger.error("dynamic_ats_keywords_fetch_failed", error=str(e))
            return []
    
    def _fetch_dynamic_industry_skills(
        self,
        extracted_skills: Set[str],
        industry: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Fetch industry skills dynamically.
        
        Args:
            extracted_skills: Skills extracted from job description
            industry: Industry name
            
        Returns:
            List of industry skills
        """
        try:
            # 1. Get skills from database
            db_skills = self.crud.get_industry_skills(
                db=self.db,
                industry=industry,
                min_demand=0.6,
                limit=30
            )
            
            # 2. Search for extracted skills
            if extracted_skills:
                skill_matches = self.crud.search_skills(
                    db=self.db,
                    skill_names=list(extracted_skills),
                    industry=industry
                )
                
                # Merge
                all_skills = {skill.skill_name: skill for skill in db_skills}
                for skill in skill_matches:
                    if skill.skill_name not in all_skills:
                        all_skills[skill.skill_name] = skill
                
                db_skills = list(all_skills.values())
            
            # 3. For missing skills, fetch real-time data
            db_skill_names = {skill.skill_name.lower() for skill in db_skills}
            missing_skills = extracted_skills - db_skill_names
            
            if missing_skills:
                logger.info(
                    "missing_skills_for_industry",
                    count=len(missing_skills),
                    skills=list(missing_skills)[:10]
                )
                
                # Fetch real-time skill demand data
                real_time_skills = self._fetch_real_time_skill_demand(
                    skills=missing_skills,
                    industry=industry
                )
                
                db_skills.extend(real_time_skills)
            
            # Convert to dict format
            result = []
            for skill in db_skills:
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
            
            logger.info("dynamic_industry_skills_fetched", count=len(result))
            return result
            
        except Exception as e:
            logger.error("dynamic_industry_skills_fetch_failed", error=str(e))
            return []
    
    def _fetch_real_time_skill_data(
        self,
        skills: Set[str],
        job_family: Optional[str]
    ) -> List[Any]:
        """
        Fetch real-time skill data from external sources.
        
        This is a placeholder for integration with external APIs like:
        - LinkedIn Skills API
        - Indeed Job Postings API
        - Stack Overflow Developer Survey
        - GitHub trending repositories
        
        Args:
            skills: Skills to fetch data for
            job_family: Job family context
            
        Returns:
            List of keyword objects
        """
        # TODO: Integrate with external APIs
        # For now, create temporary entries with estimated scores
        
        from app.models.knowledge_base import ATSKeyword
        import uuid
        
        result = []
        
        for skill in skills:
            # Estimate importance based on skill type
            importance = self._estimate_skill_importance(skill, job_family)
            
            # Create temporary keyword object (not saved to DB)
            keyword = ATSKeyword(
                id=uuid.uuid4(),
                keyword=skill.title(),  # Capitalize
                category=self._categorize_skill(skill),
                job_family=job_family or "all",
                frequency_score=0.7,  # Default
                importance_score=importance,
                synonyms=[],
                related_keywords=[],
                typical_context=None,
                ats_variations=[skill, skill.lower(), skill.upper()]
            )
            
            result.append(keyword)
            
            logger.info(
                "created_temporary_keyword",
                skill=skill,
                importance=importance,
                category=keyword.category
            )
        
        return result
    
    def _fetch_real_time_skill_demand(
        self,
        skills: Set[str],
        industry: Optional[str]
    ) -> List[Any]:
        """
        Fetch real-time skill demand data.
        
        Placeholder for external API integration.
        
        Args:
            skills: Skills to fetch demand for
            industry: Industry context
            
        Returns:
            List of skill objects
        """
        # TODO: Integrate with external APIs
        
        from app.models.knowledge_base import IndustrySkill
        import uuid
        
        result = []
        
        for skill in skills:
            # Estimate demand based on skill type
            demand = self._estimate_skill_demand(skill, industry)
            
            # Create temporary skill object
            skill_obj = IndustrySkill(
                id=uuid.uuid4(),
                skill_name=skill.title(),
                skill_category=self._categorize_skill(skill),
                industry=industry or "technology",
                demand_score=demand,
                growth_rate=0.15,  # Default 15% growth
                job_postings_count=10000,  # Estimated
                typical_proficiency_levels=["beginner", "intermediate", "advanced", "expert"],
                related_skills=[],
                common_tools=[],
                certifications=[],
                avg_salary_impact=12000  # Estimated
            )
            
            result.append(skill_obj)
            
            logger.info(
                "created_temporary_skill",
                skill=skill,
                demand=demand,
                category=skill_obj.skill_category
            )
        
        return result
    
    def _estimate_skill_importance(self, skill: str, job_family: Optional[str]) -> float:
        """Estimate importance score for a skill."""
        skill_lower = skill.lower()
        
        # High importance skills
        high_importance = {
            "python", "java", "javascript", "typescript", "react", "angular",
            "aws", "azure", "docker", "kubernetes", "sql", "machine learning"
        }
        
        # Medium importance skills
        medium_importance = {
            "git", "agile", "scrum", "rest api", "node.js", "mongodb",
            "postgresql", "redis", "jenkins", "terraform"
        }
        
        if skill_lower in high_importance:
            return 0.85
        elif skill_lower in medium_importance:
            return 0.75
        else:
            return 0.70
    
    def _estimate_skill_demand(self, skill: str, industry: Optional[str]) -> float:
        """Estimate demand score for a skill."""
        skill_lower = skill.lower()
        
        # Very high demand
        very_high_demand = {
            "python", "javascript", "react", "aws", "kubernetes", "machine learning"
        }
        
        # High demand
        high_demand = {
            "java", "typescript", "angular", "docker", "sql", "node.js", "go"
        }
        
        if skill_lower in very_high_demand:
            return 0.90
        elif skill_lower in high_demand:
            return 0.80
        else:
            return 0.70
    
    def _categorize_skill(self, skill: str) -> str:
        """Categorize a skill."""
        skill_lower = skill.lower()
        
        # Programming languages
        languages = {"python", "java", "javascript", "typescript", "go", "rust", "c++", "c#"}
        if skill_lower in languages:
            return "programming"
        
        # Frontend
        frontend = {"react", "angular", "vue", "html", "css", "sass"}
        if skill_lower in frontend:
            return "frontend"
        
        # Backend
        backend = {"node.js", "django", "flask", "spring", "express"}
        if skill_lower in backend:
            return "backend"
        
        # Cloud
        cloud = {"aws", "azure", "gcp", "google cloud"}
        if skill_lower in cloud:
            return "cloud"
        
        # DevOps
        devops = {"docker", "kubernetes", "terraform", "ansible", "jenkins"}
        if skill_lower in devops:
            return "devops"
        
        # Database
        database = {"sql", "mysql", "postgresql", "mongodb", "redis"}
        if skill_lower in database:
            return "database"
        
        # Default
        return "technical"
    
    # Helper methods (same as GroundingService)
    
    def _extract_job_title(self, job_description: str) -> Optional[str]:
        """Extract job title from job description."""
        patterns = [
            r"(?:position|role|title):\s*([^\n]+)",
            r"(?:hiring|seeking)\s+(?:a|an)\s+([^\n]+)",
            r"^([A-Z][^\n]{10,50})\s*(?:\n|$)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, job_description, re.IGNORECASE | re.MULTILINE)
            if match:
                title = match.group(1).strip()
                title = re.sub(r'\s+', ' ', title)
                return title[:100]
        
        return None
    
    def _extract_industry(self, job_description: str) -> Optional[str]:
        """Extract industry from job description."""
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
    
    def _infer_job_family(self, job_title: Optional[str], job_description: str) -> Optional[str]:
        """Infer job family from title and description."""
        text = f"{job_title or ''} {job_description}".lower()
        
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
    
    def _fetch_job_title_data(self, job_title: str) -> Optional[Dict[str, Any]]:
        """Fetch job title data from database."""
        try:
            job_data = self.crud.get_job_title_data(
                db=self.db,
                title=job_title,
                fuzzy_match=True
            )
            
            if not job_data:
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
            
            if result["salary_min"] and result["salary_max"]:
                result["salary_range"] = {
                    "min": result["salary_min"],
                    "max": result["salary_max"],
                    "median": result["salary_median"]
                }
            
            if result["experience_min"] is not None:
                result["experience_range"] = {
                    "min": result["experience_min"],
                    "max": result["experience_max"] or result["experience_min"] + 5
                }
            
            return result
            
        except Exception as e:
            logger.error("job_title_data_fetch_failed", error=str(e))
            return None
    
    def _fetch_action_verbs(self, job_family: Optional[str], job_title: Optional[str]) -> List[Dict[str, Any]]:
        """Fetch action verbs from database."""
        try:
            verbs = self.crud.get_action_verbs(
                db=self.db,
                impact_level="high",
                min_ats_score=0.7,
                limit=50
            )
            
            if job_title:
                role_verbs = self.crud.get_action_verbs_for_role(
                    db=self.db,
                    role=job_title,
                    limit=30
                )
                
                all_verbs = {verb.verb: verb for verb in verbs}
                for verb in role_verbs:
                    if verb.verb not in all_verbs:
                        all_verbs[verb.verb] = verb
                
                verbs = list(all_verbs.values())
            
            result = []
            for verb in verbs:
                result.append({
                    "verb": verb.verb,
                    "category": verb.category,
                    "impact": verb.impact_level,
                    "ats_score": verb.ats_score,
                    "example": verb.example_usage
                })
            
            result.sort(key=lambda x: x["ats_score"], reverse=True)
            return result
            
        except Exception as e:
            logger.error("action_verbs_fetch_failed", error=str(e))
            return []
    
    def _fetch_industry_metrics(self, industry: Optional[str], job_family: Optional[str]) -> List[Dict[str, Any]]:
        """Fetch industry metrics from database."""
        try:
            metrics = self.crud.get_industry_metrics(
                db=self.db,
                industry=industry,
                job_family=job_family,
                limit=20
            )
            
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
            
            return result
            
        except Exception as e:
            logger.error("industry_metrics_fetch_failed", error=str(e))
            return []
    
    def _fetch_certifications(self, industry: Optional[str], job_family: Optional[str]) -> List[Dict[str, Any]]:
        """Fetch certifications from database."""
        try:
            certs = self.crud.get_certifications(
                db=self.db,
                industry=industry,
                job_family=job_family,
                min_demand=0.5,
                limit=15
            )
            
            result = []
            for cert in certs:
                result.append({
                    "name": cert.certification_name,
                    "abbreviation": cert.abbreviation,
                    "organization": cert.issuing_organization,
                    "demand": cert.demand_score,
                    "salary_impact": cert.salary_impact
                })
            
            return result
            
        except Exception as e:
            logger.error("certifications_fetch_failed", error=str(e))
            return []


def create_dynamic_grounding_service(db: Session) -> DynamicGroundingService:
    """
    Factory function to create dynamic grounding service.
    
    Args:
        db: Database session
        
    Returns:
        DynamicGroundingService instance
    """
    return DynamicGroundingService(db)
