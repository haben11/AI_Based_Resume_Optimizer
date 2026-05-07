"""
Streaming Client Example

Demonstrates how to consume the streaming optimization endpoint.
Shows real-time progress updates and token streaming.

Author: CV Optimizer Team
Version: 1.0.0
"""

import requests
import json
import sys


def stream_optimization(
    api_url: str,
    resume_id: str,
    job_description: str,
    access_token: str
):
    """
    Stream resume optimization with real-time updates.
    
    Args:
        api_url: API base URL (e.g., http://localhost:8000)
        resume_id: Resume UUID
        job_description: Job description text
        access_token: JWT access token
    """
    
    url = f"{api_url}/api/v1/cv-optimizer/optimize/stream"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "resume_id": resume_id,
        "job_description": job_description
    }
    
    print("🚀 Starting streaming optimization...")
    print("=" * 80)
    
    try:
        # Stream response
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            stream=True  # Enable streaming
        )
        
        response.raise_for_status()
        
        # Process SSE stream
        optimized_content = ""
        current_stage = None
        
        for line in response.iter_lines():
            if not line:
                continue
            
            line = line.decode('utf-8')
            
            # Parse SSE format
            if line.startswith('event:'):
                event_type = line.split(':', 1)[1].strip()
            elif line.startswith('data:'):
                data_str = line.split(':', 1)[1].strip()
                data = json.loads(data_str)
                
                # Handle different event types
                if event_type == 'progress':
                    stage = data.get('stage', '')
                    message = data.get('message', '')
                    progress = data.get('progress', 0)
                    
                    # Print progress update
                    if stage != current_stage:
                        print(f"\n📍 {stage.upper().replace('_', ' ')}")
                        current_stage = stage
                    
                    print(f"   [{progress:3d}%] {message}")
                    
                    # Print additional data if available
                    if 'data' in data:
                        extra_data = data['data']
                        if isinstance(extra_data, dict):
                            for key, value in extra_data.items():
                                print(f"         {key}: {value}")
                
                elif event_type == 'token':
                    # Accumulate tokens
                    token = data.get('token', '')
                    optimized_content += token
                    
                    # Print token (without newline)
                    sys.stdout.write(token)
                    sys.stdout.flush()
                
                elif event_type == 'complete':
                    print("\n\n" + "=" * 80)
                    print("✅ OPTIMIZATION COMPLETE!")
                    print("=" * 80)
                    
                    result = data.get('result', {})
                    
                    # Print validation results
                    validation = result.get('validation', {})
                    print(f"\n📊 Quality Score: {validation.get('quality_score', 0):.2f}")
                    print(f"   Valid: {validation.get('is_valid', False)}")
                    print(f"   Issues: {len(validation.get('issues', []))}")
                    
                    # Print hallucination check if available
                    hallucination = result.get('hallucination_check')
                    if hallucination:
                        print(f"\n🔍 Hallucination Check:")
                        print(f"   Trustworthy: {hallucination.get('is_trustworthy', False)}")
                        print(f"   Confidence: {hallucination.get('confidence', 0):.2f}")
                        print(f"   Findings: {len(hallucination.get('findings', []))}")
                    
                    # Print optimized content
                    print(f"\n📄 Optimized Resume:")
                    print("-" * 80)
                    print(result.get('optimized_content', ''))
                    print("-" * 80)
                
                elif event_type == 'error':
                    print(f"\n❌ ERROR: {data.get('message', 'Unknown error')}")
                    print(f"   Details: {data.get('error', '')}")
        
        print("\n✨ Stream completed successfully!")
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {str(e)}")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


def main():
    """Main function for testing."""
    
    # Configuration
    API_URL = "http://localhost:8000"
    RESUME_ID = "your-resume-uuid-here"
    ACCESS_TOKEN = "your-jwt-token-here"
    
    JOB_DESCRIPTION = """
    Senior Software Engineer
    
    We are looking for an experienced Senior Software Engineer to join our team.
    
    Requirements:
    - 5+ years of experience with Python and JavaScript
    - Strong experience with AWS cloud services
    - Experience with React and Node.js
    - Excellent problem-solving and communication skills
    
    Responsibilities:
    - Lead development of scalable web applications
    - Mentor junior developers
    - Design and implement REST APIs
    """
    
    # Stream optimization
    stream_optimization(
        api_url=API_URL,
        resume_id=RESUME_ID,
        job_description=JOB_DESCRIPTION,
        access_token=ACCESS_TOKEN
    )


if __name__ == "__main__":
    main()
