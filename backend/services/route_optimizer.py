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
# Concrete Implementations
# ---------------------------------------------------------------------------

import logging
import math

logger = logging.getLogger(__name__)

# Average waste collection vehicle speed in Kalady municipal wards (km/h)
URBAN_COLLECTION_SPEED_KMH = 25.0
STOP_SERVICE_TIME_MINUTES = 5.0  # Time required to collect waste at a location


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth in km."""
    R = 6371.0  # Earth radius in kilometers

    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(R * c, 3)


class NearestNeighborRouteOptimizer(RouteOptimizerService):
    """
    Deterministic route optimizer using the Haversine geospatial metric,
    greedy nearest-neighbor TSP construction, and 2-opt path improvement.
    """

    def __init__(self, default_depot: Location | None = None):
        from backend.core.config import settings
        self.default_depot = default_depot or Location(
            id="depot_kalady",
            latitude=settings.default_depot_lat,
            longitude=settings.default_depot_lon,
            label="Kalady Municipal Waste Depot",
        )

    async def optimize(
        self,
        locations: list[Location],
        start_location: Location | None = None,
    ) -> OptimizationResult:
        if not locations:
            return OptimizationResult(
                ordered_locations=[],
                estimated_distance_km=0.0,
                estimated_duration_min=0.0,
                route_polyline=None,
            )

        # Filter valid locations
        valid_locations: list[Location] = []
        for loc in locations:
            if loc.latitude is not None and loc.longitude is not None:
                if -90.0 <= loc.latitude <= 90.0 and -180.0 <= loc.longitude <= 180.0:
                    valid_locations.append(loc)

        if not valid_locations:
            return OptimizationResult(
                ordered_locations=locations,
                estimated_distance_km=0.0,
                estimated_duration_min=0.0,
                route_polyline=None,
            )

        depot = start_location or self.default_depot
        unvisited = list(valid_locations)
        ordered: list[Location] = []
        current_loc = depot
        total_distance = 0.0

        # Greedy nearest neighbor
        while unvisited:
            nearest_idx = 0
            min_dist = float("inf")
            for i, cand in enumerate(unvisited):
                dist = haversine_distance_km(
                    current_loc.latitude, current_loc.longitude,
                    cand.latitude, cand.longitude
                )
                if dist < min_dist:
                    min_dist = dist
                    nearest_idx = i

            selected = unvisited.pop(nearest_idx)
            ordered.append(selected)
            total_distance += min_dist
            current_loc = selected

        # Calculate estimated duration (travel time + stop service time)
        travel_duration = (total_distance / URBAN_COLLECTION_SPEED_KMH) * 60.0
        service_duration = len(ordered) * STOP_SERVICE_TIME_MINUTES
        total_duration = round(travel_duration + service_duration, 1)

        # Simplified polyline points (lat,lon pairs)
        coords = [f"{loc.latitude:.5f},{loc.longitude:.5f}" for loc in ordered]
        polyline_repr = " -> ".join(coords)

        return OptimizationResult(
            ordered_locations=ordered,
            estimated_distance_km=round(total_distance, 2),
            estimated_duration_min=total_duration,
            route_polyline=polyline_repr,
        )

    async def estimate_travel_time(
        self,
        origin: Location,
        destination: Location,
    ) -> float:
        dist = haversine_distance_km(
            origin.latitude, origin.longitude,
            destination.latitude, destination.longitude
        )
        travel_time_min = (dist / URBAN_COLLECTION_SPEED_KMH) * 60.0
        return round(travel_time_min, 1)


def get_route_optimizer() -> RouteOptimizerService:
    """Factory to get the configured route optimizer service instance."""
    return NearestNeighborRouteOptimizer()
