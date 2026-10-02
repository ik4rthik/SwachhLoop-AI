"""
SwachhLoop AI — AI & Multi-Agent API Routes
===========================================
Exposes AI services and LangGraph workflows to authorized clients:
  - POST /api/ai/detect-waste      (Waste detection from image)
  - POST /api/ai/analyze-complaint (Complaint NLP analysis)
  - POST /api/ai/optimize-route    (Route optimization)
  - POST /api/ai/verify-cleanup    (Before/after image verification)
  - POST /api/ai/awareness         (Bilingual RAG public awareness)
  - POST /api/ai/workflow/run      (Multi-agent orchestrator execution)
"""

import logging
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user, require_staff_or_admin, get_db
from backend.models.user import User
from backend.services.waste_detector import get_waste_detector
from backend.services.complaint_analyzer import get_complaint_analyzer
from backend.services.route_optimizer import get_route_optimizer, Location
from backend.services.cleanup_verifier import get_cleanup_verifier
from backend.services.knowledge_service import get_knowledge_service
from backend.services.audit_service import AuditService
from backend.agents.orchestrator import run_swachhloop_workflow
from backend.schemas.ai import (
    DetectionResponse,
    AnalyzeComplaintRequest,
    ComplaintAnalysisResponse,
    OptimizeRouteRequest,
    OptimizeRouteResponse,
    LocationSchema,
    VerificationResponse,
    AwarenessRequest,
    AwarenessResponse,
    WorkflowRunRequest,
    WorkflowRunResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["AI & Agents"])


