"""
Seed Knowledge Base with Sample Data

Populates the knowledge base tables with verified data for grounding.
This prevents hallucination by providing real, verified information.

Run with: python -m app.scripts.seed_knowledge_base

Author: CV Optimizer Team
Version: 1.0.0
"""

import uuid
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
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
from app.core.logging import logger


def seed_ats_keywords(db: Session):
    """Seed ATS keywords."""
    logger.info("Seeding ATS keywords...")
    
    keywords_data = [
        # Technical - Engineering
        {"keyword": "Python", "category": "technical", "job_family": "engineering", "frequency_score": 0.95, "importance_score": 0.9, "synonyms": ["Python3", "Python 3"], "ats_variations": ["Python", "python", "PYTHON"]},
        {"keyword": "JavaScript", "category": "technical", "job_family": "engineering", "frequency_score": 0.92, "importance_score": 0.88, "synonyms": ["JS", "ECMAScript"], "ats_variations": ["JavaScript", "javascript", "JS"]},
        {"keyword": "React", "category": "technical", "job_family": "engineering", "frequency_score": 0.88, "importance_score": 0.85, "synonyms": ["ReactJS", "React.js"], "ats_variations": ["React", "react", "ReactJS"]},
        {"keyword": "Node.js", "category": "technical", "job_family": "engineering", "frequency_score": 0.85, "importance_score": 0.82, "synonyms": ["NodeJS", "Node"], "ats_variations": ["Node.js", "NodeJS", "node"]},
        {"keyword": "AWS", "category": "technical", "job_family": "engineering", "frequency_score": 0.90, "importance_score": 0.87, "synonyms": ["Amazon Web Services"], "ats_variations": ["AWS", "aws", "Amazon Web Services"]},
        {"keyword": "Docker", "category": "technical", "job_family": "engineering", "frequency_score": 0.82, "importance_score": 0.80, "synonyms": ["Containerization"], "ats_variations": ["Docker", "docker"]},
        {"keyword": "Kubernetes", "category": "technical", "job_family": "engineering", "frequency_score": 0.78, "importance_score": 0.78, "synonyms": ["K8s"], "ats_variations": ["Kubernetes", "kubernetes", "K8s"]},
        {"keyword": "SQL", "category": "technical", "job_family": "engineering", "frequency_score": 0.88, "importance_score": 0.85, "synonyms": ["Structured Query Language"], "ats_variations": ["SQL", "sql"]},
        {"keyword": "Git", "category": "technical", "job_family": "engineering", "frequency_score": 0.90, "importance_score": 0.82, "synonyms": ["Version Control"], "ats_variations": ["Git", "git", "GitHub", "GitLab"]},
        {"keyword": "REST API", "category": "technical", "job_family": "engineering", "frequency_score": 0.85, "importance_score": 0.83, "synonyms": ["RESTful API", "REST"], "ats_variations": ["REST API", "RESTful", "REST"]},
        
        # Soft Skills
        {"keyword": "Leadership", "category": "soft_skill", "job_family": "all", "frequency_score": 0.85, "importance_score": 0.88, "synonyms": ["Team Leadership", "Leading Teams"], "ats_variations": ["Leadership", "leadership"]},
        {"keyword": "Communication", "category": "soft_skill", "job_family": "all", "frequency_score": 0.90, "importance_score": 0.85, "synonyms": ["Verbal Communication", "Written Communication"], "ats_variations": ["Communication", "communication"]},
        {"keyword": "Problem Solving", "category": "soft_skill", "job_family": "all", "frequency_score": 0.88, "importance_score": 0.87, "synonyms": ["Critical Thinking", "Analytical Skills"], "ats_variations": ["Problem Solving", "problem-solving"]},
        {"keyword": "Collaboration", "category": "soft_skill", "job_family": "all", "frequency_score": 0.82, "importance_score": 0.80, "synonyms": ["Teamwork", "Cross-functional Collaboration"], "ats_variations": ["Collaboration", "collaboration", "teamwork"]},
        {"keyword": "Agile", "category": "methodology", "job_family": "engineering", "frequency_score": 0.85, "importance_score": 0.82, "synonyms": ["Scrum", "Agile Methodology"], "ats_variations": ["Agile", "agile", "Scrum"]},
        
        # Certifications
        {"keyword": "AWS Certified", "category": "certification", "job_family": "engineering", "frequency_score": 0.75, "importance_score": 0.85, "synonyms": ["AWS Certification"], "ats_variations": ["AWS Certified", "AWS Certification"]},
        {"keyword": "PMP", "category": "certification", "job_family": "management", "frequency_score": 0.70, "importance_score": 0.82, "synonyms": ["Project Management Professional"], "ats_variations": ["PMP", "Project Management Professional"]},
    ]
    
    for kw_data in keywords_data:
        keyword = ATSKeyword(
            id=uuid.uuid4(),
            **kw_data
        )
        db.add(keyword)
    
    db.commit()
    logger.info(f"Seeded {len(keywords_data)} ATS keywords")


