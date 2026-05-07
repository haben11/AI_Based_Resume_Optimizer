"""
Test script for semantic caching implementation.

Tests:
1. Cache miss on first request
2. Exact match on identical request
3. Semantic match on similar request
4. Cache statistics
5. Cache cleanup

Usage:
    python -m pytest test_semantic_cache.py -v
    OR
    PYTHONPATH=. python test_semantic_cache.py
"""

import asyncio
import sys
import os

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.semantic_cache_service import create_semantic_cache_service
from app.core.logging import logger


# Test data
JOB_DESCRIPTION_1 = """
Senior Python Developer

We are seeking an experienced Python developer with 5+ years of experience.

Requirements:
- Strong Python programming skills
- Experience with Django and Flask
- Knowledge of PostgreSQL and Redis
- AWS deployment experience
- RESTful API design

Responsibilities:
- Design and implement backend services
- Write clean, maintainable code
- Collaborate with frontend team
- Optimize database queries
"""

JOB_DESCRIPTION_2 = """
Senior Python Engineer

Looking for a seasoned Python engineer with 5 years of experience.

Must have:
- Expert Python skills
- Django and Flask frameworks
- PostgreSQL and Redis databases
- AWS cloud experience
- REST API development

Duties:
- Build scalable backend systems
- Maintain code quality
- Work with UI developers
- Database performance tuning
"""

JOB_DESCRIPTION_3 = """
Junior JavaScript Developer

We need a junior JavaScript developer for our frontend team.

Requirements:
- 1-2 years JavaScript experience
- React or Vue.js knowledge
- HTML/CSS skills
- Git version control

Responsibilities:
- Build UI components
- Fix bugs
- Learn from senior developers
"""

OPTIMIZED_RESPONSE = """
# John Doe

## Professional Summary
Senior Python Developer with 5+ years of experience building scalable backend systems.
Expert in Django, Flask, and cloud deployment on AWS.

## Core Competencies
- Python, Django, Flask
- PostgreSQL, Redis
- AWS, Docker, Kubernetes
- RESTful API Design
- Microservices Architecture

## Professional Experience

### Senior Python Developer | Tech Corp | 2020-Present
- Architected and deployed 15+ microservices handling 1M+ requests/day
- Optimized database queries reducing response time by 60%
- Led team of 4 developers in agile environment
- Implemented CI/CD pipeline reducing deployment time by 80%

### Python Developer | StartupXYZ | 2018-2020
- Built RESTful APIs serving 100K+ daily active users
- Migrated monolithic application to microservices architecture
- Reduced infrastructure costs by 40% through AWS optimization
- Mentored 3 junior developers

## Education
Bachelor of Science in Computer Science | University of Technology | 2018

## Certifications
- AWS Certified Solutions Architect
- Python Professional Certification
"""


async def test_cache_miss():
    """Test 1: Cache miss on first request."""
    print("\n" + "="*80)
    print("TEST 1: Cache Miss (First Request)")
    print("="*80)
    
    engine = create_engine(settings.get_database_uri)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        cache_service = create_semantic_cache_service(db=db)
        
        # First request should be a cache miss
        result = await cache_service.get_cached_response(
            query_text=JOB_DESCRIPTION_1,
            resume_id="test-resume-123",
            job_title="Senior Python Developer",
            industry="Technology"
        )
        
        if result is None:
            print("✅ PASS: Cache miss as expected")
            return True
        else:
            print("❌ FAIL: Expected cache miss but got hit")
            return False
            
    finally:
        db.close()


async def test_cache_storage():
    """Test 2: Store response in cache."""
    print("\n" + "="*80)
    print("TEST 2: Cache Storage")
    print("="*80)
    
    engine = create_engine(settings.get_database_uri)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        cache_service = create_semantic_cache_service(db=db)
        
        # Store response
        cache_entry = await cache_service.cache_response(
            query_text=JOB_DESCRIPTION_1,
            response_text=OPTIMIZED_RESPONSE,
            response_metadata={
                "validation": {"is_valid": True, "quality_score": 0.92},
                "test": True
            },
            resume_id="test-resume-123",
            job_title="Senior Python Developer",
            industry="Technology",
            quality_score=0.92
        )
        
        if cache_entry and cache_entry.id:
            print(f"✅ PASS: Response cached successfully")
            print(f"   Cache ID: {cache_entry.id}")
            print(f"   Quality Score: {cache_entry.quality_score}")
            print(f"   TTL: {cache_entry.ttl_hours} hours")
            return True
        else:
            print("❌ FAIL: Failed to cache response")
            return False
            
    finally:
        db.close()


