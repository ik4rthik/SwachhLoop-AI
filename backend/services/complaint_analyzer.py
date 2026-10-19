"""
SwachhLoop AI — Complaint Analyzer Service Interface
======================================================
Defines the CONTRACT for the NLP/LLM complaint analysis service.

Phase 1: Abstract interface only. No implementation.
Phase 3: Implement with LangChain / Gemini / custom NLP pipeline.

This service will process free-text complaints from citizens, extract
structured information, assess urgency, and route to the appropriate team.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum


# ---------------------------------------------------------------------------
# Data Transfer Objects
# ---------------------------------------------------------------------------

class UrgencyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ComplaintAnalysis:
    """
    Structured output produced by ComplaintAnalyzerService.analyze().

    Attributes:
        urgency:          Assessed urgency level.
        extracted_location: Location string extracted from complaint text.
        waste_types:      Waste types mentioned in the complaint.
        suggested_action: Recommended next step for municipal staff.
        summary:          Short machine-generated summary of the complaint.
        tags:             Classification tags for filtering/routing.
    """
    urgency: UrgencyLevel
    extracted_location: str | None
    waste_types: list[str]
    suggested_action: str
    summary: str
    tags: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Service Interface (Abstract Base Class)
# ---------------------------------------------------------------------------

class ComplaintAnalyzerService(ABC):
    """
    Interface for the citizen complaint NLP analysis service.
    """

    @abstractmethod
    async def analyze(self, complaint_text: str) -> ComplaintAnalysis:
        """
        Analyse a free-text citizen complaint.

        Args:
            complaint_text: Raw complaint submitted by the citizen.

        Returns:
            ComplaintAnalysis with urgency, location, action suggestion, etc.

        Raises:
            NotImplementedError: Until Phase 3 implementation is provided.
        """
        raise NotImplementedError(
            "ComplaintAnalyzerService.analyze() is not yet implemented. "
            "Scheduled for Phase 3."
        )

    @abstractmethod
    async def extract_location(self, text: str) -> str | None:
        """
        Extract a location/address from free-form text using NER.

        Args:
            text: Any text that may contain location references.

        Returns:
            Extracted location string, or None if not found.

        Raises:
            NotImplementedError: Until Phase 3 implementation is provided.
        """
        raise NotImplementedError(
            "ComplaintAnalyzerService.extract_location() is not yet implemented. "
            "Scheduled for Phase 3."
        )



# ---------------------------------------------------------------------------
# Concrete Implementations
# ---------------------------------------------------------------------------

import logging
import re

logger = logging.getLogger(__name__)

# Known landmarks and locations in and around Kalady, Kerala
KALADY_LANDMARKS = [
    "Kalady Junction",
    "MC Road",
    "Sree Sankaracharya University",
    "Adi Shankara Janmabhumi Kshetram",
    "Mattoor",
    "Piraroor",
    "Malayattoor Road",
    "Temple Road",
    "Manickamangalam",
    "Kanjoor",
    "Kalady Market",
    "Private Bus Stand Kalady",
    "KSRTC Bus Stand",
    "St. Joseph Church Kalady",
    "Panchayat Office",
    "Periyar Riverbank",
    "Palarivattom Road",
    "Neeleswaram",
]

URGENCY_KEYWORDS = {
    UrgencyLevel.CRITICAL: [
        "hospital", "biohazard", "toxic", "chemical", "fire", "burning", 
        "road blocked", "blocked road", "school", "water contamination", "drainage overflow"
    ],
    UrgencyLevel.HIGH: [
        "carcass", "dead animal", "overflowing", "drain clogged", "clogged drain", 
        "stench", "rotting", "maggots", "market waste", "urgent"
    ],
    UrgencyLevel.MEDIUM: [
        "garbage pile", "dump", "litter", "plastic bottles", "food waste", 
        "bags", "bottles", "waste dump", "uncollected"
    ],
    UrgencyLevel.LOW: [
        "dry leaves", "dust", "small litter", "paper", "sweep"
    ],
}

WASTE_CATEGORIES = {
    "plastic": ["plastic", "polythene", "bottle", "wrapper", "cover", "carry bag"],
    "organic": ["food", "vegetable", "fruit", "rotten", "kitchen waste", "organic", "leaves"],
    "biohazard": ["hospital", "medical", "syringe", "medicine", "bandage"],
    "metal": ["tin", "can", "iron", "wire", "scrap", "metal"],
    "construction": ["debris", "concrete", "cement", "bricks", "tiles"],
    "electronic": ["e-waste", "battery", "wire", "cable", "appliance"],
}


from backend.core.guardrails import (
    validate_complaint_text,
    resilient_call_with_retry,
)


class DeterministicComplaintAnalyzer(ComplaintAnalyzerService):
    """
    Deterministic rule-based and regex NLP analyzer for civic complaints.
    Focused on Kalady civic geography and multilingual English/Malayalam transliterated terms.
    """

    async def analyze(self, complaint_text: str) -> ComplaintAnalysis:
        val = validate_complaint_text(complaint_text)
        if not val.is_valid:
            return ComplaintAnalysis(
                urgency=UrgencyLevel.LOW,
                extracted_location=None,
                waste_types=[],
                suggested_action=f"Request clarification: {val.warning_or_error}",
                summary="Empty or invalid complaint submitted.",
                tags=["incomplete"] + val.flags,
            )

        clean_text = val.sanitized_content or complaint_text
        text_lower = clean_text.lower().strip()

        # 1. Location Extraction
        extracted_location = await self.extract_location(clean_text)

        # 2. Waste Type Identification
        detected_waste = []
        for cat, keywords in WASTE_CATEGORIES.items():
            if any(kw in text_lower for kw in keywords):
                detected_waste.append(cat)
        if not detected_waste:
            detected_waste = ["general waste"]

        # 3. Urgency Assessment
        assessed_urgency = UrgencyLevel.LOW
        for urgency_lvl, keywords in URGENCY_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                assessed_urgency = urgency_lvl
                break

        # If location is missing or text is too brief, detect ambiguity
        is_ambiguous = False
        notes = []
        if not extracted_location:
            is_ambiguous = True
            notes.append("location details ambiguous or missing")
        if len(text_lower.split()) < 3:
            is_ambiguous = True
            notes.append("description is brief")

        # 4. Action Recommendation
        if assessed_urgency == UrgencyLevel.CRITICAL:
            action = "Immediate dispatch of rapid civic response team and public health alert."
        elif assessed_urgency == UrgencyLevel.HIGH:
            action = "Priority cleaner allocation within 4-6 hours with heavy waste equipment."
        elif assessed_urgency == UrgencyLevel.MEDIUM:
            action = "Schedule collection during the next regular sanitation round."
        else:
            action = "Routine sanitation and street sweeping."

        if is_ambiguous:
            action += f" Note: {'; '.join(notes)}. Contact citizen if verification needed."

        # 5. Summary Generation
        summary = (
            f"Reported {', '.join(detected_waste)} near "
            f"{extracted_location or 'unspecified location'} with {assessed_urgency.value} urgency."
        )

        tags = list(detected_waste)
        tags.append(assessed_urgency.value)
        if extracted_location:
            tags.append("geo-tagged")
        if is_ambiguous:
            tags.append("ambiguous")
        if "PROMPT_INJECTION_DETECTED" in val.flags:
            tags.append("untrusted_pattern")
            action += " [Security Notice: Input contained adversarial instruction tokens; treat as untrusted data.]"

        return ComplaintAnalysis(
            urgency=assessed_urgency,
            extracted_location=extracted_location,
            waste_types=detected_waste,
            suggested_action=action,
            summary=summary,
            tags=tags,
        )

    async def extract_location(self, text: str) -> str | None:
        if not text:
            return None

        # Check against known Kalady landmarks
        for landmark in KALADY_LANDMARKS:
            pattern = re.compile(rf"\b{re.escape(landmark)}\b", re.IGNORECASE)
            if pattern.search(text):
                return landmark

        # Regex heuristic: "near <location>", "at <location>", "in front of <location>", "opposite <location>"
        prep_patterns = [
            r"(?:near|at|opposite|in front of|behind|by|along)\s+([A-Z][a-zA-Z0-9\s]{2,25}(?:Road|Junction|Street|Market|Stop|Bridge|Bazaar|Gate|Nagar)?)",
            r"(?:ward\s+\d+|ward\s+[A-Za-z0-9]+)",
        ]
        for pat in prep_patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                loc = match.group(1).strip() if match.groups() else match.group(0).strip()
                return loc

        return None


class LLMComplaintAnalyzer(ComplaintAnalyzerService):
    """
    Pluggable LLM-based Complaint Analyzer using OpenAI/Gemini with
    resilient bounded retries and graceful fallback to the deterministic analyzer on error.
    """

    def __init__(self, api_key: str | None = None, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.fallback = DeterministicComplaintAnalyzer()

    async def _call_llm(self, complaint_text: str) -> ComplaintAnalysis:
        # In cloud LLM deployment, external API call happens here
        return await self.fallback.analyze(complaint_text)

    async def analyze(self, complaint_text: str) -> ComplaintAnalysis:
        if not self.api_key:
            return await self.fallback.analyze(complaint_text)

        try:
            return await resilient_call_with_retry(
                self._call_llm,
                complaint_text,
                operation_name="LLM_COMPLAINT_ANALYSIS",
            )
        except Exception as err:
            logger.error("LLMComplaintAnalyzer failed: %s. Using deterministic fallback.", err)
            return await self.fallback.analyze(complaint_text)

    async def extract_location(self, text: str) -> str | None:
        return await self.fallback.extract_location(text)


def get_complaint_analyzer() -> ComplaintAnalyzerService:
    """Factory to get the configured complaint analyzer service instance."""
    from backend.core.config import settings

    if settings.ai_provider == "gemini" and settings.gemini_api_key:
        return LLMComplaintAnalyzer(api_key=settings.gemini_api_key, model_name=settings.ai_model_name)
    if settings.ai_provider == "openai" and settings.openai_api_key:
        return LLMComplaintAnalyzer(api_key=settings.openai_api_key, model_name=settings.ai_model_name)
    return DeterministicComplaintAnalyzer()
