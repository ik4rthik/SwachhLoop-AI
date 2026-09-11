"""
SwachhLoop AI — Cleanup Verifier Service Interface
===================================================
Defines the CONTRACT for the cleanup verification AI service.

Phase 1: Abstract interface only. No implementation.
Phase 4: Implement with computer vision image change detection.

This service will compare before/after images of a waste site
to verify whether cleanup was performed successfully.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


# ---------------------------------------------------------------------------
# Data Transfer Objects
# ---------------------------------------------------------------------------

class VerificationStatus(str, Enum):
    VERIFIED_CLEAN = "verified_clean"       # Cleanup confirmed
    PARTIALLY_CLEAN = "partially_clean"     # Partial cleanup detected
    UNVERIFIED = "unverified"               # Cannot determine (low confidence)
    FAILED = "failed"                       # Cleanup did not occur


@dataclass
class VerificationResult:
    """
    Result returned by CleanupVerifierService.verify().

    Attributes:
        status:          Outcome of the verification.
        confidence:      Model confidence in the verdict [0.0, 1.0].
        change_score:    Quantified visual change between before/after [0.0, 1.0].
        notes:           Human-readable explanation of the verdict.
    """
    status: VerificationStatus
    confidence: float
    change_score: float
    notes: str


# ---------------------------------------------------------------------------
# Service Interface (Abstract Base Class)
# ---------------------------------------------------------------------------

class CleanupVerifierService(ABC):
    """
    Interface for the cleanup verification AI service.
    """

    @abstractmethod
    async def verify(
        self,
        before_image: bytes,
        after_image: bytes,
    ) -> VerificationResult:
        """
        Compare before and after images to verify cleanup.

        Args:
            before_image: Raw image bytes taken before cleanup.
            after_image:  Raw image bytes taken after cleanup.

        Returns:
            VerificationResult with status and confidence score.

        Raises:
            NotImplementedError: Until Phase 4 implementation is provided.
        """
        raise NotImplementedError(
            "CleanupVerifierService.verify() is not yet implemented. "
            "Scheduled for Phase 4."
        )

    @abstractmethod
    async def compute_change_score(
        self,
        before_image: bytes,
        after_image: bytes,
    ) -> float:
        """
        Compute a scalar change score between two images.

        Args:
            before_image: Raw image bytes before cleanup.
            after_image:  Raw image bytes after cleanup.

        Returns:
            Float in [0.0, 1.0] where 1.0 indicates maximum visible change.

        Raises:
            NotImplementedError: Until Phase 4 implementation is provided.
        """
        raise NotImplementedError(
            "CleanupVerifierService.compute_change_score() is not yet implemented. "
            "Scheduled for Phase 4."
        )


# ---------------------------------------------------------------------------
# NOTE: Concrete implementation will be added in Phase 4 as:
#   class CVCleanupVerifier(CleanupVerifierService): ...
# ---------------------------------------------------------------------------
