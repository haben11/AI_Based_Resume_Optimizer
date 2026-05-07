"""
Markdown to Plain Text Converter

Converts Markdown-formatted resumes to clean, readable plain text.

Author: CV Optimizer Team
Version: 1.0.0
"""

import re
from typing import Optional


class MarkdownConverter:
    """Convert Markdown to clean plain text."""
    
    @staticmethod
    def to_plain_text(markdown_text: str) -> str:
        """
        Convert Markdown resume to plain text.
        
        Args:
            markdown_text: Resume in Markdown format
            
        Returns:
            Clean plain text version
        """
        text = markdown_text
        
        # Remove bold/italic markers
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic*
        text = re.sub(r'__([^_]+)__', r'\1', text)      # __bold__
        text = re.sub(r'_([^_]+)_', r'\1', text)        # _italic_
        
        # Convert headers to plain text with proper spacing
        text = re.sub(r'^#{1,6}\s+(.+)$', r'\1', text, flags=re.MULTILINE)
        
        # Convert bullet points to simple dashes or remove
        text = re.sub(r'^\s*[\*\-\+]\s+', '• ', text, flags=re.MULTILINE)
        
        # Remove extra pipes (from tables)
        text = re.sub(r'\s*\|\s*', ' | ', text)
        
        # Clean up multiple spaces
        text = re.sub(r' {2,}', ' ', text)
        
        # Clean up multiple newlines (keep max 2)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    @staticmethod
    def to_html(markdown_text: str) -> str:
        """
        Convert Markdown resume to HTML.
        
        Args:
            markdown_text: Resume in Markdown format
            
        Returns:
            HTML version
        """
        try:
            import markdown
            return markdown.markdown(markdown_text)
        except ImportError:
            # Fallback: basic HTML conversion
            text = markdown_text
            
            # Headers
            text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
            text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
            text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
            
            # Bold
            text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
            
            # Italic
            text = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', text)
            
            # Bullet points
            text = re.sub(r'^\* (.+)$', r'<li>\1</li>', text, flags=re.MULTILINE)
            text = re.sub(r'(<li>.*</li>)', r'<ul>\1</ul>', text, flags=re.DOTALL)
            
            # Paragraphs
            text = re.sub(r'\n\n', '</p><p>', text)
            text = f'<p>{text}</p>'
            
            return text
    
    @staticmethod
    def clean_for_display(markdown_text: str, format: str = "plain") -> str:
        """
        Clean Markdown for user display.
        
        Args:
            markdown_text: Resume in Markdown format
            format: Output format ("plain" or "html")
            
        Returns:
            Cleaned text in requested format
        """
        if format == "html":
            return MarkdownConverter.to_html(markdown_text)
        else:
            return MarkdownConverter.to_plain_text(markdown_text)


# Singleton instance
markdown_converter = MarkdownConverter()
