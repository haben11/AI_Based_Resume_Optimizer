"""
Test script for grounding service.

Quick test to verify the grounding system is working correctly.
"""

from app.db.session import SessionLocal
from app.services.grounding_service import create_grounding_service


def test_grounding_service():
    """Test the grounding service with a sample job description."""
    
    db = SessionLocal()
    
    try:
        # Create grounding service
        grounding_service = create_grounding_service(db)
        
        # Sample job description
        job_description = """
        Senior Software Engineer
        
        We are looking for an experienced Senior Software Engineer to join our team.
        
        Requirements:
        - 5+ years of experience with Python and JavaScript
        - Strong experience with AWS cloud services
        - Experience with React and Node.js
        - Knowledge of Docker and Kubernetes
        - Excellent problem-solving and communication skills
        - Experience with Agile methodologies
        
        Responsibilities:
        - Lead development of scalable web applications
        - Mentor junior developers
        - Design and implement REST APIs
        - Optimize system performance
        - Collaborate with cross-functional teams
        """
        
        # Fetch grounding data
        print("Fetching grounding data...")
        context = grounding_service.fetch_grounding_data(
            job_description=job_description,
            job_title="Senior Software Engineer",
            industry="technology"
        )
        
        # Print summary
        print("\n" + "="*80)
        print("GROUNDING DATA SUMMARY")
        print("="*80)
        summary = context.get_summary()
        for key, value in summary.items():
            print(f"{key}: {value}")
        
        # Print formatted context (what goes into the prompt)
        print("\n" + "="*80)
        print("FORMATTED CONTEXT FOR LLM")
        print("="*80)
        print(context.to_prompt_context())
        
        print("\n" + "="*80)
        print("TEST PASSED ✓")
        print("="*80)
        
    except Exception as e:
        print(f"\nTEST FAILED ✗")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    test_grounding_service()
