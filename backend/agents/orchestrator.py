"""
SwachhLoop AI — Hierarchical Parent Multi-Agent Orchestrator
============================================================
Coordinates specialized subgraphs using LangGraph, maintains shared state,
enforces role and policy governance, and records traceable audit steps.
"""

from datetime import datetime, timezone
import logging
import uuid
from typing import Any

from langgraph.graph import StateGraph, START, END

from backend.agents.state import SwachhLoopState
from backend.agents.complaint_subgraph import build_complaint_subgraph
from backend.agents.logistics_subgraph import build_logistics_subgraph
from backend.agents.verification_subgraph import build_verification_subgraph
from backend.agents.awareness_subgraph import build_awareness_subgraph

logger = logging.getLogger(__name__)

# Compile subgraphs once for efficiency
_complaint_subgraph = build_complaint_subgraph()
_logistics_subgraph = build_logistics_subgraph()
_verification_subgraph = build_verification_subgraph()
_awareness_subgraph = build_awareness_subgraph()


async def router_node(state: SwachhLoopState) -> dict:
    """Entry node: initializes identifiers and validates task type."""
    workflow_id = state.get("workflow_id") or f"wf_{uuid.uuid4().hex[:10]}"
    audit = list(state.get("audit_trail") or [])

    task_type = state.get("task_type") or "UNKNOWN"
    audit.append({
        "step_id": f"step_router_{len(audit)+1}",
        "node_name": "router_node",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "SUCCESS",
        "detail": f"Workflow {workflow_id} routing task type: {task_type}",
    })

    return {
        "workflow_id": workflow_id,
        "current_node": "router_node",
        "status": "IN_PROGRESS",
        "audit_trail": audit,
    }


def route_decision(state: SwachhLoopState) -> str:
    """Conditional routing edge returning next node name."""
    task_type = state.get("task_type", "UNKNOWN")
    if task_type == "PROCESS_COMPLAINT":
        return "complaint_agent"
    elif task_type == "OPTIMIZE_ROUTE":
        return "logistics_agent"
    elif task_type == "VERIFY_CLEANUP":
        return "verification_agent"
    elif task_type == "PUBLIC_AWARENESS":
        return "awareness_agent"
    return "fallback_node"


async def complaint_agent_node(state: SwachhLoopState) -> dict:
    """Executes the complaint processing subgraph."""
    try:
        sub_result = await _complaint_subgraph.ainvoke(state)
        return {
            "current_node": "complaint_agent",
            "complaint_result": sub_result.get("complaint_result"),
            "requires_human_review": sub_result.get("requires_human_review", False),
            "review_reason": sub_result.get("review_reason"),
            "status": sub_result.get("status", "COMPLETED"),
            "audit_trail": sub_result.get("audit_trail", state.get("audit_trail", [])),
        }
    except Exception as err:
        logger.error("Complaint agent error: %s", err)
        return _handle_subgraph_error(state, "complaint_agent", err)


async def logistics_agent_node(state: SwachhLoopState) -> dict:
    """Executes the collection and route optimization subgraph."""
    try:
        sub_result = await _logistics_subgraph.ainvoke(state)
        return {
            "current_node": "logistics_agent",
            "route_result": sub_result.get("route_result"),
            "requires_human_review": sub_result.get("requires_human_review", False),
            "review_reason": sub_result.get("review_reason"),
            "status": sub_result.get("status", "COMPLETED"),
            "audit_trail": sub_result.get("audit_trail", state.get("audit_trail", [])),
        }
    except Exception as err:
        logger.error("Logistics agent error: %s", err)
        return _handle_subgraph_error(state, "logistics_agent", err)


async def verification_agent_node(state: SwachhLoopState) -> dict:
    """Executes the cleanup verification subgraph."""
    try:
        sub_result = await _verification_subgraph.ainvoke(state)
        return {
            "current_node": "verification_agent",
            "verification_result": sub_result.get("verification_result"),
            "requires_human_review": sub_result.get("requires_human_review", False),
            "review_reason": sub_result.get("review_reason"),
            "status": sub_result.get("status", "COMPLETED"),
            "audit_trail": sub_result.get("audit_trail", state.get("audit_trail", [])),
        }
    except Exception as err:
        logger.error("Verification agent error: %s", err)
        return _handle_subgraph_error(state, "verification_agent", err)


async def awareness_agent_node(state: SwachhLoopState) -> dict:
    """Executes the public awareness and RAG subgraph."""
    try:
        sub_result = await _awareness_subgraph.ainvoke(state)
        return {
            "current_node": "awareness_agent",
            "awareness_result": sub_result.get("awareness_result"),
            "requires_human_review": sub_result.get("requires_human_review", False),
            "review_reason": sub_result.get("review_reason"),
            "status": sub_result.get("status", "COMPLETED"),
            "audit_trail": sub_result.get("audit_trail", state.get("audit_trail", [])),
        }
    except Exception as err:
        logger.error("Awareness agent error: %s", err)
        return _handle_subgraph_error(state, "awareness_agent", err)


