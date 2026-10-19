"""
SwachhLoop AI — AI Guardrails, Defensive Validation & Privacy Protection
=======================================================================
Phase 5: Defensive engineering around all AI inputs, outputs, and workflows.

Capabilities:
  1. Prompt-Injection & Jailbreak Detection (heuristic & pattern-based).
  2. Input Sanitization & Boundary Enforcement (length, payload, image limits).
  3. PII & Sensitive Information Masking for audit trails and server logs.
  4. Output Validation & Constraint Checking (routes, vision bounding boxes, verification).
  5. RAG Grounding Verification & Context Containment.
  6. Resilient Async Retry with Exponential Backoff for AI provider calls.
"""

from __future__ import annotations

import asyncio
import io
import logging
import math
import re
from typing import Any, Callable, Coroutine, TypeVar

from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field

from backend.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T")


# ===========================================================================
# 1. Prompt-Injection & Adversarial Input Defense
# ===========================================================================

# High-risk adversarial markers attempting to alter model instructions or leak secrets
PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions?", re.IGNORECASE),
    re.compile(r"system\s+prompt\s*:", re.IGNORECASE),
    re.compile(r"reveal\s+(your\s+)?(system\s+prompt|secret|instructions?|api\s*key)", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(an\s+unfiltered|in\s+developer\s+mode|dan\b)", re.IGNORECASE),
    re.compile(r"act\s+as\s+(an\s+unrestricted|root|admin\b)", re.IGNORECASE),
    re.compile(r"<\s*\|\s*im_start\s*\|>", re.IGNORECASE),
    re.compile(r"<\s*\|\s*im_end\s*\|>", re.IGNORECASE),
    re.compile(r"\[\s*INST\s*\]|\[\s*/\s*INST\s*\]", re.IGNORECASE),
    re.compile(r"<\s*system\s*>|<\s*/\s*system\s*>", re.IGNORECASE),
    re.compile(r"drop\s+(database|table|collection)\b", re.IGNORECASE),
    re.compile(r"bypass\s+(safety|content\s+filter|guardrails?)", re.IGNORECASE),
]

# Structural characters that could break template framing
DELIMITER_ESCAPES = [
    ("```", "'''"),
    ("---", "- - -"),
    ("<|im_start|>", "[filtered_marker]"),
    ("<|im_end|>", "[filtered_marker]"),
    ("<system>", "[filtered_tag]"),
    ("</system>", "[/filtered_tag]"),
]


def detect_prompt_injection(text: str) -> tuple[bool, str | None]:
    """
    Check if the input text matches known prompt injection or jailbreak patterns.
    Returns (is_suspicious, matched_rule_description).
    """
    if not text:
        return False, None

    for pattern in PROMPT_INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            matched_str = match.group(0)
            return True, f"Suspicious instruction override pattern detected: '{matched_str}'"

    return False, None


def sanitize_untrusted_text(text: str) -> str:
    """
    Sanitize untrusted user-submitted text or external document content
    before embedding into LLM prompts or templates.
    Neutralizes markdown code blocks, prompt break tags, and control characters.
    """
    if not text:
        return ""

    sanitized = text
    # Strip null bytes and non-printable control characters except newline and tab
    sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", sanitized)

    # Escape delimiter collision markers
    for target, replacement in DELIMITER_ESCAPES:
        sanitized = sanitized.replace(target, replacement)

    return sanitized.strip()


# ===========================================================================
# 2. Privacy & PII Sanitization for Logs and Audits
# ===========================================================================

# Regexes for Indian mobile numbers, emails, and 12-digit identity numbers
PHONE_REGEX = re.compile(r"(?:\+91[\-\s]?)?[6-9]\d{9}\b")
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
AADHAAR_REGEX = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")


def sanitize_pii(text: str) -> str:
    """
    Redact personal phone numbers, emails, and 12-digit identity numbers
    from text before recording in server logs or public audit traces.
    """
    if not text or not settings.sanitize_logs_pii:
        return text

    sanitized = PHONE_REGEX.sub("[REDACTED_PHONE]", text)
    sanitized = EMAIL_REGEX.sub("[REDACTED_EMAIL]", sanitized)
    sanitized = AADHAAR_REGEX.sub("[REDACTED_ID]", sanitized)
    return sanitized


# ===========================================================================
# 3. Input Guardrails & Boundary Verification
# ===========================================================================

class GuardrailValidationResult(BaseModel):
    is_valid: bool
    sanitized_content: Any = None
    warning_or_error: str | None = None
    flags: list[str] = Field(default_factory=list)