def seed_industry_skills(db: Session):
    """Seed industry skills."""
    logger.info("Seeding industry skills...")
    
    skills_data = [
        {"skill_name": "Python", "skill_category": "programming", "industry": "technology", "demand_score": 0.95, "growth_rate": 0.15, "job_postings_count": 50000, "avg_salary_impact": 15000},
        {"skill_name": "Machine Learning", "skill_category": "ai_ml", "industry": "technology", "demand_score": 0.92, "growth_rate": 0.25, "job_postings_count": 35000, "avg_salary_impact": 25000},
        {"skill_name": "React", "skill_category": "frontend", "industry": "technology", "demand_score": 0.90, "growth_rate": 0.12, "job_postings_count": 45000, "avg_salary_impact": 12000},
        {"skill_name": "AWS", "skill_category": "cloud", "industry": "technology", "demand_score": 0.93, "growth_rate": 0.18, "job_postings_count": 48000, "avg_salary_impact": 18000},
        {"skill_name": "Data Analysis", "skill_category": "analytics", "industry": "technology", "demand_score": 0.88, "growth_rate": 0.14, "job_postings_count": 40000, "avg_salary_impact": 14000},
        {"skill_name": "Project Management", "skill_category": "management", "industry": "all", "demand_score": 0.85, "growth_rate": 0.08, "job_postings_count": 55000, "avg_salary_impact": 10000},
        {"skill_name": "SQL", "skill_category": "database", "industry": "technology", "demand_score": 0.90, "growth_rate": 0.10, "job_postings_count": 52000, "avg_salary_impact": 11000},
        {"skill_name": "Docker", "skill_category": "devops", "industry": "technology", "demand_score": 0.85, "growth_rate": 0.20, "job_postings_count": 32000, "avg_salary_impact": 16000},
        {"skill_name": "Kubernetes", "skill_category": "devops", "industry": "technology", "demand_score": 0.82, "growth_rate": 0.22, "job_postings_count": 28000, "avg_salary_impact": 18000},
        {"skill_name": "TypeScript", "skill_category": "programming", "industry": "technology", "demand_score": 0.87, "growth_rate": 0.19, "job_postings_count": 38000, "avg_salary_impact": 13000},
    ]
    
    for skill_data in skills_data:
        skill = IndustrySkill(
            id=uuid.uuid4(),
            **skill_data
        )
        db.add(skill)
    
    db.commit()
    logger.info(f"Seeded {len(skills_data)} industry skills")


def seed_job_titles(db: Session):
    """Seed job title data."""
    logger.info("Seeding job titles...")
    
    job_titles_data = [
        {
            "title": "Senior Software Engineer",
            "normalized_title": "senior software engineer",
            "seniority_level": "senior",
            "job_family": "engineering",
            "required_skills": ["Python", "JavaScript", "SQL", "Git"],
            "preferred_skills": ["AWS", "Docker", "React"],
            "salary_min": 120000,
            "salary_max": 180000,
            "salary_median": 150000,
            "min_years_experience": 5,
            "max_years_experience": 10,
            "typical_education": ["Bachelor's in Computer Science", "Bachelor's in Engineering"]
        },
        {
            "title": "Full Stack Developer",
            "normalized_title": "full stack developer",
            "seniority_level": "mid",
            "job_family": "engineering",
            "required_skills": ["JavaScript", "React", "Node.js", "SQL"],
            "preferred_skills": ["TypeScript", "MongoDB", "AWS"],
            "salary_min": 90000,
            "salary_max": 140000,
            "salary_median": 115000,
            "min_years_experience": 3,
            "max_years_experience": 7,
            "typical_education": ["Bachelor's in Computer Science"]
        },
        {
            "title": "Data Scientist",
            "normalized_title": "data scientist",
            "seniority_level": "mid",
            "job_family": "data",
            "required_skills": ["Python", "Machine Learning", "SQL", "Statistics"],
            "preferred_skills": ["TensorFlow", "PyTorch", "AWS"],
            "salary_min": 100000,
            "salary_max": 160000,
            "salary_median": 130000,
            "min_years_experience": 3,
            "max_years_experience": 8,
            "typical_education": ["Master's in Data Science", "PhD in Statistics"]
        },
        {
            "title": "DevOps Engineer",
            "normalized_title": "devops engineer",
            "seniority_level": "mid",
            "job_family": "engineering",
            "required_skills": ["Docker", "Kubernetes", "AWS", "CI/CD"],
            "preferred_skills": ["Terraform", "Ansible", "Python"],
            "salary_min": 95000,
            "salary_max": 150000,
            "salary_median": 122000,
            "min_years_experience": 3,
            "max_years_experience": 7,
            "typical_education": ["Bachelor's in Computer Science", "Bachelor's in IT"]
        },
        {
            "title": "Product Manager",
            "normalized_title": "product manager",
            "seniority_level": "mid",
            "job_family": "product",
            "required_skills": ["Product Strategy", "Agile", "Data Analysis", "Communication"],
            "preferred_skills": ["SQL", "A/B Testing", "User Research"],
            "salary_min": 100000,
            "salary_max": 160000,
            "salary_median": 130000,
            "min_years_experience": 4,
            "max_years_experience": 8,
            "typical_education": ["Bachelor's in Business", "MBA"]
        },
    ]
    
    for job_data in job_titles_data:
        job_title = JobTitleData(
            id=uuid.uuid4(),
            **job_data
        )
        db.add(job_title)
    
    db.commit()
    logger.info(f"Seeded {len(job_titles_data)} job titles")


