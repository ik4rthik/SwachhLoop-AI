"""
SwachhLoop AI — Collection & Route Optimization Subgraph
========================================================
Specialized LangGraph workflow for receiving civic waste tasks, sorting
by urgency and location, computing optimal collection paths, and validating feasibility.
"""

from datetime import datetime, timezone
import logging
from langgraph.graph import StateGraph, START, END

from backend.agents.state import SwachhLoopState, RouteOptimizationOutput
from backend.services.route_optimizer import Location, get_route_optimizer

logger = logging.getLogger(__name__)


async def prepare_tasks_node(state: SwachhLoopState) -> dict:
    """Validate input locations and convert to Location domain models."""
    audit = list(state.get("audit_trail") or [])
    raw_locations = state.get("locations_data") or []

    valid_models: list[Location] = []
    for item in raw_locations:
        try:
            loc_id = str(item.get("id") or item.get("complaint_id") or f"loc_{len(valid_models)+1}")
            lat = float(item["latitude"])
            lon = float(item["longitude"])
            label = str(item.get("label") or item.get("location_label") or f"Stop {len(valid_models)+1}")
            valid_models.append(Location(id=loc_id, latitude=lat, longitude=lon, label=label))
        except (KeyError, TypeError, ValueError) as err:
            logger.warning("Skipping malformed location in logistics subgraph: %s (%s)", item, err)

    audit.append({
        "step_id": f"step_prep_logistics_{len(audit)+1}",
        "node_name": "prepare_tasks_node",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "SUCCESS",
        "detail": f"Parsed {len(valid_models)} of {len(raw_locations)} collection points.",
    })

    return {
        "current_node": "prepare_tasks_node",
        "_valid_locations": valid_models,
        "audit_trail": audit,
    }


async def optimize_node(state: SwachhLoopState) -> dict:
    """Compute the optimal visiting route using the Route Optimizer service."""
    audit = list(state.get("audit_trail") or [])
    locations: list[Location] = state.get("_valid_locations") or []

    optimizer = get_route_optimizer()
    opt_result = await optimizer.optimize(locations)

    audit.append({
        "step_id": f"step_opt_route_{len(audit)+1}",
        "node_name": "optimize_node",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "SUCCESS",
        "detail": f"Optimized route: {opt_result.estimated_distance_km} km, {opt_result.estimated_duration_min} min.",
    })

    return {
        "current_node": "optimize_node",
        "_optimization_result": opt_result,
        "audit_trail": audit,
    }


async def evaluate_feasibility_node(state: SwachhLoopState) -> dict:
    """Evaluate operational feasibility and determine if human supervisor sign-off is required."""
    audit = list(state.get("audit_trail") or [])
    opt = state.get("_optimization_result")

    if not opt or not opt.ordered_locations:
        res = RouteOptimizationOutput(
            ordered_stops=[],
            total_distance_km=0.0,
            estimated_duration_min=0.0,
            polyline=None,
            stop_count=0,
            route_status="FAILED",
            notes="No valid stops available for route computation.",
        )
        return {
            "current_node": "evaluate_feasibility_node",
            "route_result": res.model_dump(),
            "requires_human_review": False,
            "status": "COMPLETED",
            "audit_trail": audit,
        }

    # Flag for supervisor review if distance > 40 km or duration > 360 min (6 hours)
    requires_review = opt.estimated_distance_km > 40.0 or opt.estimated_duration_min > 360.0
    review_reason = (
        "Route exceeds typical single-shift capacity (>40km or >6hrs). Supervisor re-assignment recommended."
        if requires_review
        else None
    )

    ordered_dict = [
        {
            "sequence": idx + 1,
            "id": loc.id,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "label": loc.label,
        }
        for idx, loc in enumerate(opt.ordered_locations)
    ]

    output = RouteOptimizationOutput(
        ordered_stops=ordered_dict,
        total_distance_km=opt.estimated_distance_km,
        estimated_duration_min=opt.estimated_duration_min,
        polyline=opt.route_polyline,
        stop_count=len(ordered_dict),
        route_status="DEGRADED" if requires_review else "OPTIMIZED",
        notes=review_reason or "Feasible route generated.",
    )

    audit.append({
        "step_id": f"step_eval_feasibility_{len(audit)+1}",
        "node_name": "evaluate_feasibility_node",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "REVIEW_REQUIRED" if requires_review else "SUCCESS",
        "detail": f"Feasibility check finished. Review required: {requires_review}",
    })

    return {
        "current_node": "evaluate_feasibility_node",
        "route_result": output.model_dump(),
        "requires_human_review": requires_review,
        "review_reason": review_reason,
        "status": "NEEDS_REVIEW" if requires_review else "COMPLETED",
        "audit_trail": audit,
    }


def build_logistics_subgraph():
    """Build and compile the collection & route optimization StateGraph."""
    workflow = StateGraph(SwachhLoopState)
    workflow.add_node("prepare_tasks", prepare_tasks_node)
    workflow.add_node("optimize_route", optimize_node)
    workflow.add_node("evaluate_feasibility", evaluate_feasibility_node)

    workflow.add_edge(START, "prepare_tasks")
    workflow.add_edge("prepare_tasks", "optimize_route")
    workflow.add_edge("optimize_route", "evaluate_feasibility")
    workflow.add_edge("evaluate_feasibility", END)

    return workflow.compile()
