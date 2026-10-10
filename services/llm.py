"""High-performance async Gemini LLM service for Trinetri AI.

Provides direct HTTP/2 streaming integration with Google Generative AI (Gemini Flash)
using httpx, with zero bulky third-party dependencies, support for parallel calls,
Server-Sent Events (SSE) streaming, and graceful error handling.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx
from dotenv import load_dotenv

# Ensure local .env file is loaded if present
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

logger = logging.getLogger("trinetri.llm")

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
FALLBACK_MODEL = "gemini-1.5-flash"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


def get_effective_api_key(client_key: Optional[str] = None) -> Optional[str]:
    """Resolves the active Gemini API key from client header or server environment."""
    if client_key and client_key.strip():
        return client_key.strip()
    env_key = os.getenv("GEMINI_API_KEY", "").strip()
    return env_key if env_key else None


class GeminiService:
    """Async client communicating directly with Google Generative Language API."""

    def __init__(self, timeout_seconds: float = 60.0):
        self.timeout = httpx.Timeout(timeout_seconds, connect=10.0)

    async def generate_content(
        self,
        system_instruction: str,
        user_prompt: str,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.4,
        max_output_tokens: int = 3000,
    ) -> str:
        """Executes a single synchronous-style async generation call."""
        effective_key = get_effective_api_key(api_key)
        if not effective_key:
            raise ValueError(
                "Gemini API Key is not configured. Please supply an API key via "
                "the UI settings or define GEMINI_API_KEY in your server environment."
            )

        url = f"{GEMINI_BASE_URL}/{model}:generateContent?key={effective_key}"
        payload = {
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_prompt}],
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_output_tokens,
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload)
                if response.status_code == 404 and model != FALLBACK_MODEL:
                    # Model might not be available in region, retry with fallback
                    logger.warning("Model %s returned 404, falling back to %s", model, FALLBACK_MODEL)
                    return await self.generate_content(
                        system_instruction,
                        user_prompt,
                        api_key=effective_key,
                        model=FALLBACK_MODEL,
                        temperature=temperature,
                        max_output_tokens=max_output_tokens,
                    )

                if response.status_code != 200:
                    err_detail = response.text
                    try:
                        err_json = response.json()
                        err_detail = err_json.get("error", {}).get("message", err_detail)
                    except Exception:
                        pass
                    raise RuntimeError(f"Gemini API Error ({response.status_code}): {err_detail}")

                data = response.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    return ""

                parts = candidates[0].get("content", {}).get("parts", [])
                return "".join(part.get("text", "") for part in parts)

            except httpx.RequestError as exc:
                raise RuntimeError(f"Network error communicating with Gemini API: {str(exc)}")

    async def stream_generate_content(
        self,
        system_instruction: str,
        contents: List[Dict[str, Any]],
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.4,
        max_output_tokens: int = 4000,
    ) -> AsyncIterator[str]:
        """Streams tokens from Gemini API via Server-Sent Events (SSE)."""
        effective_key = get_effective_api_key(api_key)
        if not effective_key:
            raise ValueError(
                "Gemini API Key is not configured. Please supply an API key via "
                "the UI settings or define GEMINI_API_KEY in your server environment."
            )

        url = f"{GEMINI_BASE_URL}/{model}:streamGenerateContent?alt=sse&key={effective_key}"
        payload = {
            "system_instruction": {
                "parts": [{"text": system_instruction}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_output_tokens,
            },
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        err_bytes = await response.aread()
                        err_text = err_bytes.decode("utf-8", errors="replace")
                        try:
                            err_json = json.loads(err_text)
                            err_text = err_json.get("error", {}).get("message", err_text)
                        except Exception:
                            pass
                        raise RuntimeError(f"Gemini Streaming Error ({response.status_code}): {err_text}")

                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            candidates = chunk.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                for part in parts:
                                    text_chunk = part.get("text", "")
                                    if text_chunk:
                                        yield text_chunk
                        except json.JSONDecodeError:
                            continue

            except httpx.RequestError as exc:
                raise RuntimeError(f"Network error streaming from Gemini API: {str(exc)}")


# Global singleton instance
gemini_service = GeminiService()