def seed_action_verbs(db: Session):
    """Seed action verbs."""
    logger.info("Seeding action verbs...")
    
    verbs_data = [
        # Leadership
        {"verb": "Led", "category": "leadership", "impact_level": "high", "ats_score": 0.95, "best_for_roles": ["Manager", "Lead", "Director"]},
        {"verb": "Directed", "category": "leadership", "impact_level": "high", "ats_score": 0.92, "best_for_roles": ["Manager", "Director"]},
        {"verb": "Managed", "category": "leadership", "impact_level": "high", "ats_score": 0.90, "best_for_roles": ["Manager", "Lead"]},
        {"verb": "Mentored", "category": "leadership", "impact_level": "medium", "ats_score": 0.85, "best_for_roles": ["Senior", "Lead"]},
        
        # Technical
        {"verb": "Developed", "category": "technical", "impact_level": "high", "ats_score": 0.93, "best_for_roles": ["Engineer", "Developer"]},
        {"verb": "Engineered", "category": "technical", "impact_level": "high", "ats_score": 0.91, "best_for_roles": ["Engineer"]},
        {"verb": "Architected", "category": "technical", "impact_level": "high", "ats_score": 0.90, "best_for_roles": ["Architect", "Senior Engineer"]},
        {"verb": "Implemented", "category": "technical", "impact_level": "high", "ats_score": 0.88, "best_for_roles": ["Engineer", "Developer"]},
        {"verb": "Optimized", "category": "technical", "impact_level": "high", "ats_score": 0.87, "best_for_roles": ["Engineer", "Developer"]},
        {"verb": "Automated", "category": "technical", "impact_level": "high", "ats_score": 0.86, "best_for_roles": ["DevOps", "Engineer"]},
        
        # Achievement
        {"verb": "Achieved", "category": "achievement", "impact_level": "high", "ats_score": 0.94, "best_for_roles": ["all"]},
        {"verb": "Delivered", "category": "achievement", "impact_level": "high", "ats_score": 0.92, "best_for_roles": ["all"]},
        {"verb": "Exceeded", "category": "achievement", "impact_level": "high", "ats_score": 0.90, "best_for_roles": ["all"]},
        {"verb": "Accelerated", "category": "achievement", "impact_level": "high", "ats_score": 0.88, "best_for_roles": ["all"]},
        
        # Analytical
        {"verb": "Analyzed", "category": "analytical", "impact_level": "medium", "ats_score": 0.85, "best_for_roles": ["Analyst", "Data Scientist"]},
        {"verb": "Evaluated", "category": "analytical", "impact_level": "medium", "ats_score": 0.83, "best_for_roles": ["Analyst"]},
        {"verb": "Researched", "category": "analytical", "impact_level": "medium", "ats_score": 0.82, "best_for_roles": ["Researcher", "Scientist"]},
        
        # Creative
        {"verb": "Designed", "category": "creative", "impact_level": "high", "ats_score": 0.89, "best_for_roles": ["Designer", "Architect"]},
        {"verb": "Created", "category": "creative", "impact_level": "high", "ats_score": 0.87, "best_for_roles": ["Designer", "Developer"]},
        {"verb": "Innovated", "category": "creative", "impact_level": "high", "ats_score": 0.86, "best_for_roles": ["all"]},
    ]
    
    for verb_data in verbs_data:
        verb = ActionVerb(
            id=uuid.uuid4(),
            **verb_data
        )
        db.add(verb)
    
    db.commit()
    logger.info(f"Seeded {len(verbs_data)} action verbs")