@router.post("/detect-waste", response_model=DetectionResponse, summary="Detect waste categories in an image")
async def detect_waste(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Analyze uploaded photo to detect waste presence, categories, and confidence score."""
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File provided must be an image (JPEG, PNG, WebP).",
        )

    image_bytes = await image.read()
    if len(image_bytes) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded image file is empty.",
        )

    detector = get_waste_detector()
    result = await detector.detect(image_bytes)

    await AuditService.log(
        db=db,
        actor_id=current_user.id,
        action="AI_DETECT_WASTE",
        resource_type="image",
        detail=f"Detected waste: {result.detected}, types: {result.waste_types}, confidence: {result.confidence}",
    )

    return DetectionResponse(
        detected=result.detected,
        waste_types=result.waste_types,
        confidence=result.confidence,
        bounding_boxes=result.bounding_boxes,  # type: ignore
    )


@router.post("/analyze-complaint", response_model=ComplaintAnalysisResponse, summary="Analyze complaint text with NLP")
async def analyze_complaint(
    payload: AnalyzeComplaintRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Extract urgency, location, waste category, and action suggestions from text."""
    analyzer = get_complaint_analyzer()
    analysis = await analyzer.analyze(payload.text)

    await AuditService.log(
        db=db,
        actor_id=current_user.id,
        action="AI_ANALYZE_COMPLAINT",
        resource_type="complaint_text",
        detail=f"Assessed urgency: {analysis.urgency.value}, location: {analysis.extracted_location}",
    )

    return ComplaintAnalysisResponse(
        urgency=analysis.urgency.value,
        extracted_location=analysis.extracted_location,
        waste_types=analysis.waste_types,
        suggested_action=analysis.suggested_action,
        summary=analysis.summary,
        tags=analysis.tags,
    )


@router.post("/optimize-route", response_model=OptimizeRouteResponse, summary="Optimize waste collection route")
async def optimize_route(
    payload: OptimizeRouteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Compute optimal visiting sequence for waste collection points using geospatial TSP.
    Available to cleaners, municipal staff, and administrators.
    """
    if current_user.role not in ["cleaner", "municipal_staff", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Route optimization is reserved for cleaners and municipal supervisors.",
        )

    loc_models = [
        Location(id=loc.id, latitude=loc.latitude, longitude=loc.longitude, label=loc.label)
        for loc in payload.locations
    ]
    start_model = (
        Location(
            id=payload.start_location.id,
            latitude=payload.start_location.latitude,
            longitude=payload.start_location.longitude,
            label=payload.start_location.label,
        )
        if payload.start_location
        else None
    )

    optimizer = get_route_optimizer()
    opt_res = await optimizer.optimize(loc_models, start_location=start_model)

    ordered_schemas = [
        LocationSchema(id=l.id, latitude=l.latitude, longitude=l.longitude, label=l.label)
        for l in opt_res.ordered_locations
    ]

    await AuditService.log(
        db=db,
        actor_id=current_user.id,
        action="AI_OPTIMIZE_ROUTE",
        resource_type="route",
        detail=f"Optimized route with {len(ordered_schemas)} stops ({opt_res.estimated_distance_km} km)",
    )

    return OptimizeRouteResponse(
        ordered_locations=ordered_schemas,
        estimated_distance_km=opt_res.estimated_distance_km,
        estimated_duration_min=opt_res.estimated_duration_min,
        route_polyline=opt_res.route_polyline,
    )


@router.post("/verify-cleanup", response_model=VerificationResponse, summary="Verify cleanup with before/after photos")
async def verify_cleanup(
    before_image: UploadFile = File(...),
    after_image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Compare before and after cleanup evidence to verify that waste was cleared.
    Reserved for cleaners, staff, and admins.
    """
    if current_user.role not in ["cleaner", "municipal_staff", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verification is reserved for field workers and municipal staff.",
        )

    before_bytes = await before_image.read()
    after_bytes = await after_image.read()

    verifier = get_cleanup_verifier()
    result = await verifier.verify(before_bytes, after_bytes)

    await AuditService.log(
        db=db,
        actor_id=current_user.id,
        action="AI_VERIFY_CLEANUP",
        resource_type="evidence",
        detail=f"Verification status: {result.status.value}, change score: {result.change_score}, confidence: {result.confidence}",
    )

    return VerificationResponse(
        status=result.status.value if hasattr(result.status, "value") else str(result.status),
        confidence=result.confidence,
        change_score=result.change_score,
        notes=result.notes,
    )


@router.post("/awareness", response_model=AwarenessResponse, summary="Civic knowledge RAG query (English & Malayalam)")
async def awareness_rag(
    payload: AwarenessRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve grounded civic waste management guidance for Kalady Grama Panchayat.
    Supports English and Malayalam queries.
    """
    service = get_knowledge_service()
    resp = await service.answer_query(payload.query, language=payload.language)

    sources = [
        {
            "id": s["id"],
            "title": s["title"],
            "topic": s["topic"],
            "relevance": s.get("relevance", 0.0),
        }
        for s in resp.source_articles
    ]

    return AwarenessResponse(
        query=resp.query,
        language=resp.language,
        answer=resp.answer,
        source_articles=sources,  # type: ignore
        found_knowledge=resp.found_knowledge,
        notes=resp.notes,
    )


@router.post("/workflow/run", response_model=WorkflowRunResponse, summary="Run LangGraph multi-agent workflow")
async def run_workflow(
    payload: WorkflowRunRequest,
    current_user: User = Depends(require_staff_or_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute hierarchical LangGraph multi-agent orchestration for a given task type.
    Reserved for municipal staff and administrators.
    """
    final_state = await run_swachhloop_workflow(
        task_type=payload.task_type,
        complaint_id=payload.complaint_id,
        complaint_text=payload.complaint_text,
        locations_data=payload.locations_data,
        query_text=payload.query_text,
        language=payload.language,
    )

    # Collect results based on task type
    results: dict[str, Any] = {}
    if payload.task_type == "PROCESS_COMPLAINT":
        results = final_state.get("complaint_result") or {}
    elif payload.task_type == "OPTIMIZE_ROUTE":
        results = final_state.get("route_result") or {}
    elif payload.task_type == "VERIFY_CLEANUP":
        results = final_state.get("verification_result") or {}
    elif payload.task_type == "PUBLIC_AWARENESS":
        results = final_state.get("awareness_result") or {}

    await AuditService.log(
        db=db,
        actor_id=current_user.id,
        action="AI_WORKFLOW_RUN",
        resource_type="workflow",
        detail=f"Executed workflow {final_state.get('workflow_id')} ({payload.task_type}): Status={final_state.get('status')}",
    )

    return WorkflowRunResponse(
        workflow_id=final_state.get("workflow_id", "unknown"),
        task_type=payload.task_type,
        status=final_state.get("status", "COMPLETED"),
        requires_human_review=final_state.get("requires_human_review", False),
        review_reason=final_state.get("review_reason"),
        results=results,
        audit_trail=final_state.get("audit_trail", []),
    )