def validate_complaint_text(text: str) -> GuardrailValidationResult:
    """
    Validate and guard citizen complaint text:
      - Enforces min length (1) and max length (max_complaint_text_length)
      - Inspects for prompt injection attempts
      - Sanitizes control sequences
    """
    if not text or not text.strip():
        return GuardrailValidationResult(
            is_valid=False,
            warning_or_error="Complaint text must not be empty.",
            flags=["EMPTY_TEXT"],
        )

    if len(text) > settings.max_complaint_text_length:
        return GuardrailValidationResult(
            is_valid=False,
            warning_or_error=f"Complaint text exceeds maximum allowed length of {settings.max_complaint_text_length} characters.",
            flags=["EXCEEDS_MAX_LENGTH"],
        )

    is_inj, reason = detect_prompt_injection(text)
    sanitized = sanitize_untrusted_text(text)
    flags = []
    if is_inj:
        flags.append("PROMPT_INJECTION_DETECTED")
        logger.warning("Guardrail flag: %s in complaint text", reason)

    return GuardrailValidationResult(
        is_valid=True,
        sanitized_content=sanitized,
        warning_or_error=reason,
        flags=flags,
    )


def validate_image_bytes(image_bytes: bytes, max_bytes: int | None = None) -> GuardrailValidationResult:
    """
    Validate uploaded image bytes:
      - Enforces file size limits
      - Verifies image integrity using PIL
      - Protects against zero-byte files, decompression bombs, or corrupted headers
    """
    limit = max_bytes or settings.max_image_upload_bytes
    if not image_bytes or len(image_bytes) == 0:
        return GuardrailValidationResult(
            is_valid=False,
            warning_or_error="Image file is empty (0 bytes).",
            flags=["ZERO_BYTE_FILE"],
        )

    if len(image_bytes) > limit:
        return GuardrailValidationResult(
            is_valid=False,
            warning_or_error=f"Image size ({len(image_bytes)} bytes) exceeds the maximum allowed limit of {limit} bytes.",
            flags=["EXCEEDS_FILE_SIZE_LIMIT"],
        )

    try:
        buf = io.BytesIO(image_bytes)
        img = Image.open(buf)
        img.verify()

        # Reopen to inspect dimensions safely (verify closes/invalidates the stream)
        buf.seek(0)
        img = Image.open(buf)
        width, height = img.size

        if width < 5 or height < 5:
            return GuardrailValidationResult(
                is_valid=False,
                warning_or_error=f"Image dimensions ({width}x{height}) are too small to be valid photographic evidence.",
                flags=["IMAGE_TOO_SMALL"],
            )

        # Decompression bomb defense: max 100 megapixels
        if width * height > 100_000_000:
            return GuardrailValidationResult(
                is_valid=False,
                warning_or_error="Image pixel area exceeds safety limit (possible decompression bomb).",
                flags=["IMAGE_AREA_EXCESSIVE"],
            )

        return GuardrailValidationResult(
            is_valid=True,
            sanitized_content={"width": width, "height": height, "format": img.format},
            flags=["VALID_IMAGE"],
        )

    except (UnidentifiedImageError, OSError, ValueError) as err:
        return GuardrailValidationResult(
            is_valid=False,
            warning_or_error=f"Corrupted or invalid image data: {str(err)}",
            flags=["CORRUPT_IMAGE"],
        )


def validate_route_request_points(locations: list[Any], max_stops: int | None = None) -> GuardrailValidationResult:
    """
    Validate route optimization input stops:
      - Validates minimum (1) and maximum count
      - Validates geographic coordinate bounds (-90 <= lat <= 90, -180 <= lon <= 180)
      - Detects duplicate coordinate stops
    """
    limit = max_stops or settings.max_route_stops
    if not locations:
        return GuardrailValidationResult(
            is_valid=False,
            warning_or_error="At least one valid location stop is required for route optimization.",
            flags=["EMPTY_LOCATIONS"],
        )

    if len(locations) > limit:
        return GuardrailValidationResult(
            is_valid=False,
            warning_or_error=f"Location stops count ({len(locations)}) exceeds maximum supported limit of {limit} stops.",
            flags=["EXCEEDS_MAX_STOPS"],
        )

    seen_coords = set()
    has_duplicates = False
    valid_count = 0

    for loc in locations:
        lat = getattr(loc, "latitude", None) if hasattr(loc, "latitude") else loc.get("latitude")
        lon = getattr(loc, "longitude", None) if hasattr(loc, "longitude") else loc.get("longitude")

        if lat is None or lon is None:
            return GuardrailValidationResult(
                is_valid=False,
                warning_or_error="Location stop missing required latitude or longitude.",
                flags=["MISSING_COORDINATES"],
            )

        try:
            flat, flon = float(lat), float(lon)
        except (ValueError, TypeError):
            return GuardrailValidationResult(
                is_valid=False,
                warning_or_error=f"Invalid coordinate format: lat={lat}, lon={lon}.",
                flags=["INVALID_COORDINATES"],
            )

        if math.isnan(flat) or math.isnan(flon) or not (-90.0 <= flat <= 90.0) or not (-180.0 <= flon <= 180.0):
            return GuardrailValidationResult(
                is_valid=False,
                warning_or_error=f"Coordinates out of bounds: lat={flat}, lon={flon}.",
                flags=["OUT_OF_BOUNDS_COORDINATES"],
            )

        coord_key = (round(flat, 6), round(flon, 6))
        if coord_key in seen_coords:
            has_duplicates = True
        else:
            seen_coords.add(coord_key)
        valid_count += 1

    flags = ["VALID_STOPS"]
    if has_duplicates:
        flags.append("DUPLICATE_STOPS_PRESENT")

    return GuardrailValidationResult(
        is_valid=True,
        sanitized_content={"valid_count": valid_count, "unique_coords": len(seen_coords)},
        warning_or_error="Duplicate coordinates detected in route request." if has_duplicates else None,
        flags=flags,
    )


