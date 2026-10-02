"""
SwachhLoop AI — Cleanup Verification & Escalation Subgraph
==========================================================
Specialized LangGraph workflow for before/after image verification,
quality auditing, and escalation decisioning for civic cleanup tasks.
"""

from datetime import datetime, timezone
import logging
from langgraph.graph import StateGraph, START, END

from backend.agents.state import SwachhLoopState, VerificationOutput
from backend.services.cleanup_verifier import get_cleanup_verifier, VerificationStatus

logger = logging.getLogger(__name__)


async def verify_evidence_node(state: SwachhLoopState) -> dict:
    """Verify cleanup by comparing before and after images."""
    audit = list(state.get("audit_trail") or [])
    before_bytes = state.get("before_image_bytes")
    after_bytes = state.get("after_image_bytes")

    verifier = get_cleanup_verifier()
    result = await verifier.verify(before_bytes, after_bytes)

    audit.append({
        "step_id": f"step_verify_ev_{len(audit)+1}",
        "node_name": "verify_evidence_node",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "SUCCESS",
        "detail": f"Verification status: {result.status.value}, change score: {result.change_score}, confidence: {result.confidence}",
    })

    return {
        "current_node": "verify_evidence_node",
        "_cv_verification_result": result,
        "audit_trail": audit,
    }


async def escalation_decision_node(state: SwachhLoopState) -> dict:
    """Apply civic business rules to determine approval, rejection, or escalation."""
    audit = list(state.get("audit_trail") or [])
    cv_res = state.get("_cv_verification_result")

    if not cv_res:
        out = VerificationOutput(
            status="unverified",
            confidence=0.0,
            change_score=0.0,
            decision="ESCALATE_MANUAL_REVIEW",
            notes="Missing verification inputs.",
            requires_inspection=True,
        )
        return {
            "current_node": "escalation_decision_node",
            "verification_result": out.model_dump(),
            "requires_human_review": True,
            "review_reason": "No verification data available.",
            "status": "NEEDS_REVIEW",
            "audit_trail": audit,
        }

    status = cv_res.status
    confidence = cv_res.confidence
    change_score = cv_res.change_score

    # Strict governance: Do not automatically mark uncertain results as verified
    if status == VerificationStatus.VERIFIED_CLEAN and confidence >= 0.80:
        decision = "APPROVED"
        requires_review = False
        requires_inspection = False
        notes = "Automated AI verification passed: waste cleared with high confidence."
        review_reason = None
    elif status == VerificationStatus.FAILED:
        decision = "REJECTED"
        requires_review = True
        requires_inspection = True
        notes = cv_res.notes or "Visual evidence indicates cleanup did not meet standards."
        review_reason = "Cleanup task rejected by AI verification. Escalated to municipal supervisor."
    else:  # PARTIALLY_CLEAN or UNVERIFIED or low confidence
        decision = "ESCALATE_MANUAL_REVIEW"
        requires_review = True
        requires_inspection = True
        notes = cv_res.notes or "Uncertain or partial cleanup detected. Manual inspection required."
        review_reason = "Confidence threshold not met. Field inspection required before closing complaint."

    output = VerificationOutput(
        status=status.value if hasattr(status, "value") else str(status),
        confidence=confidence,
        change_score=change_score,
        decision=decision,
        notes=notes,
        requires_inspection=requires_inspection,
    )

    audit.append({
        "step_id": f"step_escalate_dec_{len(audit)+1}",
        "node_name": "escalation_decision_node",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "REVIEW_REQUIRED" if requires_review else "SUCCESS",
        "detail": f"Decided verdict: {decision}. Requires review: {requires_review}",
    })

    return {
        "current_node": "escalation_decision_node",
        "verification_result": output.model_dump(),
        "requires_human_review": requires_review,
        "review_reason": review_reason,
        "status": "NEEDS_REVIEW" if requires_review else "COMPLETED",
        "audit_trail": audit,
    }


def build_verification_subgraph():
    """Build and compile the cleanup verification StateGraph."""
    workflow = StateGraph(SwachhLoopState)
    workflow.add_node("verify_evidence", verify_evidence_node)
    workflow.add_node("escalation_decision", escalation_decision_node)

    workflow.add_edge(START, "verify_evidence")
    workflow.add_edge("verify_evidence", "escalation_decision")
    workflow.add_edge("escalation_decision", END)

    return workflow.compile()
