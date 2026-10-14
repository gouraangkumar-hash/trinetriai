"""High-performance async Gemini LLM service for Trinetri AI.

Provides direct HTTP/2 streaming integration with Google Generative AI (Gemini Flash)
using httpx, with zero bulky third-party dependencies, support for parallel calls,
Server-Sent Events (SSE) streaming, and graceful error handling.
"""

import asyncio
import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Set

import httpx
from dotenv import load_dotenv

# Ensure local .env file is loaded if present
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

logger = logging.getLogger("trinetri.llm")

# httpx logs full request URLs at INFO; keep that quiet as defense-in-depth for secrets.
logging.getLogger("httpx").setLevel(logging.WARNING)

DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
PREFERRED_MODELS: List[str] = [
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
]
FALLBACK_MODEL = "gemini-3.8-flash"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

_MODEL_CACHE: Dict[str, List[str]] = {}
_WORKING_MODEL_CACHE: Dict[str, str] = {}

# Astrology discusses death, health and conflict; relax only the default thresholds so
# legitimate readings are not blocked while still blocking clearly harmful output.
SAFETY_SETTINGS: List[Dict[str, str]] = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]

# finishReason values that mean the model refused / was cut off by policy
_BLOCKED_FINISH_REASONS = {"SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII", "RECITATION"}


def get_effective_api_key(client_key: Optional[str] = None) -> Optional[str]:
    """Resolves the active Gemini API key from client header or server environment."""
    if client_key and client_key.strip():
        return client_key.strip()
    env_key = os.getenv("GEMINI_API_KEY", "").strip()
    return env_key if env_key else None


def _key_fingerprint(api_key: str) -> str:
    return hashlib.sha256(api_key.encode()).hexdigest()[:16]


def _auth_headers(api_key: str) -> Dict[str, str]:
    """Sends the key in a header so it never appears in URLs, logs, or tracebacks."""
    return {"x-goog-api-key": api_key, "Content-Type": "application/json"}


def _pick_fallback(available: List[str], exclude: Set[str]) -> Optional[str]:
    """Chooses a model that has not been tried yet, preferring the configured list."""
    if available:
        for pref in PREFERRED_MODELS:
            if pref in available and pref not in exclude:
                return pref
        for cand in available:
            if cand not in exclude:
                return cand
    # Fallback directly to PREFERRED_MODELS when available list is empty or discovery timed out
    for pref in PREFERRED_MODELS:
        if pref not in exclude:
            return pref
    return None


def _extract_error_message(resp_text: str, fallback: str) -> str:
    try:
        err_json = json.loads(resp_text)
        return err_json.get("error", {}).get("message", fallback)
    except Exception:
        return fallback


async def discover_available_models(api_key: Optional[str] = None) -> List[str]:
    """Queries Gemini ListModels endpoint to find all models that support generateContent."""
    effective_key = get_effective_api_key(api_key)
    if not effective_key:
        return []

    cache_key = _key_fingerprint(effective_key)
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]

    url = GEMINI_BASE_URL
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=_auth_headers(effective_key))
            if resp.status_code == 200:
                data = resp.json()
                models = data.get("models", [])
                valid = []
                for m in models:
                    methods = m.get("supportedGenerationMethods", [])
                    if "generateContent" in methods:
                        raw_name = m.get("name", "")
                        clean_name = raw_name.replace("models/", "").strip()
                        if clean_name:
                            valid.append(clean_name)
                if valid:
                    _MODEL_CACHE[cache_key] = valid
                    logger.info("Discovered %d active Gemini models for key: %s", len(valid), valid[:5])
                    return valid
    except Exception as exc:
        logger.warning("Could not list models from Gemini API: %s", type(exc).__name__)

    return []


