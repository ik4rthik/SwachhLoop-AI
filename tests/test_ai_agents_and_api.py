"""
SwachhLoop AI — Phase 4 LangGraph Multi-Agent Workflows & API Tests
===================================================================
Tests for:
  - Complaint Processing Subgraph
  - Collection & Route Optimization Subgraph
  - Cleanup Verification & Escalation Subgraph
  - Public Awareness RAG Subgraph
  - Parent Hierarchical Multi-Agent Orchestrator
  - FastAPI /api/ai/ route endpoints with RBAC & validation
"""

import io
import pytest
from httpx import AsyncClient
from PIL import Image

from backend.agents.orchestrator import run_swachhloop_workflow
from backend.agents.complaint_subgraph import build_complaint_subgraph
from backend.agents.logistics_subgraph import build_logistics_subgraph
from backend.agents.verification_subgraph import build_verification_subgraph
from backend.agents.awareness_subgraph import build_awareness_subgraph


def create_test_image_bytes(color: tuple = (100, 150, 200), size: tuple = (100, 100)) -> bytes:
    buf = io.BytesIO()
    img = Image.new("RGB", size, color=color)
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ===========================================================================
# 1. LangGraph Subgraph Direct Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_complaint_subgraph_execution():
    graph = build_complaint_subgraph()
    state = {
        "complaint_text": "Hospital toxic biohazard waste near Kalady Junction",
        "image_bytes": create_test_image_bytes(),
        "audit_trail": [],
    }
    result = await graph.ainvoke(state)

    assert result["complaint_result"] is not None
    assert result["complaint_result"]["urgency"] == "critical"
    assert result["requires_human_review"] is True
    assert len(result["audit_trail"]) >= 3


@pytest.mark.asyncio
async def test_logistics_subgraph_execution():
    graph = build_logistics_subgraph()
    locs = [
        {"id": "stop1", "latitude": 10.1667, "longitude": 76.4333, "label": "Kalady Center"},
        {"id": "stop2", "latitude": 10.1800, "longitude": 76.4250, "label": "Mattoor"},
    ]
    state = {
        "locations_data": locs,
        "audit_trail": [],
    }
    result = await graph.ainvoke(state)

    assert result["route_result"] is not None
    assert result["route_result"]["stop_count"] == 2
    assert result["route_result"]["route_status"] == "OPTIMIZED"


@pytest.mark.asyncio
async def test_verification_subgraph_clean_approval():
    graph = build_verification_subgraph()
    state = {
        "before_image_bytes": create_test_image_bytes(color=(10, 10, 10)),
        "after_image_bytes": create_test_image_bytes(color=(240, 240, 240)),
        "audit_trail": [],
    }
    result = await graph.ainvoke(state)

    assert result["verification_result"] is not None
    assert result["verification_result"]["decision"] == "APPROVED"
    assert result["requires_human_review"] is False


@pytest.mark.asyncio
async def test_verification_subgraph_failed_rejection():
    graph = build_verification_subgraph()
    # Identical images
    img = create_test_image_bytes(color=(100, 100, 100))
    state = {
        "before_image_bytes": img,
        "after_image_bytes": img,
        "audit_trail": [],
    }
    result = await graph.ainvoke(state)

    assert result["verification_result"]["decision"] == "REJECTED"
    assert result["requires_human_review"] is True


@pytest.mark.asyncio
async def test_awareness_subgraph_execution():
    graph = build_awareness_subgraph()
    state = {
        "query_text": "What are the rules for plastic ban and penalties?",
        "language": "en",
        "audit_trail": [],
    }
    result = await graph.ainvoke(state)

    assert result["awareness_result"] is not None
    assert result["awareness_result"]["found"] is True
    assert "plastic" in result["awareness_result"]["answer"].lower()


# ===========================================================================
# 2. Parent Orchestrator Graph Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_orchestrator_routing_complaint():
    res = await run_swachhloop_workflow(
        "PROCESS_COMPLAINT",
        complaint_text="Overflowing garbage heap near Mattoor market",
    )
    assert res["status"] in ["COMPLETED", "NEEDS_REVIEW"]
    assert res["complaint_result"] is not None
    assert "Mattoor" in str(res["complaint_result"]["extracted_location"])


@pytest.mark.asyncio
async def test_orchestrator_routing_route():
    locs = [
        {"id": "loc1", "latitude": 10.1667, "longitude": 76.4333, "label": "Point A"},
        {"id": "loc2", "latitude": 10.1700, "longitude": 76.4350, "label": "Point B"},
    ]
    res = await run_swachhloop_workflow("OPTIMIZE_ROUTE", locations_data=locs)
    assert res["status"] == "COMPLETED"
    assert res["route_result"]["stop_count"] == 2


@pytest.mark.asyncio
async def test_orchestrator_fallback_on_unknown():
    res = await run_swachhloop_workflow("NON_EXISTENT_TASK_TYPE")
    assert res["status"] == "ERROR"
    assert res["error_message"] is not None
    assert res["requires_human_review"] is True


