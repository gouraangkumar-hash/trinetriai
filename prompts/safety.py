"""Sanitization helpers that keep untrusted text from breaking out of prompt templates.

These helpers never reject input (so existing API behaviour is unchanged); they only
neutralize delimiter sequences used by our prompt templates, strip control characters,
and enforce a maximum length.
"""

import re

MAX_QUERY_CHARS = 1000
MAX_SINGLE_LINE_CHARS = 120
MAX_CHAT_MESSAGE_CHARS = 4000
MAX_EVIDENCE_CHARS = 8000

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_TRIPLE_QUOTES = re.compile(r'"{3,}|\'{3,}|`{3,}')
_HEADER_RUN = re.compile(r"={3,}")
_ANGLE_TAGS = re.compile(r"<\s*/?\s*(?:user_query|eye_evidence)[^>]*>", re.IGNORECASE)


def _neutralize(text: str) -> str:
    text = text.replace("\r", "")
    text = _CONTROL_CHARS.sub("", text)
    text = _ANGLE_TAGS.sub("", text)
    text = _TRIPLE_QUOTES.sub("'", text)
    text = _HEADER_RUN.sub("--", text)
    return text


def sanitize_user_text(text: str, max_chars: int = MAX_QUERY_CHARS) -> str:
    """Neutralize fence/header delimiters, strip control chars and truncate multi-line text."""
    cleaned = _neutralize(text or "").strip()
    return cleaned[:max_chars].rstrip()


def sanitize_single_line(text: str, max_chars: int = MAX_SINGLE_LINE_CHARS) -> str:
    """Like sanitize_user_text but collapses all whitespace/newlines into one line."""
    cleaned = " ".join(_neutralize(text or "").split())
    return cleaned[:max_chars].rstrip()


def sanitize_evidence(text: str, max_chars: int = MAX_EVIDENCE_CHARS) -> str:
    """Neutralize delimiters in model-generated evidence before re-embedding it in a prompt."""
    cleaned = _neutralize(text or "").strip()
    return cleaned[:max_chars].rstrip()