async def resolve_best_model(api_key: Optional[str] = None, requested_model: Optional[str] = None) -> str:
    """Resolves the best supported active model for the provided API key."""
    if requested_model and requested_model.strip():
        return requested_model.strip()

    effective_key = get_effective_api_key(api_key)
    if effective_key:
        cache_key = _key_fingerprint(effective_key)
        if cache_key in _WORKING_MODEL_CACHE:
            return _WORKING_MODEL_CACHE[cache_key]

        available = await discover_available_models(effective_key)
        for pref in PREFERRED_MODELS:
            if pref in available:
                _WORKING_MODEL_CACHE[cache_key] = pref
                return pref
        if available:
            _WORKING_MODEL_CACHE[cache_key] = available[0]
            return available[0]

    return DEFAULT_MODEL


class GeminiService:
    """Async client communicating directly with Google Generative Language API."""

    MAX_TRANSIENT_RETRIES = 2

    def __init__(self, timeout_seconds: float = 90.0):
        self.timeout = httpx.Timeout(timeout_seconds, connect=15.0)

    @staticmethod
    def _build_payload(
        system_instruction: str,
        contents: List[Dict[str, Any]],
        temperature: float,
        max_output_tokens: int,
    ) -> Dict[str, Any]:
        return {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_output_tokens,
            },
            "safetySettings": SAFETY_SETTINGS,
        }

    @staticmethod
    async def _next_model_on_fallback(effective_key: str, tried: Set[str]) -> Optional[str]:
        """Finds an untried model after a failure or timeout and records it as the working default."""
        available = await discover_available_models(effective_key)
        fallback = _pick_fallback(available, tried)
        if fallback:
            _WORKING_MODEL_CACHE[_key_fingerprint(effective_key)] = fallback
        return fallback

    _next_model_on_404 = _next_model_on_fallback

    async def generate_content(
        self,
        system_instruction: str,
        user_prompt: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.4,
        max_output_tokens: int = 3000,
        _retry_count: int = 0,
        _tried_models: Optional[Set[str]] = None,
    ) -> str:
        """Executes a single synchronous-style async generation call with auto-fallback."""
        effective_key = get_effective_api_key(api_key)
        if not effective_key:
            raise ValueError(
                "Gemini API Key is not configured. Please supply an API key via "
                "the UI settings or define GEMINI_API_KEY in your server environment."
            )

        active_model = model or await resolve_best_model(effective_key)
        tried = set(_tried_models or set())
        tried.add(active_model)

        url = f"{GEMINI_BASE_URL}/{active_model}:generateContent"
        payload = self._build_payload(
            system_instruction,
            [{"role": "user", "parts": [{"text": user_prompt}]}],
            temperature,
            max_output_tokens,
        )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload, headers=_auth_headers(effective_key))

                if response.status_code == 404:
                    fallback = await self._next_model_on_fallback(effective_key, tried)
                    if fallback:
                        logger.warning(
                            "Model %s returned 404, automatically switching to %s",
                            active_model,
                            fallback,
                        )
                        return await self.generate_content(
                            system_instruction,
                            user_prompt,
                            api_key=effective_key,
                            model=fallback,
                            temperature=temperature,
                            max_output_tokens=max_output_tokens,
                            _retry_count=_retry_count,
                            _tried_models=tried,
                        )

                if response.status_code in (429, 503):
                    if _retry_count < self.MAX_TRANSIENT_RETRIES:
                        backoff = 2.0 * (_retry_count + 1)
                        logger.warning(
                            "Gemini API returned status %d on %s, retrying in %.1fs (attempt %d/%d)...",
                            response.status_code,
                            active_model,
                            backoff,
                            _retry_count + 1,
                            self.MAX_TRANSIENT_RETRIES,
                        )
                        await asyncio.sleep(backoff)
                        return await self.generate_content(
                            system_instruction,
                            user_prompt,
                            api_key=effective_key,
                            model=active_model,
                            temperature=temperature,
                            max_output_tokens=max_output_tokens,
                            _retry_count=_retry_count + 1,
                            _tried_models=tried,
                        )
                    # When transient retries are exhausted on current model, failover to next model
                    fallback = await self._next_model_on_fallback(effective_key, tried)
                    if fallback:
                        logger.warning(
                            "Model %s returned status %d after %d retries, automatically failing over to %s",
                            active_model,
                            response.status_code,
                            self.MAX_TRANSIENT_RETRIES,
                            fallback,
                        )
                        return await self.generate_content(
                            system_instruction,
                            user_prompt,
                            api_key=effective_key,
                            model=fallback,
                            temperature=temperature,
                            max_output_tokens=max_output_tokens,
                            _retry_count=0,
                            _tried_models=tried,
                        )

                if response.status_code != 200:
                    err_detail = _extract_error_message(response.text, response.text)
                    raise RuntimeError(f"Gemini API Error ({response.status_code}): {err_detail}")

                data = response.json()
                candidates = data.get("candidates") or []
                if not candidates:
                    prompt_feedback = data.get("promptFeedback") or {}
                    block_reason = prompt_feedback.get("blockReason")
                    if block_reason:
                        raise RuntimeError(f"Gemini generation blocked by safety policy ({block_reason})")
                    return ""

                content_obj = candidates[0].get("content") or {}
                parts = content_obj.get("parts") or []
                text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))

                finish_reason = candidates[0].get("finishReason")
                if finish_reason == "MAX_TOKENS":
                    logger.warning(
                        "Gemini response from %s was truncated (MAX_TOKENS, limit=%d)",
                        active_model,
                        max_output_tokens,
                    )
                elif finish_reason in _BLOCKED_FINISH_REASONS and not text.strip():
                    raise RuntimeError(f"Gemini generation blocked ({finish_reason})")
                return text

            except httpx.TimeoutException as exc:
                fallback = await self._next_model_on_fallback(effective_key, tried)
                if fallback:
                    logger.warning(
                        "Model %s timed out (%s), automatically failing over to %s",
                        active_model,
                        type(exc).__name__,
                        fallback,
                    )
                    return await self.generate_content(
                        system_instruction,
                        user_prompt,
                        api_key=effective_key,
                        model=fallback,
                        temperature=temperature,
                        max_output_tokens=max_output_tokens,
                        _retry_count=0,
                        _tried_models=tried,
                    )
                raise RuntimeError(f"Network error communicating with Gemini API: {type(exc).__name__}")
            except httpx.RequestError as exc:
                raise RuntimeError(f"Network error communicating with Gemini API: {type(exc).__name__}")

    async def stream_generate_content(
        self,
        system_instruction: str,
        contents: List[Dict[str, Any]],
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.4,
        max_output_tokens: int = 4000,
        _retry_count: int = 0,
        _tried_models: Optional[Set[str]] = None,
    ) -> AsyncIterator[str]:
        """Streams tokens from Gemini API via Server-Sent Events (SSE) with auto-fallback."""
        effective_key = get_effective_api_key(api_key)
        if not effective_key:
            raise ValueError(
                "Gemini API Key is not configured. Please supply an API key via "
                "the UI settings or define GEMINI_API_KEY in your server environment."
            )

        active_model = model or await resolve_best_model(effective_key)
        tried = set(_tried_models or set())
        tried.add(active_model)

        url = f"{GEMINI_BASE_URL}/{active_model}:streamGenerateContent?alt=sse"
        payload = self._build_payload(system_instruction, contents, temperature, max_output_tokens)

        emitted_any = False
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                async with client.stream(
                    "POST", url, json=payload, headers=_auth_headers(effective_key)
                ) as response:
                    if response.status_code == 404:
                        fallback = await self._next_model_on_fallback(effective_key, tried)
                        if fallback:
                            logger.warning(
                                "Stream model %s returned 404, falling back to %s",
                                active_model,
                                fallback,
                            )
                            async for tok in self.stream_generate_content(
                                system_instruction,
                                contents,
                                api_key=effective_key,
                                model=fallback,
                                temperature=temperature,
                                max_output_tokens=max_output_tokens,
                                _retry_count=_retry_count,
                                _tried_models=tried,
                            ):
                                yield tok
                            return

                    if response.status_code in (429, 503):
                        # Safe to retry: no tokens have been emitted before the status line.
                        await response.aread()
                        if _retry_count < self.MAX_TRANSIENT_RETRIES:
                            backoff = 2.0 * (_retry_count + 1)
                            logger.warning(
                                "Gemini stream returned status %d on %s, retrying in %.1fs (attempt %d/%d)...",
                                response.status_code,
                                active_model,
                                backoff,
                                _retry_count + 1,
                                self.MAX_TRANSIENT_RETRIES,
                            )
                            await asyncio.sleep(backoff)
                            async for tok in self.stream_generate_content(
                                system_instruction,
                                contents,
                                api_key=effective_key,
                                model=active_model,
                                temperature=temperature,
                                max_output_tokens=max_output_tokens,
                                _retry_count=_retry_count + 1,
                                _tried_models=tried,
                            ):
                                yield tok
                            return
                        fallback = await self._next_model_on_fallback(effective_key, tried)
                        if fallback:
                            logger.warning(
                                "Stream model %s returned status %d after %d retries, automatically failing over to %s",
                                active_model,
                                response.status_code,
                                self.MAX_TRANSIENT_RETRIES,
                                fallback,
                            )
                            async for tok in self.stream_generate_content(
                                system_instruction,
                                contents,
                                api_key=effective_key,
                                model=fallback,
                                temperature=temperature,
                                max_output_tokens=max_output_tokens,
                                _retry_count=0,
                                _tried_models=tried,
                            ):
                                yield tok
                            return

                    if response.status_code != 200:
                        err_bytes = await response.aread()
                        err_text = err_bytes.decode("utf-8", errors="replace")
                        err_text = _extract_error_message(err_text, err_text)
                        raise RuntimeError(f"Gemini Streaming Error ({response.status_code}): {err_text}")

                    finish_reason: Optional[str] = None
                    block_reason: Optional[str] = None

                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue

                        feedback = chunk.get("promptFeedback") or {}
                        if feedback.get("blockReason"):
                            block_reason = feedback.get("blockReason")

                        candidates = chunk.get("candidates") or []
                        if candidates:
                            cand = candidates[0]
                            if cand.get("finishReason"):
                                finish_reason = cand.get("finishReason")
                            content_obj = cand.get("content") or {}
                            parts = content_obj.get("parts") or []
                            for part in parts:
                                if isinstance(part, dict):
                                    text_chunk = part.get("text", "")
                                    if text_chunk:
                                        emitted_any = True
                                        yield text_chunk

                    if finish_reason == "MAX_TOKENS":
                        logger.warning(
                            "Gemini stream from %s was truncated (MAX_TOKENS, limit=%d)",
                            active_model,
                            max_output_tokens,
                        )
                    if not emitted_any:
                        if block_reason:
                            raise RuntimeError(f"Gemini generation blocked by safety policy ({block_reason})")
                        if finish_reason in _BLOCKED_FINISH_REASONS:
                            raise RuntimeError(f"Gemini generation blocked ({finish_reason})")

            except httpx.TimeoutException as exc:
                if not emitted_any:
                    fallback = await self._next_model_on_fallback(effective_key, tried)
                    if fallback:
                        logger.warning(
                            "Stream model %s timed out (%s), automatically failing over to %s",
                            active_model,
                            type(exc).__name__,
                            fallback,
                        )
                        async for tok in self.stream_generate_content(
                            system_instruction,
                            contents,
                            api_key=effective_key,
                            model=fallback,
                            temperature=temperature,
                            max_output_tokens=max_output_tokens,
                            _retry_count=0,
                            _tried_models=tried,
                        ):
                            yield tok
                        return
                raise RuntimeError(f"Network error streaming from Gemini API: {type(exc).__name__}")
            except httpx.RequestError as exc:
                raise RuntimeError(f"Network error streaming from Gemini API: {type(exc).__name__}")


# Global singleton instance
gemini_service = GeminiService()
