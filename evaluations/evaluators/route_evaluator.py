"""
SwachhLoop AI — Route Optimization & Constraint Evaluator
=========================================================
Evaluates route optimization outputs against operational constraints,
measures constraint violations, and computes distance savings against a naive baseline.
"""

import json
from pathlib import Path
from typing import Any

from backend.services.route_optimizer import (
    Location,
    get_route_optimizer,
    haversine_distance_km,
)
from backend.core.guardrails import validate_route_constraints
from evaluations.evaluators.base import BaseEvaluator
from evaluations.metrics import compute_route_evaluation_metrics


class RouteEvaluator(BaseEvaluator):
    def __init__(self, dataset_path: str = "evaluations/datasets/routes_eval.json"):
        self.dataset_path = Path(dataset_path)

    @property
    def name(self) -> str:
        return "Route Optimization & Constraint Evaluation"

    async def evaluate(self) -> dict[str, Any]:
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Evaluation dataset not found at {self.dataset_path}")

        with open(self.dataset_path, "r", encoding="utf-8") as f:
            cases = json.load(f)

        optimizer = get_route_optimizer()
        records: list[dict[str, Any]] = []

        for case in cases:
            locations = [
                Location(id=loc["id"], latitude=loc["latitude"], longitude=loc["longitude"], label=loc["label"])
                for loc in case["locations"]
            ]

            # Compute naive baseline distance (straight visiting order without TSP optimization)
            naive_distance = 0.0
            from backend.core.config import settings
            depot_lat, depot_lon = settings.default_depot_lat, settings.default_depot_lon
            curr_lat, curr_lon = depot_lat, depot_lon
            for loc in locations:
                naive_distance += haversine_distance_km(curr_lat, curr_lon, loc.latitude, loc.longitude)
                curr_lat, curr_lon = loc.latitude, loc.longitude

            opt_res = await optimizer.optimize(locations)

            # Validate constraints
            is_valid, violations = validate_route_constraints(
                opt_res,
                expected_stop_count=case["expected_stop_count"],
            )

            records.append({
                "id": case["id"],
                "name": case["name"],
                "has_violations": not is_valid,
                "violations": violations,
                "optimized_distance_km": opt_res.estimated_distance_km,
                "naive_distance_km": round(naive_distance, 2),
                "optimized_duration_min": opt_res.estimated_duration_min,
                "stops_count": len(opt_res.ordered_locations),
            })

        metrics = compute_route_evaluation_metrics(records)

        return {
            "suite_name": self.name,
            "dataset_type": "offline_synthetic_fixtures",
            "sample_count": len(cases),
            "metrics": metrics,
            "details": records,
        }
