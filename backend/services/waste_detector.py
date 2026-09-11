"""
SwachhLoop AI — Waste Detector Service Interface
=================================================
Defines the CONTRACT for the computer vision waste detection service.

Phase 1: Abstract interface only. No implementation.
Phase 3: Implement with YOLO / custom CV model.

Downstream consumers (API routes, agents) should depend on the
WasteDetectorService ABC — not on any concrete implementation.
This ensures Phase 3 can swap in a real model without touching
any other layer.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Data Transfer Objects
# ---------------------------------------------------------------------------

@dataclass
class DetectionResult:
    """
    Result returned by WasteDetectorService.detect().

    Attributes:
        detected:       True if waste was found in the image.
        waste_types:    List of detected waste categories
                        (e.g. ["plastic", "organic"]).
        confidence:     Overall detection confidence score [0.0, 1.0].
        bounding_boxes: Raw bounding box data for detected objects
                        (format TBD in Phase 3).
    """
    detected: bool
    waste_types: list[str]
    confidence: float
    bounding_boxes: list[dict]


# ---------------------------------------------------------------------------
# Service Interface (Abstract Base Class)
# ---------------------------------------------------------------------------

class WasteDetectorService(ABC):
    """
    Interface for the waste detection AI service.

    All concrete implementations must inherit from this class and
    implement every abstract method.
    """

    @abstractmethod
    async def detect(self, image_bytes: bytes) -> DetectionResult:
        """
        Analyse an image and detect waste.

        Args:
            image_bytes: Raw image data (JPEG / PNG).

        Returns:
            DetectionResult with detected waste types and confidence scores.

        Raises:
            NotImplementedError: Until Phase 3 implementation is provided.
        """
        raise NotImplementedError(
            "WasteDetectorService.detect() is not yet implemented. "
            "Scheduled for Phase 3."
        )

    @abstractmethod
    async def classify(self, image_bytes: bytes) -> dict[str, float]:
        """
        Classify waste in an image into categories with confidence scores.

        Args:
            image_bytes: Raw image data.

        Returns:
            Dictionary mapping waste category → confidence score.
            Example: {"plastic": 0.87, "organic": 0.12}

        Raises:
            NotImplementedError: Until Phase 3 implementation is provided.
        """
        raise NotImplementedError(
            "WasteDetectorService.classify() is not yet implemented. "
            "Scheduled for Phase 3."
        )


# ---------------------------------------------------------------------------
# NOTE: Do NOT add fake implementations here.
# The concrete class will be added in Phase 3 as:
#   class YOLOWasteDetector(WasteDetectorService): ...
# ---------------------------------------------------------------------------