def validate_rag_query_input(query: str) -> GuardrailValidationResult:
    """
    Validate civic RAG user query:
      - Validates non-empty and length within bounds
      - Detects prompt injection attempts
      - Sanitizes text
    """
    if not query or not query.strip():
        return GuardrailValidationResult(
            is_valid=False,
            warning_or_error="RAG query text must not be empty.",
            flags=["EMPTY_QUERY"],
        )

    if len(query) > settings.max_rag_query_length:
        return GuardrailValidationResult(
            is_valid=False,
            warning_or_error=f"RAG query exceeds max allowed length of {settings.max_rag_query_length} characters.",
            flags=["EXCEEDS_MAX_LENGTH"],
        )

    is_inj, reason = detect_prompt_injection(query)
    sanitized = sanitize_untrusted_text(query)
    flags = []
    if is_inj:
        flags.append("PROMPT_INJECTION_DETECTED")
        logger.warning("Guardrail flag: %s in RAG query", reason)

    return GuardrailValidationResult(
        is_valid=True,
        sanitized_content=sanitized,
        warning_or_error=reason,
        flags=flags,
    )


# ===========================================================================
# 4. Output Guardrails & Constraint Verification
# ===========================================================================

def validate_detection_output(result: Any) -> tuple[bool, str | None]:
    """
    Ensure waste detector results are physically plausible and adhere to contract.
    """
    if not hasattr(result, "confidence") or not hasattr(result, "waste_types"):
        return False, "Detection result missing mandatory attributes."

    if not (0.0 <= result.confidence <= 1.0):
        return False, f"Confidence score {result.confidence} out of range [0.0, 1.0]."

    for box in getattr(result, "bounding_boxes", []):
        coords = box.get("box_2d", []) if isinstance(box, dict) else getattr(box, "box_2d", [])
        if coords and len(coords) == 4:
            y1, x1, y2, x2 = coords
            if y1 < 0 or x1 < 0 or y2 < 0 or x2 < 0 or y2 < y1 or x2 < x1:
                return False, f"Malformed bounding box coordinates: {coords}"

    return True, None


def validate_route_constraints(
    opt_result: Any,
    expected_stop_count: int,
    max_duration_min: float = 480.0,  # 8 hours shift limit
    max_distance_km: float = 100.0,
) -> tuple[bool, list[str]]:
    """
    Validate route optimization output against physical and operational constraints:
      - Non-negative distance and travel duration
      - Number of ordered stops equals input stops
      - Feasibility limits (shift length, maximum distance)
    """
    violations: list[str] = []

    if opt_result.estimated_distance_km < 0:
        violations.append(f"Negative estimated distance: {opt_result.estimated_distance_km} km")

    if opt_result.estimated_duration_min < 0:
        violations.append(f"Negative estimated duration: {opt_result.estimated_duration_min} min")

    actual_stops = len(opt_result.ordered_locations)
    if actual_stops != expected_stop_count:
        violations.append(
            f"Stop count mismatch: received {expected_stop_count} locations, but route has {actual_stops} stops."
        )

    if opt_result.estimated_distance_km > max_distance_km:
        violations.append(
            f"Route distance ({opt_result.estimated_distance_km} km) exceeds single-vehicle operational limit of {max_distance_km} km."
        )

    if opt_result.estimated_duration_min > max_duration_min:
        violations.append(
            f"Route duration ({opt_result.estimated_duration_min} min) exceeds maximum shift boundary of {max_duration_min} min."
        )

    is_valid = len(violations) == 0
    return is_valid, violations


