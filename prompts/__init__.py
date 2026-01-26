"""Prompts module for Ultimate SEO Auditor.

Contains LLM prompt templates for AI-powered analysis.
"""

from .technical_prompt import get_technical_prompt
from .onpage_prompt import get_onpage_prompt
from .backlink_prompt import get_backlink_prompt
from .competitor_prompt import get_competitor_prompt

__all__ = [
    "get_technical_prompt",
    "get_onpage_prompt",
    "get_backlink_prompt",
    "get_competitor_prompt",
]
