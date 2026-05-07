"""
ESCO Knowledge Base Seeder

Seeds the Knowledge Base tables from publicly available HuggingFace datasets:
  - Skills:      TechWolf/Synthetic-ESCO-skill-sentences  (ESCO skill labels)
  - Occupations: danieldux/ESCO esco_en config            (ESCO occupations + descriptions)
  - Job Titles:  gpriday/job-titles                       (65k real-world job titles)

Run with the project venv:
    .venv/Scripts/python.exe -m app.scripts.seed_kb_esco

Author: Haben
Version: 2.0.0
"""

import os
import sys
import uuid
from sqlalchemy.orm import Session
from datasets import load_dataset
import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download

# Ensure project root is on the path when run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.db.session import SessionLocal
from app.models.knowledge_base import IndustrySkill, JobTitleData, ATSKeyword
from app.core.logging import logger

BATCH_SIZE = 500


# ---------------------------------------------------------------------------
# Skills seeding  (TechWolf/Synthetic-ESCO-skill-sentences)
# ---------------------------------------------------------------------------

def seed_skills(db: Session) -> int:
    """
    Extract unique ESCO skill labels from the TechWolf dataset and insert them
    into industry_skills + ats_keywords.
    Returns the number of new rows inserted.
    """
    logger.info("seeding_esco_skills", dataset="TechWolf/Synthetic-ESCO-skill-sentences")

    dataset = load_dataset(
        "TechWolf/Synthetic-ESCO-skill-sentences",
        split="train",
        streaming=True,
    )

    # Collect unique skill names first (the dataset has many duplicate skill labels)
    seen: set[str] = {
        s[0] for s in db.query(IndustrySkill.skill_name).all()
    }

    skills_batch: list[dict] = []
    keywords_batch: list[dict] = []
    total_inserted = 0

    for record in dataset:
        skill_name: str = (record.get("skill") or "").strip()
        if not skill_name or skill_name in seen:
            continue
        seen.add(skill_name)

        # Simple heuristic category mapping
        lower = skill_name.lower()
        if any(k in lower for k in ("communicat", "teamwork", "leadership", "negotiat",
                                     "present", "interpersonal", "collaborat")):
            category = "soft_skill"
        elif any(k in lower for k in ("language", "french", "german", "spanish",
                                       "mandarin", "arabic", "portuguese")):
            category = "language"
        else:
            category = "technical"

        skill_id = uuid.uuid4()
        skills_batch.append({
            "id": skill_id,
            "skill_name": skill_name,
            "skill_category": category,
            "industry": "General",
            "demand_score": 0.8,
            "growth_rate": 0.05,
            "job_postings_count": 0,
            "related_skills": [],
            "common_tools": [],
            "certifications": [],
        })
        keywords_batch.append({
            "id": uuid.uuid4(),
            "keyword": skill_name,
            "category": category,
            "job_family": "all",
            "importance_score": 0.9,
            "synonyms": [],
            "typical_context": None,
            "ats_variations": [skill_name, skill_name.lower()],
        })

        if len(skills_batch) >= BATCH_SIZE:
            db.bulk_insert_mappings(IndustrySkill, skills_batch)
            db.bulk_insert_mappings(ATSKeyword, keywords_batch)
            db.commit()
            total_inserted += len(skills_batch)
            logger.info("skills_batch_inserted", total=total_inserted)
            skills_batch = []
            keywords_batch = []

    # Final partial batch
    if skills_batch:
        db.bulk_insert_mappings(IndustrySkill, skills_batch)
        db.bulk_insert_mappings(ATSKeyword, keywords_batch)
        db.commit()
        total_inserted += len(skills_batch)

    logger.info("skills_seeding_complete", total_inserted=total_inserted)
    return total_inserted


# ---------------------------------------------------------------------------
# Occupations seeding  (danieldux/ESCO  esco_en config)
# ---------------------------------------------------------------------------

def seed_occupations(db: Session) -> int:
    """
    Load ESCO occupations from danieldux/ESCO via pyarrow (bypasses datasets
    schema mismatch bug) and insert into job_title_data.
    Returns the number of new rows inserted.
    """
    logger.info("seeding_esco_occupations", dataset="danieldux/ESCO (esco_en)")

    # Download the parquet file directly — avoids the datasets CastError
    parquet_path = hf_hub_download(
        repo_id="danieldux/ESCO",
        filename="data/en/train.parquet",
        repo_type="dataset",
    )
    table = pq.read_table(parquet_path)

    existing: set[str] = {
        t[0] for t in db.query(JobTitleData.title).all()
    }

    batch: list[dict] = []
    total_inserted = 0

    for i in range(len(table)):
        title: str = (table["ESCO_OCCUPATION"][i].as_py() or "").strip()
        if not title or title in existing:
            continue
        existing.add(title)

        description: str = (table["ESCO_DESCRIPTION"][i].as_py() or "").strip()
        isco_labels_raw = table["ISCO_LABELS"][i].as_py()
        isco_labels: list = isco_labels_raw if isinstance(isco_labels_raw, list) else []

        job_family = _infer_job_family(title, isco_labels)

        batch.append({
            "id": uuid.uuid4(),
            "title": title,
            "normalized_title": title.lower().replace("-", " ").strip(),
            "seniority_level": "mid",
            "job_family": job_family,
            "required_skills": [],
            "preferred_skills": [],
            "common_responsibilities": [description] if description else [],
            "salary_currency": "USD",
        })

        if len(batch) >= BATCH_SIZE:
            db.bulk_insert_mappings(JobTitleData, batch)
            db.commit()
            total_inserted += len(batch)
            logger.info("occupations_batch_inserted", total=total_inserted)
            batch = []

    if batch:
        db.bulk_insert_mappings(JobTitleData, batch)
        db.commit()
        total_inserted += len(batch)

    logger.info("occupations_seeding_complete", total_inserted=total_inserted)
    return total_inserted