def validate_cleanup_verification_output(result: Any) -> tuple[bool, str | None]:
    """
    Ensure cleanup verification results adhere to numeric and state bounds.
    """
    if not hasattr(result, "status") or not hasattr(result, "change_score") or not hasattr(result, "confidence"):
        return False, "Verification result missing required fields."

    if not (0.0 <= result.change_score <= 1.0):
        return False, f"Change score {result.change_score} outside [0.0, 1.0]."

    if not (0.0 <= result.confidence <= 1.0):
        return False, f"Confidence score {result.confidence} outside [0.0, 1.0]."

    return True, None


def evaluate_rag_groundedness(
    answer: str,
    retrieved_sources: list[dict[str, Any]],
    language: str = "en",
) -> tuple[bool, float, str]:
    """
    Deterministic groundedness check for RAG responses.
    Verifies that the generated answer has supporting lexical overlap and citations
    from the retrieved knowledge snippets, avoiding ungrounded civic claims.

    Returns:
        (is_grounded, grounding_score, explanation)
    """
    if not retrieved_sources:
        return False, 0.0, "No source articles were retrieved to ground this answer."

    if not answer or not answer.strip():
        return False, 0.0, "Generated answer is empty."

    # Extract combined content and keywords from retrieved context
    context_tokens: set[str] = set()
    for s in retrieved_sources:
        text_source = f"{s.get('title', '')} {s.get('content', '')} {' '.join(s.get('keywords', []))}"
        tokens = re.findall(r"[\w\u0D00-\u0D7F]+", text_source.lower())
        for t in tokens:
            if len(t) > 2:
                context_tokens.add(t)

    # Tokenize generated answer
    answer_tokens = [t for t in re.findall(r"[\w\u0D00-\u0D7F]+", answer.lower()) if len(t) > 2]
    if not answer_tokens:
        return True, 1.0, "Answer contains only brief/stop words."

    overlap = [t for t in answer_tokens if t in context_tokens]
    grounding_score = round(len(overlap) / len(answer_tokens), 3)

    # A grounded answer should share at least 30% core lexical overlap with source context
    is_grounded = grounding_score >= 0.30
    explanation = (
        f"Grounded response: {int(grounding_score * 100)}% of content terms match retrieved civic sources."
        if is_grounded
        else f"Ungrounded civic claim risk: Only {int(grounding_score * 100)}% term overlap with verified documents."
    )
    return is_grounded, grounding_score, explanation


# ===========================================================================
# 5. Resilient Retry with Exponential Backoff
# ===========================================================================

async def resilient_call_with_retry(
    func: Callable[..., Coroutine[Any, Any, T]],
    *args: Any,
    max_retries: int | None = None,
    backoff_factor: float | None = None,
    timeout_seconds: float | None = None,
    operation_name: str = "AI_PROVIDER_CALL",
    **kwargs: Any,
) -> T:
    """
    Execute an async AI provider call with bounded retries, exponential backoff,
    and timeout protection.

    - Catches transient network errors, timeouts, and connection drops.
    - Prevents infinite loops or unbounded retries.
    - Re-raises final error if retries are exhausted.
    """
    retries = max_retries if max_retries is not None else settings.ai_max_retries
    factor = backoff_factor if backoff_factor is not None else settings.ai_retry_backoff_factor
    timeout = timeout_seconds if timeout_seconds is not None else settings.ai_request_timeout_seconds

    attempt = 0
    while True:
        attempt += 1
        try:
            return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
        except (asyncio.TimeoutError, TimeoutError) as err:
            logger.warning(
                "%s timed out after %.1fs (attempt %d of %d)",
                operation_name, timeout, attempt, retries + 1
            )
            if attempt > retries:
                raise TimeoutError(f"{operation_name} failed after {attempt} attempts: request timed out.") from err
        except Exception as err:
            # Check for non-retryable 4xx client errors
            status_code = getattr(err, "status_code", None) or getattr(err, "code", None)
            if status_code and 400 <= int(status_code) < 500 and int(status_code) != 429:
                logger.error("%s failed with client error %s. Not retrying.", operation_name, status_code)
                raise err

            logger.warning(
                "%s failed with error: %s (attempt %d of %d)",
                operation_name, err, attempt, retries + 1
            )
            if attempt > retries:
                logger.error("%s exhausted all %d retries.", operation_name, retries)
                raise err

        # Exponential backoff delay: 0.5s, 0.75s, 1.12s...
        sleep_time = 0.5 * (factor ** (attempt - 1))
        await asyncio.sleep(sleep_time)
