"""
SwachhLoop AI — Base Evaluator Interface
=========================================
Defines the standard contract for service and workflow evaluators.
"""

from abc import ABC, abstractmethod
from typing import Any


class BaseEvaluator(ABC):
    """Abstract base class for all AI service and workflow evaluators."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the evaluation suite."""
        raise NotImplementedError

    @abstractmethod
    async def evaluate(self) -> dict[str, Any]:
        """
        Execute offline evaluation against deterministic fixtures/dataset.
        Returns a dictionary containing sample count, metrics, and details.
        """
        raise NotImplementedError
