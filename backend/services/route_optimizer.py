"""
SwachhLoop AI — Route Optimizer Service Interface
==================================================
Defines the CONTRACT for the cleanup route optimization service.

Phase 1: Abstract interface only. No implementation.
Phase 4: Implement with OR-Tools / NetworkX + OpenStreetMap data.

This service will take a list of waste complaint locations and produce
an optimized visiting order that minimizes travel time/distance for
the assigned cleaner.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Data Transfer Objects
# ---------------------------------------------------------------------------

@dataclass
class Location:
    """
    A geographic point to be visited.

    Attributes:
        id:        Unique identifier (e.g., complaint_id or address string).
        latitude:  Decimal latitude.
        longitude: Decimal longitude.
        label:     Human-readable label for display.
    """
    id: str
    latitude: float
    longitude: float
    label: str = ""


@dataclass
class OptimizationResult:
    """
    Result returned by RouteOptimizerService.optimize().

    Attributes:
        ordered_locations:    Locations in optimized visiting order.
        estimated_distance_km: Total estimated route distance.
        estimated_duration_min: Total estimated travel time in minutes.
        route_polyline:       Encoded polyline for map display (Phase 4).
    """
    ordered_locations: list[Location]
    estimated_distance_km: float
    estimated_duration_min: float
    route_polyline: str | None = None


# ---------------------------------------------------------------------------
# Service Interface (Abstract Base Class)
# ---------------------------------------------------------------------------

class RouteOptimizerService(ABC):
    """
    Interface for the cleanup route optimization service.
    """

    @abstractmethod
    async def optimize(
        self,
        locations: list[Location],
        start_location: Location | None = None,
    ) -> OptimizationResult:
        """
        Compute an optimized visiting order for a set of locations.

        Args:
            locations:      List of waste locations to visit.
            start_location: Optional depot/start point for the cleaner.

        Returns:
            OptimizationResult with ordered locations and distance/time estimates.

        Raises:
            NotImplementedError: Until Phase 4 implementation is provided.
        """
        raise NotImplementedError(
            "RouteOptimizerService.optimize() is not yet implemented. "
            "Scheduled for Phase 4."
        )

    @abstractmethod
    async def estimate_travel_time(
        self,
        origin: Location,
        destination: Location,
    ) -> float:
        """
        Estimate travel time between two points in minutes.

        Args:
            origin:      Starting point.
            destination: End point.

        Returns:
            Estimated travel time in minutes.

        Raises:
            NotImplementedError: Until Phase 4 implementation is provided.
        """
        raise NotImplementedError(
            "RouteOptimizerService.estimate_travel_time() is not yet implemented. "
            "Scheduled for Phase 4."
        )


# ---------------------------------------------------------------------------
# NOTE: Concrete implementation will be added in Phase 4 as:
#   class ORToolsRouteOptimizer(RouteOptimizerService): ...
# ---------------------------------------------------------------------------
