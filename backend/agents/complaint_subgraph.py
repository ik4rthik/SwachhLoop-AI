"""
SwachhLoop AI — Complaint Processing Subgraph
=============================================
Specialized LangGraph workflow for complaint intake, computer vision waste
detection, NLP text analysis, validation, and priority assignment.
"""

from datetime import datetime, timezone
import logging
from langgraph.graph import StateGraph, START, END

from backend.agents.state import SwachhLoopState, ComplaintProcessingOutput
from backend.services.waste_detector import get_waste_detector
from backend.services.complaint_analyzer import get_complaint_analyzer

logger = logging.getLogger(__name__)


async def intake_node(state: SwachhLoopState) -> dict:
    """Intake node: analyze uploaded image if available."""
    audit = list(state.get("audit_trail") or [])
    image_bytes = state.get("image_bytes")
    detected_types = []
    confidence = 0.0

    if image_bytes and len(image_bytes) > 0:
        detector = get_waste_detector()
        detection = await detector.detect(image_bytes)
        if detection.detected:
            detected_types = detection.waste_types
            confidence = detection.confidence

    audit.append({
        "step_id": f"step_intake_{len(audit)+1}",
        "node_name": "intake_node",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "SUCCESS",
        "detail": f"Processed image input. Detected: {detected_types} (conf: {confidence})",
    })

    return {
        "current_node": "intake_node",
        "audit_trail": audit,
        "_detected_types": detected_types,
        "_image_confidence": confidence,
    }


async def analysis_node(state: SwachhLoopState) -> dict:
    """Analyze complaint text and extract semantics."""
    audit = list(state.get("audit_trail") or [])
    text = state.get("complaint_text") or ""
    analyzer = get_complaint_analyzer()

    analysis = await analyzer.analyze(text)

    audit.append({
        "step_id": f"step_analysis_{len(audit)+1}",
        "node_name": "analysis_node",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "SUCCESS",
        "detail": f"NLP analyzed complaint. Urgency: {analysis.urgency.value}, Location: {analysis.extracted_location}",
    })

    return {
        "current_node": "analysis_node",
        "audit_trail": audit,
        "_nlp_analysis": analysis,
    }


async def validate_node(state: SwachhLoopState) -> dict:
    """Validate, synthesize findings, and produce structured output."""
    audit = list(state.get("audit_trail") or [])
    nlp = state.get("_nlp_analysis")
    detected_types = state.get("_detected_types", [])
    img_conf = state.get("_image_confidence", 0.0)

    # Combine waste types
    combined_types = list(set((nlp.waste_types if nlp else []) + detected_types))
    urgency_val = nlp.urgency.value if nlp else "low"
    location_val = nlp.extracted_location if nlp else None
    action_val = nlp.suggested_action if nlp else "Inspect reported location."
    summary_val = nlp.summary if nlp else "Citizen submitted complaint."
    tags = list(nlp.tags if nlp else [])
    for dt in detected_types:
        if dt not in tags:
            tags.append(dt)

    # Check validity and ambiguity
    text = (state.get("complaint_text") or "").strip()
    is_ambiguous = False
    validation_status = "VALID"

    if len(text) < 5 and not detected_types:
        is_ambiguous = True
        validation_status = "INVALID"
        action_val = "Reject or request additional details: insufficient information provided."
    elif not location_val and not state.get("locations_data"):
        is_ambiguous = True
        validation_status = "AMBIGUOUS"

    overall_confidence = max(0.5, img_conf) if detected_types else 0.75
    requires_review = urgency_val == "critical" or validation_status != "VALID"
    review_reason = (
        "Critical urgency hazard reported — supervisor sign-off recommended."
        if urgency_val == "critical"
        else ("Ambiguous location / details." if is_ambiguous else None)
    )

    result = ComplaintProcessingOutput(
        category=combined_types[0] if combined_types else "general waste",
        urgency=urgency_val,
        extracted_location=location_val,
        suggested_action=action_val,
        summary=summary_val,
        tags=tags,
        confidence=overall_confidence,
        detected_waste_types=combined_types,
        is_ambiguous=is_ambiguous,
        validation_status=validation_status,
    )

    audit.append({
        "step_id": f"step_validate_{len(audit)+1}",
        "node_name": "validate_node",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "REVIEW_REQUIRED" if requires_review else "SUCCESS",
        "detail": f"Synthesized complaint output. Status: {validation_status}, Requires Review: {requires_review}",
    })

    return {
        "current_node": "validate_node",
        "complaint_result": result.model_dump(),
        "requires_human_review": requires_review,
        "review_reason": review_reason,
        "status": "NEEDS_REVIEW" if requires_review else "COMPLETED",
        "audit_trail": audit,
    }


def build_complaint_subgraph():
    """Build and compile the complaint processing StateGraph."""
    workflow = StateGraph(SwachhLoopState)
    workflow.add_node("intake", intake_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("validate", validate_node)

    workflow.add_edge(START, "intake")
    workflow.add_edge("intake", "analysis")
    workflow.add_edge("analysis", "validate")
    workflow.add_edge("validate", END)

    return workflow.compile()
