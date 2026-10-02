"""
SwachhLoop AI — AI & Multi-Agent Schemas
========================================
Pydantic v2 validation models for AI service requests, predictions,
route optimization, verification, and multi-agent workflows.
"""

from typing import Any, Literal
from pydantic import BaseModel, Field


class DetectionBox(BaseModel):
    label: str
    box_2d: list[int] = Field(default_factory=list)
    confidence: float


class DetectionResponse(BaseModel):
    detected: bool
    waste_types: list[str] = Field(default_factory=list)
    confidence: float
    bounding_boxes: list[DetectionBox] = Field(default_factory=list)


class AnalyzeComplaintRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000, description="Complaint text submitted by citizen")
    image_url: str | None = None


class ComplaintAnalysisResponse(BaseModel):
    urgency: str
    extracted_location: str | None = None
    waste_types: list[str] = Field(default_factory=list)
    suggested_action: str
    summary: str
    tags: list[str] = Field(default_factory=list)


class LocationSchema(BaseModel):
    id: str
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    label: str = ""


class OptimizeRouteRequest(BaseModel):
    locations: list[LocationSchema] = Field(..., min_length=1)
    start_location: LocationSchema | None = None


class OptimizeRouteResponse(BaseModel):
    ordered_locations: list[LocationSchema] = Field(default_factory=list)
    estimated_distance_km: float
    estimated_duration_min: float
    route_polyline: str | None = None


class VerificationResponse(BaseModel):
    status: str
    confidence: float
    change_score: float
    notes: str


class AwarenessRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000)
    language: Literal["en", "ml"] | None = None


class AwarenessArticleSource(BaseModel):
    id: str
    title: str
    topic: str
    relevance: float = 0.0


class AwarenessResponse(BaseModel):
    query: str
    language: str
    answer: str
    source_articles: list[AwarenessArticleSource] = Field(default_factory=list)
    found_knowledge: bool
    notes: str = ""


class WorkflowRunRequest(BaseModel):
    task_type: Literal[
        "PROCESS_COMPLAINT",
        "OPTIMIZE_ROUTE",
        "VERIFY_CLEANUP",
        "PUBLIC_AWARENESS",
    ]
    complaint_id: int | None = None
    complaint_text: str | None = None
    locations_data: list[dict[str, Any]] | None = None
    query_text: str | None = None
    language: Literal["en", "ml"] | None = None


class WorkflowRunResponse(BaseModel):
    workflow_id: str
    task_type: str
    status: str
    requires_human_review: bool
    review_reason: str | None = None
    results: dict[str, Any] = Field(default_factory=dict)
    audit_trail: list[dict[str, Any]] = Field(default_factory=list)
