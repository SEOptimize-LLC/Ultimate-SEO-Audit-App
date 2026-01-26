"""OpenRouter API Client.

Handles LLM API calls for AI-powered SEO analysis and recommendations.
https://openrouter.ai/
"""

import requests
import json
from typing import Optional, Generator
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Response from LLM analysis."""
    content: str
    model: str
    usage: dict
    finish_reason: str


class OpenRouterClient:
    """Client for OpenRouter API.

    Supports multiple LLM models for SEO analysis.
    """

    BASE_URL = "https://openrouter.ai/api/v1"

    # Available models for SEO analysis
    MODELS = {
        "claude-3.5-sonnet": "anthropic/claude-3.5-sonnet",
        "claude-3-opus": "anthropic/claude-3-opus",
        "gpt-4o": "openai/gpt-4o",
        "gpt-4-turbo": "openai/gpt-4-turbo",
        "gemini-pro": "google/gemini-pro-1.5",
    }

    DEFAULT_MODEL = "anthropic/claude-3.5-sonnet"

    def __init__(self, api_key: str, default_model: Optional[str] = None):
        """Initialize the client.

        Args:
            api_key: OpenRouter API key
            default_model: Default model to use
        """
        self.api_key = api_key
        self.default_model = default_model or self.DEFAULT_MODEL

    def _get_headers(self) -> dict:
        """Get request headers."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://seo-auditor.local",
            "X-Title": "Ultimate SEO Auditor",
        }

    def _make_request(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        stream: bool = False,
    ) -> dict:
        """Make a chat completion request.

        Args:
            messages: List of message dictionaries
            model: Model to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            stream: Whether to stream response

        Returns:
            API response dictionary
        """
        url = f"{self.BASE_URL}/chat/completions"

        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
        }

        response = requests.post(
            url,
            headers=self._get_headers(),
            json=payload,
            timeout=120,
        )
        response.raise_for_status()

        return response.json()

    def analyze(
        self,
        system_prompt: str,
        user_content: str,
        model: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Run analysis with system prompt and user content.

        Args:
            system_prompt: System prompt with expertise/instructions
            user_content: User message with audit data
            model: Model to use
            max_tokens: Maximum response tokens

        Returns:
            LLMResponse with analysis
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        result = self._make_request(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
        )

        choice = result.get("choices", [{}])[0]

        return LLMResponse(
            content=choice.get("message", {}).get("content", ""),
            model=result.get("model", ""),
            usage=result.get("usage", {}),
            finish_reason=choice.get("finish_reason", ""),
        )

    def analyze_stream(
        self,
        system_prompt: str,
        user_content: str,
        model: Optional[str] = None,
        max_tokens: int = 4096,
    ) -> Generator[str, None, None]:
        """Run analysis with streaming response.

        Args:
            system_prompt: System prompt
            user_content: User message with audit data
            model: Model to use
            max_tokens: Maximum response tokens

        Yields:
            Content chunks as they arrive
        """
        url = f"{self.BASE_URL}/chat/completions"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        payload = {
            "model": model or self.default_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.3,
            "stream": True,
        }

        with requests.post(
            url,
            headers=self._get_headers(),
            json=payload,
            stream=True,
            timeout=120,
        ) as response:
            response.raise_for_status()

            for line in response.iter_lines():
                if line:
                    line = line.decode("utf-8")
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

    def test_connection(self) -> bool:
        """Test API connection.

        Returns:
            True if connection successful
        """
        try:
            messages = [
                {"role": "user", "content": "Say 'OK' if you can hear me."}
            ]
            result = self._make_request(
                messages=messages,
                max_tokens=10,
            )
            return "choices" in result
        except Exception:
            return False

    def get_available_models(self) -> list[str]:
        """Get list of available model IDs.

        Returns:
            List of model identifiers
        """
        return list(self.MODELS.values())


def create_client_from_streamlit() -> Optional[OpenRouterClient]:
    """Create OpenRouter client from Streamlit secrets.

    Returns:
        OpenRouterClient if API key available, None otherwise
    """
    try:
        import streamlit as st
        api_key = st.secrets.get("OPENROUTER_API_KEY")
        default_model = st.secrets.get("DEFAULT_MODEL")

        if api_key:
            return OpenRouterClient(api_key, default_model)
        return None
    except Exception:
        return None


# Convenience function for quick analysis
def analyze_audit_data(
    audit_type: str,
    issues_data: str,
    api_key: str,
    model: Optional[str] = None,
) -> str:
    """Quick function to analyze audit data.

    Args:
        audit_type: Type of audit (technical, onpage, backlink, competitor)
        issues_data: JSON or formatted string of issues
        api_key: OpenRouter API key
        model: Optional model override

    Returns:
        Analysis text
    """
    from prompts import (
        get_technical_prompt,
        get_onpage_prompt,
        get_backlink_prompt,
        get_competitor_prompt,
    )

    prompt_map = {
        "technical": get_technical_prompt,
        "onpage": get_onpage_prompt,
        "backlink": get_backlink_prompt,
        "competitor": get_competitor_prompt,
    }

    if audit_type not in prompt_map:
        raise ValueError(f"Unknown audit type: {audit_type}")

    system_prompt = prompt_map[audit_type]()
    client = OpenRouterClient(api_key)

    response = client.analyze(
        system_prompt=system_prompt,
        user_content=issues_data,
        model=model,
    )

    return response.content