async def fallback_node(state: SwachhLoopState) -> dict:
    """Handles unsupported or missing task types safely."""
    audit = list(state.get("audit_trail") or [])
    task_type = state.get("task_type", "UNKNOWN")

    audit.append({
        "step_id": f"step_fallback_{len(audit)+1}",
        "node_name": "fallback_node",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "FAILED",
        "detail": f"Unsupported task type: {task_type}. No specialized agent available.",
    })

    return {
        "current_node": "fallback_node",
        "status": "ERROR",
        "error_message": f"Unsupported workflow task type: '{task_type}'",
        "requires_human_review": True,
        "review_reason": f"Workflow failed due to unsupported task: {task_type}",
        "audit_trail": audit,
    }


async def governance_node(state: SwachhLoopState) -> dict:
    """
    Final governance & policy check:
    Ensures irreversible actions are flagged for supervisor review when confidence is low.
    """
    audit = list(state.get("audit_trail") or [])
    requires_review = state.get("requires_human_review", False)
    status = state.get("status", "COMPLETED")

    if status == "ERROR":
        final_status = "ERROR"
    elif requires_review:
        final_status = "NEEDS_REVIEW"
    else:
        final_status = status if status != "IN_PROGRESS" else "COMPLETED"

    audit.append({
        "step_id": f"step_gov_{len(audit)+1}",
        "node_name": "governance_node",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "REVIEW_REQUIRED" if requires_review else "SUCCESS",
        "detail": f"Governance check passed. Final Status: {final_status}. Review Required: {requires_review}",
    })

    return {
        "current_node": "governance_node",
        "status": final_status,
        "audit_trail": audit,
    }


def _handle_subgraph_error(state: SwachhLoopState, node_name: str, err: Exception) -> dict:
    audit = list(state.get("audit_trail") or [])
    audit.append({
        "step_id": f"step_err_{len(audit)+1}",
        "node_name": node_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "FAILED",
        "detail": f"Subagent error: {str(err)}",
    })
    return {
        "current_node": node_name,
        "status": "ERROR",
        "error_message": str(err),
        "requires_human_review": True,
        "review_reason": f"Agent {node_name} encountered an error: {str(err)}",
        "audit_trail": audit,
    }


def build_parent_orchestrator():
    """Build and compile the parent hierarchical multi-agent orchestrator StateGraph."""
    parent = StateGraph(SwachhLoopState)

    parent.add_node("router", router_node)
    parent.add_node("complaint_agent", complaint_agent_node)
    parent.add_node("logistics_agent", logistics_agent_node)
    parent.add_node("verification_agent", verification_agent_node)
    parent.add_node("awareness_agent", awareness_agent_node)
    parent.add_node("fallback_node", fallback_node)
    parent.add_node("governance", governance_node)

    parent.add_edge(START, "router")

    parent.add_conditional_edges(
        "router",
        route_decision,
        {
            "complaint_agent": "complaint_agent",
            "logistics_agent": "logistics_agent",
            "verification_agent": "verification_agent",
            "awareness_agent": "awareness_agent",
            "fallback_node": "fallback_node",
        },
    )

    parent.add_edge("complaint_agent", "governance")
    parent.add_edge("logistics_agent", "governance")
    parent.add_edge("verification_agent", "governance")
    parent.add_edge("awareness_agent", "governance")
    parent.add_edge("fallback_node", "governance")

    parent.add_edge("governance", END)

    return parent.compile()


# Compiled singleton orchestrator instance
orchestrator_graph = build_parent_orchestrator()


async def run_swachhloop_workflow(task_type: str, **kwargs: Any) -> SwachhLoopState:
    """
    Public entry point to execute the multi-agent workflow.
    
    Args:
        task_type: Task type (e.g., PROCESS_COMPLAINT, OPTIMIZE_ROUTE, VERIFY_CLEANUP, PUBLIC_AWARENESS)
        **kwargs: Input arguments matching SwachhLoopState fields.
        
    Returns:
        Final SwachhLoopState containing results, audit trail, and governance status.
    """
    initial_state: SwachhLoopState = {
        "workflow_id": kwargs.get("workflow_id") or f"wf_{uuid.uuid4().hex[:10]}",
        "task_type": task_type,  # type: ignore
        "current_node": "INIT",
        "complaint_id": kwargs.get("complaint_id"),
        "complaint_text": kwargs.get("complaint_text"),
        "image_bytes": kwargs.get("image_bytes"),
        "before_image_bytes": kwargs.get("before_image_bytes"),
        "after_image_bytes": kwargs.get("after_image_bytes"),
        "locations_data": kwargs.get("locations_data"),
        "query_text": kwargs.get("query_text"),
        "language": kwargs.get("language"),
        "complaint_result": None,
        "route_result": None,
        "verification_result": None,
        "awareness_result": None,
        "requires_human_review": False,
        "review_reason": None,
        "status": "PENDING",
        "error_message": None,
        "audit_trail": [],
    }

    result = await orchestrator_graph.ainvoke(initial_state)
    return result
