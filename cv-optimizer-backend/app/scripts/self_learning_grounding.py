"""
Self-Learning Grounding Service

This script runs as a background task (e.g., weekly) to analyze anonymized 
job descriptions from the OptimizationHistory table. 

It updates the demand scores and frequency of skills in the Knowledge Base, 
ensuring the RAG pipeline is always grounded in current market trends.

Author: Haben
Version: 1.0.0
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Set
from sqlalchemy.orm import Session
from sqlalchemy import func

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.resume import OptimizationHistory
from app.models.knowledge_base import IndustrySkill, ATSKeyword
from app.services.dynamic_grounding_service import SkillExtractor
from app.core.logging import logger

def analyze_market_trends(db: Session, days: int = 7):
    """
    Analyzes job descriptions from the past N days to update skill demand scores.
    """
    logger.info("starting_market_trend_analysis", days_back=days)
    
    # 1. Fetch JDs from the period
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    jds = db.query(OptimizationHistory.job_description).filter(
        OptimizationHistory.created_at >= cutoff_date
    ).all()
    
    total_jds = len(jds)
    if total_jds == 0:
        logger.info("no_new_data_for_analysis")
        return

    logger.info("analyzing_jds", count=total_jds)

    # 2. Extract and count skills
    extractor = SkillExtractor()
    skill_counts: Dict[str, int] = {}
    
    for (jd_text,) in jds:
        # Extract skills (using known list + potentially regex for new keywords)
        skills = extractor.extract_skills(jd_text)
        for skill in skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1

    # 3. Update Knowledge Base
    # We update both IndustrySkill and ATSKeyword importance scores
    for skill_name, count in skill_counts.items():
        # Calculate demand score (relative frequency)
        # We use a moving average approach: 0.7 * old_score + 0.3 * current_period_score
        current_period_demand = count / total_jds
        
        # Normalize: if a skill appears in 20% of JDs, it's highly in demand (0.8+)
        # Formula: min(1.0, current_period_demand * 5) 
        normalized_demand = min(1.0, current_period_demand * 5)

        # Update IndustrySkill
        skill_entry = db.query(IndustrySkill).filter(
            func.lower(IndustrySkill.skill_name) == skill_name.lower()
        ).first()
        
        if skill_entry:
            # Moving average for stability
            skill_entry.demand_score = (skill_entry.demand_score * 0.7) + (normalized_demand * 0.3)
            skill_entry.job_postings_count += count
            logger.info("updated_skill_demand", skill=skill_name, new_score=skill_entry.demand_score)
        
        # Update ATSKeyword importance
        keyword_entry = db.query(ATSKeyword).filter(
            func.lower(ATSKeyword.keyword) == skill_name.lower()
        ).first()
        
        if keyword_entry:
            keyword_entry.importance_score = (keyword_entry.importance_score * 0.8) + (normalized_demand * 0.2)
            keyword_entry.frequency_score = (keyword_entry.frequency_score * 0.8) + (current_period_demand * 0.2)

    db.commit()
    logger.info("market_trend_analysis_complete")

def main():
    db = SessionLocal()
    try:
        analyze_market_trends(db)
    except Exception as e:
        logger.error("market_analysis_failed", error=str(e))
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