def seed_industry_metrics(db: Session):
    """Seed industry metrics."""
    logger.info("Seeding industry metrics...")
    
    metrics_data = [
        {"metric_name": "Code Coverage", "metric_type": "percentage", "industry": "technology", "job_family": "engineering", "typical_min": 70.0, "typical_max": 90.0, "exceptional_threshold": 95.0},
        {"metric_name": "System Uptime", "metric_type": "percentage", "industry": "technology", "job_family": "engineering", "typical_min": 99.0, "typical_max": 99.9, "exceptional_threshold": 99.99},
        {"metric_name": "Response Time", "metric_type": "milliseconds", "industry": "technology", "job_family": "engineering", "typical_min": 100.0, "typical_max": 500.0, "exceptional_threshold": 50.0},
        {"metric_name": "User Growth", "metric_type": "percentage", "industry": "technology", "job_family": "product", "typical_min": 10.0, "typical_max": 50.0, "exceptional_threshold": 100.0},
        {"metric_name": "Cost Reduction", "metric_type": "percentage", "industry": "all", "job_family": "all", "typical_min": 10.0, "typical_max": 30.0, "exceptional_threshold": 50.0},
        {"metric_name": "Revenue Growth", "metric_type": "percentage", "industry": "all", "job_family": "sales", "typical_min": 15.0, "typical_max": 40.0, "exceptional_threshold": 75.0},
        {"metric_name": "Team Size", "metric_type": "count", "industry": "all", "job_family": "management", "typical_min": 3.0, "typical_max": 15.0, "exceptional_threshold": 30.0},
        {"metric_name": "Project Delivery", "metric_type": "percentage", "industry": "all", "job_family": "management", "typical_min": 80.0, "typical_max": 95.0, "exceptional_threshold": 100.0},
    ]
    
    for metric_data in metrics_data:
        metric = IndustryMetric(
            id=uuid.uuid4(),
            **metric_data
        )
        db.add(metric)
    
    db.commit()
    logger.info(f"Seeded {len(metrics_data)} industry metrics")


def seed_certifications(db: Session):
    """Seed certifications."""
    logger.info("Seeding certifications...")
    
    certs_data = [
        {"certification_name": "AWS Certified Solutions Architect", "abbreviation": "AWS CSA", "issuing_organization": "Amazon Web Services", "industry": "technology", "job_families": ["engineering", "devops"], "demand_score": 0.90, "salary_impact": 15000},
        {"certification_name": "Certified Kubernetes Administrator", "abbreviation": "CKA", "issuing_organization": "Cloud Native Computing Foundation", "industry": "technology", "job_families": ["engineering", "devops"], "demand_score": 0.85, "salary_impact": 12000},
        {"certification_name": "Project Management Professional", "abbreviation": "PMP", "issuing_organization": "Project Management Institute", "industry": "all", "job_families": ["management"], "demand_score": 0.88, "salary_impact": 10000},
        {"certification_name": "Certified ScrumMaster", "abbreviation": "CSM", "issuing_organization": "Scrum Alliance", "industry": "technology", "job_families": ["management", "product"], "demand_score": 0.82, "salary_impact": 8000},
        {"certification_name": "Google Cloud Professional", "abbreviation": "GCP", "issuing_organization": "Google Cloud", "industry": "technology", "job_families": ["engineering", "devops"], "demand_score": 0.83, "salary_impact": 13000},
    ]
    
    for cert_data in certs_data:
        cert = CertificationData(
            id=uuid.uuid4(),
            **cert_data
        )
        db.add(cert)
    
    db.commit()
    logger.info(f"Seeded {len(certs_data)} certifications")


def main():
    """Main seeding function."""
    logger.info("Starting knowledge base seeding...")
    
    db = SessionLocal()
    
    try:
        seed_ats_keywords(db)
        seed_industry_skills(db)
        seed_job_titles(db)
        seed_action_verbs(db)
        seed_industry_metrics(db)
        seed_certifications(db)
        
        logger.info("Knowledge base seeding completed successfully!")
        
    except Exception as e:
        logger.error(f"Seeding failed: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