# ===========================================================================
# 3. FastAPI AI Endpoints & Authorization Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_api_detect_waste_endpoint(client: AsyncClient, citizen_token: str):
    img_bytes = create_test_image_bytes()
    response = await client.post(
        "/api/ai/detect-waste",
        headers={"Authorization": f"Bearer {citizen_token}"},
        files={"image": ("test.jpg", img_bytes, "image/jpeg")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "detected" in data
    assert "confidence" in data
    assert isinstance(data["waste_types"], list)


@pytest.mark.asyncio
async def test_api_detect_waste_invalid_file(client: AsyncClient, citizen_token: str):
    response = await client.post(
        "/api/ai/detect-waste",
        headers={"Authorization": f"Bearer {citizen_token}"},
        files={"image": ("test.txt", b"plain text data", "text/plain")},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_api_analyze_complaint_endpoint(client: AsyncClient, citizen_token: str):
    response = await client.post(
        "/api/ai/analyze-complaint",
        headers={"Authorization": f"Bearer {citizen_token}"},
        json={"text": "Huge garbage heap near Kalady Junction"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["urgency"] in ["low", "medium", "high", "critical"]
    assert data["extracted_location"] == "Kalady Junction"


@pytest.mark.asyncio
async def test_api_optimize_route_permissions(
    client: AsyncClient,
    citizen_token: str,
    staff_token: str,
    cleaner_token: str,
):
    loc_payload = {
        "locations": [
            {"id": "1", "latitude": 10.1667, "longitude": 76.4333, "label": "Stop 1"},
            {"id": "2", "latitude": 10.1750, "longitude": 76.4300, "label": "Stop 2"},
        ]
    }

    # Citizen is Forbidden (403)
    res_citizen = await client.post(
        "/api/ai/optimize-route",
        headers={"Authorization": f"Bearer {citizen_token}"},
        json=loc_payload,
    )
    assert res_citizen.status_code == 403

    # Cleaner is Allowed (200)
    res_cleaner = await client.post(
        "/api/ai/optimize-route",
        headers={"Authorization": f"Bearer {cleaner_token}"},
        json=loc_payload,
    )
    assert res_cleaner.status_code == 200
    assert res_cleaner.json()["estimated_distance_km"] > 0.0

    # Staff is Allowed (200)
    res_staff = await client.post(
        "/api/ai/optimize-route",
        headers={"Authorization": f"Bearer {staff_token}"},
        json=loc_payload,
    )
    assert res_staff.status_code == 200


@pytest.mark.asyncio
async def test_api_verify_cleanup_permissions(
    client: AsyncClient,
    citizen_token: str,
    cleaner_token: str,
):
    before_img = create_test_image_bytes(color=(10, 10, 10))
    after_img = create_test_image_bytes(color=(200, 200, 200))

    # Citizen forbidden (403)
    res_cit = await client.post(
        "/api/ai/verify-cleanup",
        headers={"Authorization": f"Bearer {citizen_token}"},
        files={
            "before_image": ("before.jpg", before_img, "image/jpeg"),
            "after_image": ("after.jpg", after_img, "image/jpeg"),
        },
    )
    assert res_cit.status_code == 403

    # Cleaner allowed (200)
    res_cleaner = await client.post(
        "/api/ai/verify-cleanup",
        headers={"Authorization": f"Bearer {cleaner_token}"},
        files={
            "before_image": ("before.jpg", before_img, "image/jpeg"),
            "after_image": ("after.jpg", after_img, "image/jpeg"),
        },
    )
    assert res_cleaner.status_code == 200
    data = res_cleaner.json()
    assert "status" in data
    assert "change_score" in data


@pytest.mark.asyncio
async def test_api_awareness_endpoint(client: AsyncClient, citizen_token: str):
    response = await client.post(
        "/api/ai/awareness",
        headers={"Authorization": f"Bearer {citizen_token}"},
        json={"query": "How is e-waste disposed at Kalady RRF?", "language": "en"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["found_knowledge"] is True
    assert len(data["source_articles"]) > 0


@pytest.mark.asyncio
async def test_api_workflow_run_endpoint(
    client: AsyncClient,
    citizen_token: str,
    staff_token: str,
):
    payload = {
        "task_type": "PROCESS_COMPLAINT",
        "complaint_text": "Chemical waste dumped near Periyar riverbank",
    }

    # Citizen is Forbidden (403)
    res_cit = await client.post(
        "/api/ai/workflow/run",
        headers={"Authorization": f"Bearer {citizen_token}"},
        json=payload,
    )
    assert res_cit.status_code == 403

    # Staff is Allowed (200)
    res_staff = await client.post(
        "/api/ai/workflow/run",
        headers={"Authorization": f"Bearer {staff_token}"},
        json=payload,
    )
    assert res_staff.status_code == 200
    data = res_staff.json()
    assert "workflow_id" in data
    assert data["task_type"] == "PROCESS_COMPLAINT"
    assert "results" in data
    assert len(data["audit_trail"]) > 0
