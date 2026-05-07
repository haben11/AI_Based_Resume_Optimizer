import re
from typing import Dict, Any, List

def parse_optimized_cv(content: str) -> Dict[str, Any]:
    """
    Enhanced parser to extract all sections of a professional resume.
    Handles Summary, Experience, Skills, Education, Projects, and Certifications.
    """
    sections = {
        "full_name": "Applicant Name",
        "contact_info": {
            "email": "candidate@example.com",
            "phone": "+1 (555) 000-0000",
            "location": "San Francisco, CA",
            "linkedin": "linkedin.com/in/candidate"
        },
        "summary": "",
        "experience": [],
        "skills": [],
        "education": [],
        "projects": [],
        "certifications": []
    }
    
    # Extract Name from H1
    name_match = re.search(r'^# (.*)', content)
    if name_match:
        sections["full_name"] = name_match.group(1).strip()
    
    # Split content by H2 sections
    # Using lookahead to keep the header in the split parts
    raw_sections = re.split(r'\n(?=## )', content)
    
    for part in raw_sections:
        header_match = re.match(r'## (.*)', part.strip())
        if not header_match:
            continue
            
        header = header_match.group(1).lower().strip()
        body = part[header_match.end():].strip()
        
        # Use simple mapping for variations in section naming
        if any(x in header for x in ["summary", "profile", "about", "objective", "professional"]):
            sections["summary"] = body
            
        elif "experience" in header or "work history" in header:
            items = re.split(r'\n### ', f"\n{body}")
            for item in items:
                if not item.strip(): continue
                lines = item.strip().split('\n')
                title = lines[0].strip()
                bullets = [l.strip("* -").strip() for l in lines[1:] if l.strip()]
                sections["experience"].append({"title": title, "bullets": bullets})
                
        elif "skills" in header or "competencies" in header:
            # Handle both comma-separated and bulleted lists
            if "," in body and "\n" not in body:
                sections["skills"] = [s.strip() for s in body.split(",")]
            else:
                sections["skills"] = [s.strip("* -").strip() for s in body.split('\n') if s.strip()]
                
        elif "projects" in header:
            items = re.split(r'\n### ', f"\n{body}")
            for item in items:
                if not item.strip(): continue
                lines = item.strip().split('\n')
                title = lines[0].strip()
                bullets = [l.strip("* -").strip() for l in lines[1:] if l.strip()]
                sections["projects"].append({"title": title, "bullets": bullets})
                
        elif "education" in header:
            sections["education"] = [s.strip("* -").strip() for s in body.split('\n') if s.strip()]
            
        elif "certification" in header:
            sections["certifications"] = [s.strip("* -").strip() for s in body.split('\n') if s.strip()]

    return sections
