"""LLM Client Factory and Demo Mode Manager.

Connects to Groq API using OpenAI-compatible endpoints or provides deterministic
demo mode fallback when credentials are not configured or when network is offline.
Includes caching to conserve API quota and avoid redundant model calls.
"""

import os
from pathlib import Path
from typing import Optional, Dict
from dotenv import load_dotenv
from openai import OpenAI

# Load .env file from project root
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class LLMClientManager:
    """Manages LLM client lifecycle, caching, and demo mode fallback."""

    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.model = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b").strip()
        self.base_url = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1").strip()
        
        self.is_demo_mode = not bool(self.api_key) or self.api_key.startswith("your_actual")
        self._client: Optional[OpenAI] = None
        self._cache: Dict[str, str] = {}
        
        if not self.is_demo_mode:
            try:
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    timeout=8.0,
                    max_retries=1
                )
            except Exception:
                self.is_demo_mode = True

    def generate_explanation(self, prompt: str, system_prompt: str, fallback: str) -> str:
        """Call Groq API or return fallback in demo mode, with caching for quota protection."""
        if self.is_demo_mode or not self._client:
            return fallback

        cache_key = f"{self.model}::{prompt.strip()}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.2
            )
            content = resp.choices[0].message.content
            if content and content.strip():
                clean_res = content.strip()
                self._cache[cache_key] = clean_res
                return clean_res
            return fallback
        except Exception:
            return fallback


# Global singleton
llm_manager = LLMClientManager()
