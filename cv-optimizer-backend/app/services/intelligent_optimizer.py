"""
Intelligent Optimizer Service

Granular AI optimization for resume sections, bullets, and sentences.
Provides real-time suggestions and context-aware improvements.

Author: CV Optimizer Team
Version: 1.0.0
"""

from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from app.core.config import settings
from app.core.logging import logger
from app.crud.crud_structured_resume import structured_resume_repo
from app.schemas.structured_resume import (
    OptimizationLevel,
    OptimizationSuggestion,
    SuggestionType
)
import re
import json


class IntelligentOptimizer:
    """
    Intelligent optimizer for granular resume improvements.
    
    Capabilities:
    - Optimize entire resume, sections, bullets, or selected text
    - Generate real-time suggestions
    - Context-aware improvements based on job description
    - Quality scoring and validation
    """
    
    def __init__(self):
        """Initialize intelligent optimizer."""
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.3,
            convert_system_message_to_human=True
        )
    
    async def optimize_full_resume(
        self,
        db: Session,
        resume_id: UUID,
        job_description: Optional[str] = None,
        user_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Optimize entire resume.
        
        Args:
            db: Database session
            resume_id: Resume identifier
            job_description: Target job description
            user_instructions: Custom user instructions
            
        Returns:
            Optimization result with suggestions
        """
        logger.info("optimizing_full_resume", resume_id=resume_id)
        
        # Get resume
        resume = structured_resume_repo.get(db, resume_id)
        if not resume:
            raise ValueError("Resume not found")
        
        # Build full resume content
        full_content = self._build_resume_text(resume)
        
        # Create optimization request
        opt_request = structured_resume_repo.create_optimization_request(
            db=db,
            resume_id=resume_id,
            level=OptimizationLevel.FULL_RESUME.value,
            original_content=full_content,
            job_description=job_description,
            user_instructions=user_instructions
        )
        
        # Generate optimized version
        prompt = self._build_full_resume_prompt(job_description, user_instructions)
        
        chain = prompt | self.llm
        response = await chain.ainvoke({
            "resume_content": full_content,
            "job_description": job_description or "General optimization",
            "user_instructions": user_instructions or "No specific instructions"
        })
        
        optimized_content = response.content
        
        # Generate suggestions
        suggestions = await self._generate_resume_suggestions(
            full_content,
            optimized_content,
            job_description
        )
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(optimized_content)
        
        # Update request
        structured_resume_repo.update_optimization_request(
            db=db,
            request_id=opt_request.id,
            optimized_content=optimized_content,
            suggestions=[s.dict() for s in suggestions],
            status="completed",
            quality_score=quality_score
        )
        
        logger.info(
            "full_resume_optimized",
            resume_id=resume_id,
            quality_score=quality_score,
            num_suggestions=len(suggestions)
        )
        
        return {
            "optimization_id": str(opt_request.id),
            "optimized_content": optimized_content,
            "suggestions": suggestions,
            "quality_score": quality_score
        }
    
    async def optimize_section(
        self,
        db: Session,
        section_id: UUID,
        job_description: Optional[str] = None,
        user_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Optimize specific section.
        
        Args:
            db: Database session
            section_id: Section identifier
            job_description: Target job description
            user_instructions: Custom user instructions
            
        Returns:
            Optimization result with suggestions
        """
        logger.info("optimizing_section", section_id=section_id)
        
        # Get section
        section = structured_resume_repo.get_section(db, section_id)
        if not section:
            raise ValueError("Section not found")
        
        # Build section content
        section_content = self._build_section_text(section)
        
        # Create optimization request
        opt_request = structured_resume_repo.create_optimization_request(
            db=db,
            resume_id=section.resume_id,
            level=OptimizationLevel.SECTION.value,
            target_id=section_id,
            original_content=section_content,
            job_description=job_description,
            user_instructions=user_instructions
        )
        
        # Generate optimized version
        prompt = self._build_section_prompt(
            section.section_type.value,
            job_description,
            user_instructions
        )
        
        chain = prompt | self.llm
        response = await chain.ainvoke({
            "section_type": section.section_type.value,
            "section_content": section_content,
            "job_description": job_description or "General optimization",
            "user_instructions": user_instructions or "No specific instructions"
        })
        
        optimized_content = response.content
        
        # Generate suggestions
        suggestions = await self._generate_section_suggestions(
            section,
            optimized_content,
            job_description
        )
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(optimized_content)
        
        # Update request
        structured_resume_repo.update_optimization_request(
            db=db,
            request_id=opt_request.id,
            optimized_content=optimized_content,
            suggestions=[s.dict() for s in suggestions],
            status="completed",
            quality_score=quality_score
        )
        
        logger.info(
            "section_optimized",
            section_id=section_id,
            quality_score=quality_score,
            num_suggestions=len(suggestions)
        )
        
        return {
            "optimization_id": str(opt_request.id),
            "optimized_content": optimized_content,
            "suggestions": suggestions,
            "quality_score": quality_score
        }
    
    async def optimize_bullet(
        self,
        db: Session,
        bullet_id: UUID,
        job_description: Optional[str] = None,
        user_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Optimize specific bullet point.
        
        Args:
            db: Database session
            bullet_id: Bullet identifier
            job_description: Target job description
            user_instructions: Custom user instructions
            
        Returns:
            Optimization result with suggestions
        """
        logger.info("optimizing_bullet", bullet_id=bullet_id)
        
        # Get bullet
        bullet = structured_resume_repo.get_bullet(db, bullet_id)
        if not bullet:
            raise ValueError("Bullet not found")
        
        # Get section for context
        section = structured_resume_repo.get_section(db, bullet.section_id)
        
        # Create optimization request
        opt_request = structured_resume_repo.create_optimization_request(
            db=db,
            resume_id=section.resume_id,
            level=OptimizationLevel.BULLET.value,
            target_id=bullet_id,
            original_content=bullet.content,
            job_description=job_description,
            user_instructions=user_instructions
        )
        
        # Generate optimized version
        prompt = self._build_bullet_prompt(job_description, user_instructions)
        
        chain = prompt | self.llm
        response = await chain.ainvoke({
            "bullet_content": bullet.content,
            "section_context": f"{section.title} - {section.subtitle or ''}",
            "job_description": job_description or "General optimization",
            "user_instructions": user_instructions or "No specific instructions"
        })
        
        optimized_content = response.content.strip()
        
        # Generate suggestions
        suggestions = await self._generate_bullet_suggestions(
            bullet.content,
            optimized_content,
            job_description
        )
        
        # Calculate quality score
        quality_score = self._calculate_bullet_quality(optimized_content)
        
        # Update request
        structured_resume_repo.update_optimization_request(
            db=db,
            request_id=opt_request.id,
            optimized_content=optimized_content,
            suggestions=[s.dict() for s in suggestions],
            status="completed",
            quality_score=quality_score
        )
        
        logger.info(
            "bullet_optimized",
            bullet_id=bullet_id,
            quality_score=quality_score,
            num_suggestions=len(suggestions)
        )
        
        return {
            "optimization_id": str(opt_request.id),
            "optimized_content": optimized_content,
            "suggestions": suggestions,
            "quality_score": quality_score
        }
    
    async def optimize_selection(
        self,
        db: Session,
        resume_id: UUID,
        selected_text: str,
        context: str,
        job_description: Optional[str] = None,
        user_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Optimize selected text (sentence or paragraph).
        
        Args:
            db: Database session
            resume_id: Resume identifier
            selected_text: Selected text to optimize
            context: Surrounding context
            job_description: Target job description
            user_instructions: Custom user instructions
            
        Returns:
            Optimization result with suggestions
        """
        logger.info("optimizing_selection", resume_id=resume_id, text_length=len(selected_text))
        
        # Create optimization request
        opt_request = structured_resume_repo.create_optimization_request(
            db=db,
            resume_id=resume_id,
            level=OptimizationLevel.SELECTION.value,
            original_content=selected_text,
            job_description=job_description,
            user_instructions=user_instructions
        )
        
        # Generate optimized version
        prompt = self._build_selection_prompt(job_description, user_instructions)
        
        chain = prompt | self.llm
        response = await chain.ainvoke({
            "selected_text": selected_text,
            "context": context,
            "job_description": job_description or "General optimization",
            "user_instructions": user_instructions or "No specific instructions"
        })
        
        optimized_content = response.content.strip()
        
        # Generate suggestions
        suggestions = await self._generate_selection_suggestions(
            selected_text,
            optimized_content
        )
        
        # Update request
        structured_resume_repo.update_optimization_request(
            db=db,
            request_id=opt_request.id,
            optimized_content=optimized_content,
            suggestions=[s.dict() for s in suggestions],
            status="completed"
        )
        
        logger.info("selection_optimized", resume_id=resume_id)
        
        return {
            "optimization_id": str(opt_request.id),
            "optimized_content": optimized_content,
            "suggestions": suggestions
        }
    
    # ========================================================================
    # Helper Methods
    # ========================================================================
    
    def _build_resume_text(self, resume) -> str:
        """Build full resume text from structured data."""
        parts = []
        
        for section in sorted(resume.sections, key=lambda s: s.order_index):
            if not section.is_visible:
                continue
            
            parts.append(f"\n## {section.title}")
            
            if section.subtitle:
                parts.append(f"**{section.subtitle}**")
            
            if section.date_range:
                parts.append(f"*{section.date_range}*")
            
            if section.location:
                parts.append(f"*{section.location}*")
            
            if section.description:
                parts.append(f"\n{section.description}")
            
            if section.bullets:
                parts.append("")
                for bullet in sorted(section.bullets, key=lambda b: b.order_index):
                    if bullet.is_visible:
                        parts.append(f"- {bullet.content}")
        
        return "\n".join(parts)
    
    def _build_section_text(self, section) -> str:
        """Build section text from structured data."""
        parts = [f"## {section.title}"]
        
        if section.subtitle:
            parts.append(f"**{section.subtitle}**")
        
        if section.date_range:
            parts.append(f"*{section.date_range}*")
        
        if section.location:
            parts.append(f"*{section.location}*")
        
        if section.description:
            parts.append(f"\n{section.description}")
        
        if section.bullets:
            parts.append("")
            for bullet in sorted(section.bullets, key=lambda b: b.order_index):
                if bullet.is_visible:
                    parts.append(f"- {bullet.content}")
        
        return "\n".join(parts)
    
    def _build_full_resume_prompt(
        self,
        job_description: Optional[str],
        user_instructions: Optional[str]
    ) -> ChatPromptTemplate:
        """Build prompt for full resume optimization."""
        return ChatPromptTemplate.from_messages([
            ("system", """You are an expert resume optimization AI. Your task is to improve the entire resume while maintaining factual accuracy.

CRITICAL RULES:
1. **Preserve all factual information** - Do not invent companies, dates, or achievements
2. **Maintain structure** - Keep the same sections and organization
3. **Enhance clarity and impact** - Improve wording, add action verbs, quantify achievements
4. **Tailor to job description** - Emphasize relevant skills and experiences
5. **Follow user instructions** - Respect any specific requests

Job Description:
{job_description}

User Instructions:
{user_instructions}

Return the optimized resume in the same format as the input."""),
            ("human", "{resume_content}")
        ])
    
    def _build_section_prompt(
        self,
        section_type: str,
        job_description: Optional[str],
        user_instructions: Optional[str]
    ) -> ChatPromptTemplate:
        """Build prompt for section optimization."""
        return ChatPromptTemplate.from_messages([
            ("system", f"""You are an expert resume optimization AI. Optimize this {section_type} section.

CRITICAL RULES:
1. **Preserve factual accuracy** - Do not invent information
2. **Enhance impact** - Use strong action verbs, quantify achievements
3. **Maintain format** - Keep the same structure
4. **Tailor to job** - Emphasize relevant aspects

Job Description:
{{job_description}}

User Instructions:
{{user_instructions}}

Return only the optimized section content."""),
            ("human", "Section Type: {section_type}\n\n{section_content}")
        ])
    
    def _build_bullet_prompt(
        self,
        job_description: Optional[str],
        user_instructions: Optional[str]
    ) -> ChatPromptTemplate:
        """Build prompt for bullet optimization."""
        return ChatPromptTemplate.from_messages([
            ("system", """You are an expert resume optimization AI. Optimize this bullet point using the X-Y-Z formula: Accomplished [X] as measured by [Y], by doing [Z].

CRITICAL RULES:
1. **Preserve facts** - Do not invent metrics or achievements
2. **Start with action verb** - Use strong, specific verbs
3. **Quantify impact** - Add or emphasize metrics where possible
4. **Be concise** - Keep under 150 characters if possible
5. **Tailor to job** - Emphasize relevant skills

Context: {section_context}

Job Description:
{job_description}

User Instructions:
{user_instructions}

Return only the optimized bullet point (no bullet symbol)."""),
            ("human", "{bullet_content}")
        ])
    
    def _build_selection_prompt(
        self,
        job_description: Optional[str],
        user_instructions: Optional[str]
    ) -> ChatPromptTemplate:
        """Build prompt for selection optimization."""
        return ChatPromptTemplate.from_messages([
            ("system", """You are an expert resume optimization AI. Improve the selected text while maintaining context.

CRITICAL RULES:
1. **Preserve meaning** - Keep the core message intact
2. **Enhance clarity** - Improve wording and flow
3. **Maintain tone** - Professional and confident
4. **Respect context** - Ensure it fits with surrounding text

Context: {context}

Job Description:
{job_description}

User Instructions:
{user_instructions}

Return only the improved text."""),
            ("human", "{selected_text}")
        ])
    
    async def _generate_resume_suggestions(
        self,
        original: str,
        optimized: str,
        job_description: Optional[str]
    ) -> List[OptimizationSuggestion]:
        """Generate suggestions for full resume."""
        suggestions = []
        
        # Check for missing metrics
        if len(re.findall(r'\d+%|\$\d+|\d+\+', optimized)) < 3:
            suggestions.append(OptimizationSuggestion(
                type=SuggestionType.ADD_METRIC,
                title="Add More Metrics",
                description="Include quantifiable achievements (percentages, dollar amounts, numbers)",
                priority=80
            ))
        
        # Check for action verbs
        action_verbs = ['achieved', 'developed', 'led', 'implemented', 'designed']
        if not any(verb in optimized.lower() for verb in action_verbs):
            suggestions.append(OptimizationSuggestion(
                type=SuggestionType.ADD_ACTION_VERB,
                title="Use Strong Action Verbs",
                description="Start bullet points with powerful action verbs",
                priority=70
            ))
        
        return suggestions
    
    async def _generate_section_suggestions(
        self,
        section,
        optimized: str,
        job_description: Optional[str]
    ) -> List[OptimizationSuggestion]:
        """Generate suggestions for section."""
        suggestions = []
        
        # Section-specific suggestions
        if section.section_type.value == "experience":
            if len(section.bullets) < 3:
                suggestions.append(OptimizationSuggestion(
                    type=SuggestionType.EXPAND,
                    title="Add More Bullet Points",
                    description="Include 3-5 bullet points per role for better impact",
                    priority=60
                ))
        
        return suggestions
    
    async def _generate_bullet_suggestions(
        self,
        original: str,
        optimized: str,
        job_description: Optional[str]
    ) -> List[OptimizationSuggestion]:
        """Generate suggestions for bullet."""
        suggestions = []
        
        # Check for metrics
        if not re.search(r'\d+%|\$\d+|\d+\+', optimized):
            suggestions.append(OptimizationSuggestion(
                type=SuggestionType.ADD_METRIC,
                title="Add Quantifiable Metric",
                description="Include a number, percentage, or dollar amount to show impact",
                priority=90
            ))
        
        # Check length
        if len(optimized) > 150:
            suggestions.append(OptimizationSuggestion(
                type=SuggestionType.CONDENSE,
                title="Shorten Bullet Point",
                description="Keep bullet points concise (under 150 characters)",
                priority=50
            ))
        
        return suggestions
    
    async def _generate_selection_suggestions(
        self,
        original: str,
        optimized: str
    ) -> List[OptimizationSuggestion]:
        """Generate suggestions for selection."""
        return []
    
    def _calculate_quality_score(self, content: str) -> int:
        """Calculate quality score (0-100)."""
        score = 50  # Base score
        
        # Check for metrics
        metrics_count = len(re.findall(r'\d+%|\$\d+|\d+\+', content))
        score += min(metrics_count * 5, 20)
        
        # Check for action verbs
        action_verbs = ['achieved', 'developed', 'led', 'implemented', 'designed', 'created']
        verb_count = sum(1 for verb in action_verbs if verb in content.lower())
        score += min(verb_count * 3, 15)
        
        # Check length (not too short, not too long)
        if 200 <= len(content) <= 1000:
            score += 15
        
        return min(score, 100)
    
    def _calculate_bullet_quality(self, content: str) -> int:
        """Calculate bullet quality score (0-100)."""
        score = 50
        
        # Has metric
        if re.search(r'\d+%|\$\d+|\d+\+', content):
            score += 25
        
        # Starts with action verb
        action_verbs = ['achieved', 'developed', 'led', 'implemented', 'designed', 'created']
        if any(content.lower().startswith(verb) for verb in action_verbs):
            score += 15
        
        # Good length
        if 50 <= len(content) <= 150:
            score += 10
        
        return min(score, 100)


# Singleton instance
intelligent_optimizer = IntelligentOptimizer()