# ---------------------------------------------------------------------------
# Job titles seeding  (gpriday/job-titles  — 65k titles)
# ---------------------------------------------------------------------------

def seed_job_titles(db: Session) -> int:
    """
    Load 65k real-world job titles from gpriday/job-titles and insert into
    job_title_data (skipping duplicates already inserted by seed_occupations).
    Returns the number of new rows inserted.
    """
    logger.info("seeding_job_titles", dataset="gpriday/job-titles")

    dataset = load_dataset(
        "gpriday/job-titles",
        split="train",
        streaming=True,
    )

    existing: set[str] = {
        t[0] for t in db.query(JobTitleData.title).all()
    }

    batch: list[dict] = []
    total_inserted = 0

    for record in dataset:
        title: str = (record.get("job_title") or "").strip()
        if not title or title in existing:
            continue
        existing.add(title)

        job_family = _infer_job_family(title, [])

        batch.append({
            "id": uuid.uuid4(),
            "title": title,
            "normalized_title": title.lower().replace("-", " ").strip(),
            "seniority_level": _infer_seniority(title),
            "job_family": job_family,
            "required_skills": [],
            "preferred_skills": [],
            "common_responsibilities": [],
            "salary_currency": "USD",
        })

        if len(batch) >= BATCH_SIZE:
            db.bulk_insert_mappings(JobTitleData, batch)
            db.commit()
            total_inserted += len(batch)
            logger.info("job_titles_batch_inserted", total=total_inserted)
            batch = []

    if batch:
        db.bulk_insert_mappings(JobTitleData, batch)
        db.commit()
        total_inserted += len(batch)

    logger.info("job_titles_seeding_complete", total_inserted=total_inserted)
    return total_inserted


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _infer_job_family(title: str, isco_labels: list) -> str:
    lower = title.lower()
    combined = lower + " " + " ".join(str(l).lower() for l in isco_labels)
    if any(k in combined for k in ("engineer", "developer", "software", "tech",
                                    "programmer", "devops", "data scientist",
                                    "machine learning", "architect")):
        return "engineering"
    if any(k in combined for k in ("manager", "lead", "director", "head of",
                                    "vp ", "chief", "president", "supervisor")):
        return "management"
    if any(k in combined for k in ("designer", "artist", "creative", "ux", "ui",
                                    "graphic", "illustrat")):
        return "design"
    if any(k in combined for k in ("nurse", "doctor", "physician", "therapist",
                                    "pharmacist", "surgeon", "medical")):
        return "healthcare"
    if any(k in combined for k in ("teacher", "professor", "instructor",
                                    "educator", "tutor", "lecturer")):
        return "education"
    if any(k in combined for k in ("accountant", "finance", "analyst", "auditor",
                                    "banker", "economist", "actuar")):
        return "finance"
    if any(k in combined for k in ("sales", "marketing", "brand", "advertis",
                                    "seo", "growth", "customer success")):
        return "sales_marketing"
    if any(k in combined for k in ("lawyer", "legal", "attorney", "counsel",
                                    "paralegal", "solicitor")):
        return "legal"
    return "other"


def _infer_seniority(title: str) -> str:
    lower = title.lower()
    if any(k in lower for k in ("senior", "sr.", "lead", "principal", "staff",
                                  "director", "vp", "chief", "head")):
        return "senior"
    if any(k in lower for k in ("junior", "jr.", "associate", "entry", "intern",
                                  "trainee", "graduate")):
        return "junior"
    return "mid"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    db = SessionLocal()
    try:
        print("=" * 60)
        print("ESCO Knowledge Base Seeder v2.0")
        print("=" * 60)

        print("\n[1/3] Seeding ESCO skills...")
        n_skills = seed_skills(db)
        print(f"      ✓ {n_skills} new skills inserted")

        print("\n[2/3] Seeding ESCO occupations...")
        n_occ = seed_occupations(db)
        print(f"      ✓ {n_occ} new occupations inserted")

        print("\n[3/3] Seeding job titles (65k)...")
        n_titles = seed_job_titles(db)
        print(f"      ✓ {n_titles} new job titles inserted")

        print("\n" + "=" * 60)
        print(f"Seeding complete!  Total new rows: {n_skills + n_occ + n_titles}")
        print("=" * 60)
    except Exception as e:
        logger.error("seeding_failed", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