async def test_exact_match():
    """Test 3: Exact match on identical request."""
    print("\n" + "="*80)
    print("TEST 3: Exact Match")
    print("="*80)
    
    engine = create_engine(settings.get_database_uri)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        cache_service = create_semantic_cache_service(db=db)
        
        # Request with identical job description
        result = await cache_service.get_cached_response(
            query_text=JOB_DESCRIPTION_1,
            resume_id="test-resume-123",
            job_title="Senior Python Developer",
            industry="Technology"
        )
        
        if result and result["match_type"] == "exact":
            print("✅ PASS: Exact match found")
            print(f"   Match Type: {result['match_type']}")
            print(f"   Similarity: {result['similarity_score']:.2%}")
            print(f"   Hit Count: {result['hit_count']}")
            print(f"   Response Length: {len(result['response_text'])} chars")
            return True
        else:
            print("❌ FAIL: Expected exact match but got:", result)
            return False
            
    finally:
        db.close()


async def test_semantic_match():
    """Test 4: Semantic match on similar request."""
    print("\n" + "="*80)
    print("TEST 4: Semantic Match")
    print("="*80)
    
    engine = create_engine(settings.get_database_uri)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        cache_service = create_semantic_cache_service(db=db)
        
        # Request with similar but not identical job description
        result = await cache_service.get_cached_response(
            query_text=JOB_DESCRIPTION_2,  # Similar to JOB_DESCRIPTION_1
            resume_id="test-resume-123",
            job_title="Senior Python Developer",
            industry="Technology"
        )
        
        if result and result["match_type"] == "semantic":
            print("✅ PASS: Semantic match found")
            print(f"   Match Type: {result['match_type']}")
            print(f"   Similarity: {result['similarity_score']:.2%}")
            print(f"   Hit Count: {result['hit_count']}")
            
            if result['similarity_score'] >= 0.85:
                print(f"   ✅ Similarity above threshold (0.85)")
                return True
            else:
                print(f"   ⚠️  Similarity below threshold (0.85)")
                return False
        else:
            print("❌ FAIL: Expected semantic match but got:", result)
            return False
            
    finally:
        db.close()


async def test_no_match():
    """Test 5: No match for completely different job."""
    print("\n" + "="*80)
    print("TEST 5: No Match (Different Job)")
    print("="*80)
    
    engine = create_engine(settings.get_database_uri)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        cache_service = create_semantic_cache_service(db=db)
        
        # Request with completely different job description
        result = await cache_service.get_cached_response(
            query_text=JOB_DESCRIPTION_3,  # JavaScript job, not Python
            resume_id="test-resume-123",
            job_title="Junior JavaScript Developer",
            industry="Technology"
        )
        
        if result is None:
            print("✅ PASS: No match as expected (different job)")
            return True
        else:
            print("❌ FAIL: Unexpected match for different job")
            print(f"   Match Type: {result['match_type']}")
            print(f"   Similarity: {result['similarity_score']:.2%}")
            return False
            
    finally:
        db.close()


async def test_statistics():
    """Test 6: Cache statistics."""
    print("\n" + "="*80)
    print("TEST 6: Cache Statistics")
    print("="*80)
    
    engine = create_engine(settings.get_database_uri)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        cache_service = create_semantic_cache_service(db=db)
        
        stats = cache_service.get_statistics(days=7)
        
        print(f"✅ Statistics retrieved:")
        print(f"   Total Queries: {stats['total_queries']}")
        print(f"   Cache Hits: {stats['cache_hits']}")
        print(f"   Cache Misses: {stats['cache_misses']}")
        print(f"   Hit Rate: {stats['hit_rate']:.1f}%")
        print(f"   Exact Matches: {stats['exact_matches']}")
        print(f"   Semantic Matches: {stats['semantic_matches']}")
        print(f"   Avg Similarity: {stats['avg_similarity_score']:.2%}")
        print(f"   Cost Saved: ${stats['total_cost_saved']:.2f}")
        print(f"   Time Saved: {stats['total_time_saved_hours']:.2f} hours")
        
        return True
            
    finally:
        db.close()


async def test_cleanup():
    """Test 7: Cache cleanup."""
    print("\n" + "="*80)
    print("TEST 7: Cache Cleanup")
    print("="*80)
    
    engine = create_engine(settings.get_database_uri)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        cache_service = create_semantic_cache_service(db=db)
        
        # Cleanup expired entries
        deleted_count = cache_service.cleanup_expired_entries()
        
        print(f"✅ Cleanup complete:")
        print(f"   Deleted Entries: {deleted_count}")
        
        return True
            
    finally:
        db.close()


async def run_all_tests():
    """Run all tests."""
    print("\n" + "="*80)
    print("SEMANTIC CACHE TEST SUITE")
    print("="*80)
    
    tests = [
        ("Cache Miss", test_cache_miss),
        ("Cache Storage", test_cache_storage),
        ("Exact Match", test_exact_match),
        ("Semantic Match", test_semantic_match),
        ("No Match", test_no_match),
        ("Statistics", test_statistics),
        ("Cleanup", test_cleanup),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ ERROR in {name}: {str(e)}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
