"""
SwachhLoop AI — Complaint Tests
===================================
Tests:
  1. Complaint creation (citizen)
  2. Complaint list (citizen sees own only, staff sees all)
  3. Complaint ownership enforcement
  4. Complaint retrieval
  5. Status update (staff only)
  6. Role authorization enforcement
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestComplaintCreate:
    async def test_citizen_can_submit_complaint(self, client: AsyncClient, citizen_token):
        """Citizen can submit a complaint without an image."""
        resp = await client.post(
            "/api/complaints",
            data={
                "title": "Test Waste Dump",
                "description": "Large pile of garbage near the park.",
                "latitude": "10.5273",
                "longitude": "76.2144",
                "location_label": "Gandhi Park Entrance",
                "waste_type": "Plastic Waste",
                "priority": "HIGH",
            },
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["title"] == "Test Waste Dump"
        assert data["status"] == "SUBMITTED"
        assert data["priority"] == "HIGH"
        assert data["id"] is not None

    async def test_unauthenticated_cannot_submit(self, client: AsyncClient):
        """Unauthenticated request returns 401."""
        resp = await client.post(
            "/api/complaints",
            data={"title": "Unauthorized", "priority": "LOW"},
        )
        assert resp.status_code == 401

    async def test_invalid_priority_rejected(self, client: AsyncClient, citizen_token):
        """Invalid priority value returns 422."""
        resp = await client.post(
            "/api/complaints",
            data={"title": "Bad Priority", "priority": "EXTREME"},
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert resp.status_code == 422


class TestComplaintRetrieval:
    async def test_citizen_sees_own_complaints(
        self, client: AsyncClient, citizen_token, citizen_user
    ):
        """Citizen can retrieve the complaints they submitted."""
        # Submit a complaint
        await client.post(
            "/api/complaints",
            data={"title": "My Complaint", "priority": "MEDIUM"},
            headers={"Authorization": f"Bearer {citizen_token}"},
        )

        resp = await client.get(
            "/api/complaints",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        # All complaints belong to this citizen
        for c in data:
            assert c["citizen_id"] == citizen_user.id

    async def test_staff_sees_all_complaints(
        self, client: AsyncClient, citizen_token, staff_token
    ):
        """Municipal staff can see all complaints regardless of owner."""
        # Citizen submits
        await client.post(
            "/api/complaints",
            data={"title": "Staff View Test", "priority": "LOW"},
            headers={"Authorization": f"Bearer {citizen_token}"},
        )

        resp = await client.get(
            "/api/complaints",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert resp.status_code == 200
        # Staff sees all (at least the one just submitted)
        assert len(resp.json()) >= 1

    async def test_get_complaint_by_id(self, client: AsyncClient, citizen_token):
        """Citizen can retrieve their own complaint by ID."""
        create_resp = await client.post(
            "/api/complaints",
            data={"title": "Retrieve By ID", "priority": "LOW"},
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert create_resp.status_code == 201
        complaint_id = create_resp.json()["id"]

        get_resp = await client.get(
            f"/api/complaints/{complaint_id}",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == complaint_id


class TestComplaintOwnership:
    async def test_citizen_cannot_view_another_citizens_complaint(
        self, client: AsyncClient, citizen_token, staff_token, citizen_user
    ):
        """Citizen A cannot access Citizen B's complaint."""
        # Register a second citizen
        reg = await client.post("/api/auth/register", json={
            "email": "citizen_b@test.com",
            "password": "testpass123",
            "full_name": "Citizen B",
            "role": "citizen",
        })
        assert reg.status_code == 201

        login = await client.post("/api/auth/login", json={
            "email": "citizen_b@test.com",
            "password": "testpass123",
        })
        citizen_b_token = login.json()["access_token"]

        # Citizen B submits a complaint
        create = await client.post(
            "/api/complaints",
            data={"title": "Citizen B Complaint", "priority": "LOW"},
            headers={"Authorization": f"Bearer {citizen_b_token}"},
        )
        assert create.status_code == 201
        complaint_id = create.json()["id"]

        # Citizen A tries to access Citizen B's complaint → 403
        resp = await client.get(
            f"/api/complaints/{complaint_id}",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert resp.status_code == 403

    async def test_cleaner_cannot_view_unassigned_complaint(
        self, client: AsyncClient, citizen_token, cleaner_token
    ):
        """Cleaner cannot view a complaint that is not assigned to them."""
        create = await client.post(
            "/api/complaints",
            data={"title": "Unassigned to Cleaner", "priority": "LOW"},
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        complaint_id = create.json()["id"]

        resp = await client.get(
            f"/api/complaints/{complaint_id}",
            headers={"Authorization": f"Bearer {cleaner_token}"},
        )
        assert resp.status_code == 403

    async def test_cleaner_can_view_assigned_complaint(
        self, client: AsyncClient, citizen_token, staff_token, cleaner_token, cleaner_user
    ):
        """Cleaner CAN view a complaint that has been assigned to them."""
        create = await client.post(
            "/api/complaints",
            data={"title": "Assigned to Cleaner", "priority": "HIGH"},
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        complaint_id = create.json()["id"]

        # Staff assigns to cleaner
        assign = await client.patch(
            f"/api/complaints/{complaint_id}/assign?cleaner_id={cleaner_user.id}",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert assign.status_code == 200

        # Cleaner accesses the assigned complaint
        resp = await client.get(
            f"/api/complaints/{complaint_id}",
            headers={"Authorization": f"Bearer {cleaner_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == complaint_id
        assert resp.json()["assigned_cleaner"] == cleaner_user.full_name

    async def test_get_nonexistent_complaint_returns_404(
        self, client: AsyncClient, staff_token
    ):
        """Requesting a non-existent complaint ID returns 404."""
        resp = await client.get(
            "/api/complaints/999999",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert resp.status_code == 404


class TestComplaintStatusUpdate:
    async def test_staff_can_update_status(
        self, client: AsyncClient, citizen_token, staff_token
    ):
        """Staff can update a complaint's status."""
        create = await client.post(
            "/api/complaints",
            data={"title": "Status Update Test", "priority": "MEDIUM"},
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        complaint_id = create.json()["id"]

        resp = await client.patch(
            f"/api/complaints/{complaint_id}/status?new_status=VALIDATED",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "VALIDATED"

    async def test_citizen_cannot_update_status(
        self, client: AsyncClient, citizen_token
    ):
        """Citizen cannot change complaint status (staff/admin only)."""
        create = await client.post(
            "/api/complaints",
            data={"title": "No Status Change", "priority": "LOW"},
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        complaint_id = create.json()["id"]

        resp = await client.patch(
            f"/api/complaints/{complaint_id}/status?new_status=RESOLVED",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert resp.status_code == 403
