"""
SwachhLoop AI — LangGraph Multi-Agent State Definitions
======================================================
Defines typed, immutable schemas for the shared multi-agent state
used across the hierarchical orchestrator and specialized subgraphs.
"""

from typing import Any, Literal
from typing_extensions import TypedDict
from pydantic import BaseModel, Field


class AuditStep(BaseModel):
    """Traceable execution record for a graph node."""
    step_id: str
    node_name: str
    timestamp: str
    status: Literal["SUCCESS", "FAILED", "SKIPPED", "REVIEW_REQUIRED"]
    detail: str


class ComplaintProcessingOutput(BaseModel):
    """Output produced by the complaint processing subgraph."""
    category: str
    urgency: str
    extracted_location: str | None = None
    suggested_action: str
    summary: str
    tags: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    detected_waste_types: list[str] = Field(default_factory=list)
    is_ambiguous: bool = False
    validation_status: Literal["VALID", "AMBIGUOUS", "INVALID"] = "VALID"


class RouteOptimizationOutput(BaseModel):
    """Output produced by the collection and routing subgraph."""
    ordered_stops: list[dict[str, Any]] = Field(default_factory=list)
    total_distance_km: float = 0.0
    estimated_duration_min: float = 0.0
    polyline: str | None = None
    stop_count: int = 0
    route_status: Literal["OPTIMIZED", "DEGRADED", "FAILED"] = "OPTIMIZED"
    notes: str = ""


class VerificationOutput(BaseModel):
    """Output produced by the cleanup verification subgraph."""
    status: str
    confidence: float = 0.0
    change_score: float = 0.0
    decision: Literal["APPROVED", "REJECTED", "ESCALATE_MANUAL_REVIEW"]
    notes: str = ""
    requires_inspection: bool = False


class AwarenessOutput(BaseModel):
    """Output produced by the public awareness RAG subgraph."""
    query: str
    language: str
    answer: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    found: bool = False


class SwachhLoopState(TypedDict, total=False):
    """
    Shared typed state passed between the parent orchestrator
    and specialized subgraphs in LangGraph.
    """
    # Routing & Context
    workflow_id: str
    task_type: Literal[
        "PROCESS_COMPLAINT",
        "OPTIMIZE_ROUTE",
        "VERIFY_CLEANUP",
        "PUBLIC_AWARENESS",
        "UNKNOWN",
    ]
    current_node: str
    
    # Input payloads
    complaint_id: int | None
    complaint_text: str | None
    image_bytes: bytes | None
    before_image_bytes: bytes | None
    after_image_bytes: bytes | None
    locations_data: list[dict[str, Any]] | None
    query_text: str | None
    language: str | None
    
    # Subgraph outputs
    complaint_result: dict[str, Any] | None
    route_result: dict[str, Any] | None
    verification_result: dict[str, Any] | None
    awareness_result: dict[str, Any] | None

    # Working / intermediate state fields
    _detected_types: list[str] | None
    _image_confidence: float | None
    _nlp_analysis: Any | None
    _valid_locations: list[Any] | None
    _optimization_result: Any | None
    _cv_verification_result: Any | None
    _retrieved_articles: list[Any] | None
    
    # Control flags & Traceability
    requires_human_review: bool
    review_reason: str | None
    status: Literal["PENDING", "IN_PROGRESS", "COMPLETED", "ERROR", "NEEDS_REVIEW"]
    error_message: str | None
    audit_trail: list[dict[str, Any]]
