"""
Unit tests for Output Validator

Tests validation functionality including:
- Section presence validation
- Content quality checks
- Metrics detection
- Action verb usage
- Hallucination detection
"""

import pytest
from app.utils.output_validator import OutputValidator, ValidationSeverity


class TestOutputValidator:
    """Test suite for OutputValidator class."""
    
    @pytest.fixture
    def validator(self):
        """Create an OutputValidator instance for testing."""
        return OutputValidator()
    
    @pytest.fixture
    def valid_resume(self):
        """Sample valid optimized resume."""
        return """# Jane Smith

## Professional Summary
Results-driven software engineer with 8+ years of experience in developing scalable web applications.
Proven track record of improving system performance by 50% and leading cross-functional teams.

## Core Competencies
- Python, JavaScript, React, Node.js
- AWS, Docker, Kubernetes
- Agile, Scrum, CI/CD
- Team Leadership, Mentoring

## Professional Experience

### Senior Software Engineer | TechCorp Inc | 2020-Present
- Developed microservices architecture serving 2M+ daily active users
- Improved API response time by 60% through caching optimization
- Led team of 6 engineers in delivering 15+ features quarterly
- Reduced deployment time from 2 hours to 15 minutes using CI/CD

### Software Engineer | StartupCo LLC | 2018-2020
- Built RESTful APIs handling 10K requests/second
- Increased test coverage from 40% to 95%
- Collaborated with product team to deliver 20+ user stories per sprint

## Education
B.S. Computer Science | Tech University | 2018
GPA: 3.8/4.0, Dean's List

## Certifications
- AWS Certified Solutions Architect | Amazon | 2022
- Certified Scrum Master | Scrum Alliance | 2021
"""
    
    @pytest.fixture
    def invalid_resume(self):
        """Sample invalid resume missing sections."""
        return """# John Doe

Some random text without proper structure.
No sections defined.
"""
    
    def test_valid_resume_passes(self, validator, valid_resume):
        """Test that a valid resume passes validation."""
        result = validator.validate(valid_resume)
        
        assert result.is_valid
        assert result.score > 80
        assert len(result.get_errors()) == 0
    
    def test_missing_required_sections(self, validator, invalid_resume):
        """Test detection of missing required sections."""
        result = validator.validate(invalid_resume)
        
        assert not result.is_valid
        assert len(result.sections_missing) > 0
        assert len(result.get_errors()) > 0
        
        # Should flag missing sections
        error_messages = [e.message for e in result.get_errors()]
        assert any('Missing required section' in msg for msg in error_messages)
    
    def test_section_detection(self, validator, valid_resume):
        """Test that sections are correctly detected."""
        result = validator.validate(valid_resume)
        
        assert 'summary' in result.sections_found
        assert 'experience' in result.sections_found
        assert 'skills' in result.sections_found
        assert 'education' in result.sections_found
    
    def test_metrics_detection(self, validator, valid_resume):
        """Test that metrics are detected in content."""
        result = validator.validate(valid_resume)
        
        assert result.has_metrics
        # Should not have warnings about missing metrics
        warning_messages = [w.message for w in result.get_warnings()]
        assert not any('No quantifiable metrics' in msg for msg in warning_messages)
    
    def test_no_metrics_warning(self, validator):
        """Test warning when no metrics are present."""
        resume_without_metrics = """# John Doe

## Professional Summary
Software engineer with experience in development.

## Professional Experience
### Engineer | Company | 2020-2023
- Worked on various projects
- Collaborated with team members
- Developed features

## Skills
Python, JavaScript

## Education
B.S. Computer Science | University | 2020
"""
        
        result = validator.validate(resume_without_metrics)
        
        assert not result.has_metrics
        warning_messages = [w.message for w in result.get_warnings()]
        assert any('No quantifiable metrics' in msg for msg in warning_messages)
    
    def test_action_verbs_detection(self, validator, valid_resume):
        """Test that action verbs are detected."""
        result = validator.validate(valid_resume)
        
        assert result.has_action_verbs
    
    def test_no_action_verbs_warning(self, validator):
        """Test warning when no action verbs are present."""
        resume_without_verbs = """# John Doe

## Professional Summary
A person who works in technology.

## Professional Experience
### Role | Company | 2020-2023
- Was responsible for tasks
- Had duties including various things

## Skills
Python

## Education
Degree | School | 2020
"""
        
        result = validator.validate(resume_without_verbs)
        
        warning_messages = [w.message for w in result.get_warnings()]
        assert any('action verb' in msg.lower() for msg in warning_messages)
    
    def test_length_validation_too_short(self, validator):
        """Test validation of resume that's too short."""
        short_resume = """# John Doe

## Summary
Engineer.

## Experience
Worked.

## Skills
Python

## Education
Degree
"""
        
        result = validator.validate(short_resume)
        
        error_messages = [e.message for e in result.get_errors()]
        assert any('too short' in msg.lower() for msg in error_messages)
    
    def test_length_validation_too_long(self, validator):
        """Test validation of resume that's too long."""
        # Create artificially long resume
        long_content = "This is a very long sentence. " * 300
        long_resume = f"""# John Doe

## Professional Summary
{long_content}

## Professional Experience
{long_content}

## Skills
{long_content}

## Education
{long_content}
"""
        
        result = validator.validate(long_resume)
        
        warning_messages = [w.message for w in result.get_warnings()]
        assert any('very long' in msg.lower() or 'long' in msg.lower() for msg in warning_messages)
    
    def test_formatting_validation(self, validator):
        """Test validation of markdown formatting."""
        poorly_formatted = """John Doe

Professional Summary
Some text here

Experience
More text

Skills
Python

Education
Degree
"""
        
        result = validator.validate(poorly_formatted)
        
        # Should have formatting issues
        issues = result.get_errors() + result.get_warnings()
        issue_messages = [i.message for i in issues]
        assert any('header' in msg.lower() or 'formatting' in msg.lower() for msg in issue_messages)
    
    def test_hallucination_detection(self, validator):
        """Test basic hallucination detection."""
        original = """# John Doe
Worked at Google Inc from 2020-2023"""
        
        optimized = """# John Doe
Worked at Microsoft Corp from 2019-2024"""
        
        result = validator.validate(optimized, original)
        
        # Should detect invented company and dates
        error_messages = [e.message for e in result.get_errors()]
        warning_messages = [w.message for w in result.get_warnings()]
        all_messages = error_messages + warning_messages
        
        assert any('hallucinated' in msg.lower() or 'not in original' in msg.lower() 
                  for msg in all_messages)
    
    def test_word_count_tracking(self, validator, valid_resume):
        """Test that word count is tracked."""
        result = validator.validate(valid_resume)
        
        assert result.word_count > 0
        # Rough check that word count is reasonable
        assert result.word_count == len(valid_resume.split())
    
    def test_quality_score_calculation(self, validator, valid_resume, invalid_resume):
        """Test that quality score is calculated correctly."""
        valid_result = validator.validate(valid_resume)
        invalid_result = validator.validate(invalid_resume)
        
        # Valid resume should have higher score
        assert valid_result.score > invalid_result.score
        
        # Scores should be in valid range
        assert 0 <= valid_result.score <= 100
        assert 0 <= invalid_result.score <= 100
    
    def test_severity_levels(self, validator, invalid_resume):
        """Test that issues have appropriate severity levels."""
        result = validator.validate(invalid_resume)
        
        # Should have issues of different severities
        assert len(result.issues) > 0
        
        # Check that severity is properly set
        for issue in result.issues:
            assert issue.severity in [
                ValidationSeverity.ERROR,
                ValidationSeverity.WARNING,
                ValidationSeverity.INFO
            ]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
