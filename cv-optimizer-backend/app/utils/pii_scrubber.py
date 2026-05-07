"""
PII Scrubber for GDPR/SOC2 Compliance

This module provides robust scrubbing of Personally Identifiable Information (PII)
from resume text before it is sent to external LLM providers.
It uses high-precision regex patterns and contextual markers to identify and
mask sensitive data while preserving the semantic structure of the document.

Author: Antigravity AI
Version: 1.0.0
"""

import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass


@dataclass
class ScrubberResult:
    """Result of a scrubbing operation."""
    scrubbed_text: str
    placeholders: Dict[str, str]  # Mapping of placeholder -> original value
    metadata: Dict[str, Any]      # Statistical metadata about scrubbing


class PIIScrubber:
    """
    Production-ready PII Scrubber using high-precision regex and context-aware patterns.
    
    Designed to mask:
    - Email addresses
    - Phone numbers (International and domestic)
    - Physical addresses
    - Social media profiles (LinkedIn, GitHub, etc.)
    - Specific user identifiers (Names, if provided)
    """

    # Email pattern (RFC 5322 compliant-ish for performance)
    EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    # Phone patterns (Multiple formats)
    PHONE_PATTERNS = [
        r'\+?\d{1,4}[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',  # International/Generic
        r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',                                     # US Standard
    ]
    
    # URL patterns (LinkedIn, GitHub, Personal sites)
    URL_PATTERN = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)'
    
    # Physical address markers and patterns
    # This is a heuristic approach as addresses vary wildly
    ADDRESS_MARKERS = [
        r'\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Circle|Cir|Way|Place|Pl)',
        r'(?:P\.O\.\s+Box|PO\s+Box)\s+\d+',
        r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s+[A-Z]{2}\s+\d{5}(?:-\d{4})?' # City, ST 12345
    ]

    def __init__(self):
        """Initialize the scrubber."""
        self._email_re = re.compile(self.EMAIL_PATTERN)
        self._phone_res = [re.compile(p) for p in self.PHONE_PATTERNS]
        self._url_re = re.compile(self.URL_PATTERN)
        self._address_res = [re.compile(p, re.IGNORECASE) for p in self.ADDRESS_MARKERS]

    def scrub(self, text: str, user_info: Optional[Dict[str, str]] = None) -> ScrubberResult:
        """
        Scrub PII from text and replace with placeholders.
        
        Args:
            text: Raw text to scrub
            user_info: Optional dict containing 'full_name', 'email', etc. to specifically target
            
        Returns:
            ScrubberResult containing scrubbed text and placeholder mapping
        """
        placeholders = {}
        scrubbed_text = text
        stats = {"emails": 0, "phones": 0, "urls": 0, "addresses": 0, "custom": 0}

        # 1. Scrub User Specific Info (High Precision)
        if user_info:
            if "full_name" in user_info and len(user_info["full_name"]) > 3:
                name = user_info["full_name"]
                placeholder = "[FULL_NAME]"
                if name in scrubbed_text:
                    placeholders[placeholder] = name
                    # Use re.escape to handle names with special characters
                    scrubbed_text = re.sub(re.escape(name), placeholder, scrubbed_text)
                    stats["custom"] += 1

            if "email" in user_info:
                email = user_info["email"]
                placeholder = "[EMAIL_PRIMARY]"
                if email in scrubbed_text:
                    placeholders[placeholder] = email
                    scrubbed_text = re.sub(re.escape(email), placeholder, scrubbed_text)
                    stats["custom"] += 1

        # 2. Scrub Emails (Pattern based)
        emails = self._email_re.findall(scrubbed_text)
        for i, email in enumerate(emails):
            placeholder = f"[EMAIL_{i+1}]"
            if placeholder not in placeholders: # Avoid double masking
                placeholders[placeholder] = email
                scrubbed_text = scrubbed_text.replace(email, placeholder)
                stats["emails"] += 1

        # 3. Scrub URLs
        urls = self._url_re.findall(scrubbed_text)
        for i, url in enumerate(urls):
            # Categorize URL if possible
            label = "URL"
            if "linkedin.com" in url.lower():
                label = "LINKEDIN"
            elif "github.com" in url.lower():
                label = "GITHUB"
            
            placeholder = f"[{label}_{i+1}]"
            placeholders[placeholder] = url
            scrubbed_text = scrubbed_text.replace(url, placeholder)
            stats["urls"] += 1

        # 4. Scrub Phone Numbers
        for p_re in self._phone_res:
            phones = p_re.findall(scrubbed_text)
            for i, phone in enumerate(phones):
                if len(phone.strip()) < 7: continue # Avoid false positives with short numbers
                placeholder = f"[PHONE_{i+1}]"
                if phone not in placeholders.values():
                    placeholders[placeholder] = phone
                    scrubbed_text = scrubbed_text.replace(phone, placeholder)
                    stats["phones"] += 1

        # 5. Scrub Addresses
        for a_re in self._address_res:
            addresses = a_re.findall(scrubbed_text)
            for i, addr in enumerate(addresses):
                placeholder = f"[ADDRESS_{i+1}]"
                if addr not in placeholders.values():
                    placeholders[placeholder] = addr
                    scrubbed_text = scrubbed_text.replace(addr, placeholder)
                    stats["addresses"] += 1

        return ScrubberResult(
            scrubbed_text=scrubbed_text,
            placeholders=placeholders,
            metadata=stats
        )

    def descrub(self, text: str, placeholders: Dict[str, str]) -> str:
        """
        Restore original values from placeholders.
        
        Args:
            text: Scrubbed text
            placeholders: Mapping of placeholder -> original value
            
        Returns:
            Text with original values restored
        """
        restored_text = text
        # Sort keys by length descending to avoid partial replacement issues 
        # (e.g. [EMAIL_10] being partially replaced by [EMAIL_1])
        sorted_placeholders = sorted(placeholders.items(), key=lambda x: len(x[0]), reverse=True)
        
        for placeholder, original in sorted_placeholders:
            restored_text = restored_text.replace(placeholder, original)
            
        return restored_text


# Singleton instance for application-wide use
pii_scrubber = PIIScrubber()
