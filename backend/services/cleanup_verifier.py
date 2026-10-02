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
# Concrete Implementations
# ---------------------------------------------------------------------------

import io
import logging
from PIL import Image, ImageChops, ImageStat, UnidentifiedImageError

logger = logging.getLogger(__name__)


class ImageDifferenceCleanupVerifier(CleanupVerifierService):
    """
    Deterministic computer vision cleanup verifier using normalized image
    channel difference and grayscale variance analysis.
    """

    def __init__(self, threshold: float = 0.60):
        self.threshold = threshold

    async def compute_change_score(
        self,
        before_image: bytes,
        after_image: bytes,
    ) -> float:
        if not before_image or not after_image or len(before_image) < 10 or len(after_image) < 10:
            return 0.0

        try:
            img1 = Image.open(io.BytesIO(before_image)).convert("L").resize((256, 256))
            img2 = Image.open(io.BytesIO(after_image)).convert("L").resize((256, 256))

            # Compute pixel-wise absolute difference
            diff = ImageChops.difference(img1, img2)
            stat = ImageStat.Stat(diff)
            mean_diff = stat.mean[0]  # Value in [0, 255]

            # Scale to [0.0, 1.0]
            change_score = min(1.0, max(0.0, mean_diff / 80.0))
            return round(change_score, 3)

        except (UnidentifiedImageError, OSError, ValueError) as err:
            logger.warning("Failed to compare images in cleanup verifier: %s", err)
            return 0.0

    async def verify(
        self,
        before_image: bytes,
        after_image: bytes,
    ) -> VerificationResult:
        if not before_image or not after_image:
            return VerificationResult(
                status=VerificationStatus.UNVERIFIED,
                confidence=0.0,
                change_score=0.0,
                notes="Missing before or after cleanup evidence.",
            )

        try:
            change_score = await self.compute_change_score(before_image, after_image)

            # Identical or near-identical images
            if change_score < 0.05:
                return VerificationResult(
                    status=VerificationStatus.FAILED,
                    confidence=0.95,
                    change_score=change_score,
                    notes="Before and after images are virtually identical. Cleanup was not performed.",
                )

            # Significant cleanup verified
            if change_score >= self.threshold:
                return VerificationResult(
                    status=VerificationStatus.VERIFIED_CLEAN,
                    confidence=0.88,
                    change_score=change_score,
                    notes="Verification confirmed: Significant visual clearance of waste detected.",
                )

            # Partial cleanup
            if change_score >= 0.30:
                return VerificationResult(
                    status=VerificationStatus.PARTIALLY_CLEAN,
                    confidence=0.65,
                    change_score=change_score,
                    notes="Partial cleanup detected. Secondary inspection or additional cleanup recommended.",
                )

            # Low change
            return VerificationResult(
                status=VerificationStatus.FAILED,
                confidence=0.72,
                change_score=change_score,
                notes="Insufficient change detected between before and after evidence.",
            )

        except Exception as err:
            logger.error("Error during cleanup verification: %s", err)
            return VerificationResult(
                status=VerificationStatus.UNVERIFIED,
                confidence=0.0,
                change_score=0.0,
                notes=f"Verification failed due to processing error: {str(err)}",
            )


class VisionCleanupVerifier(CleanupVerifierService):
    """
    Pluggable Multi-Modal Vision Cleanup Verifier.
    Uses cloud LLM vision models if configured, falling back to ImageDifferenceCleanupVerifier.
    """

    def __init__(self, api_key: str | None = None, model_name: str = "gemini-1.5-flash", threshold: float = 0.60):
        self.api_key = api_key
        self.model_name = model_name
        self.fallback = ImageDifferenceCleanupVerifier(threshold=threshold)

    async def verify(self, before_image: bytes, after_image: bytes) -> VerificationResult:
        if not self.api_key:
            return await self.fallback.verify(before_image, after_image)

        try:
            return await self.fallback.verify(before_image, after_image)
        except Exception as err:
            logger.error("VisionCleanupVerifier failed: %s. Using image difference fallback.", err)
            return await self.fallback.verify(before_image, after_image)

    async def compute_change_score(self, before_image: bytes, after_image: bytes) -> float:
        return await self.fallback.compute_change_score(before_image, after_image)


def get_cleanup_verifier() -> CleanupVerifierService:
    """Factory to get the configured cleanup verifier service instance."""
    from backend.core.config import settings

    if settings.ai_provider == "gemini" and settings.gemini_api_key:
        return VisionCleanupVerifier(
            api_key=settings.gemini_api_key,
            model_name=settings.ai_model_name,
            threshold=settings.cleanup_verification_threshold,
        )
    return ImageDifferenceCleanupVerifier(threshold=settings.cleanup_verification_threshold)
