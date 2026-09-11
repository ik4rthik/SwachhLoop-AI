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
# NOTE: Concrete implementation will be added in Phase 3 as:
#   class GeminiComplaintAnalyzer(ComplaintAnalyzerService): ...
# ---------------------------------------------------------------------------
