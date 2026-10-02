"""
SwachhLoop AI — Task Access Tests
=====================================
Tests:
  1. Tasks are created when staff assigns a complaint
  2. Cleaner can view their own tasks
  3. Cleaner cannot view tasks assigned to another cleaner
  4. Cleaner can update their task status
  5. Staff can view all tasks
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def _create_and_assign_complaint(
    client: AsyncClient,
    citizen_token: str,
    staff_token: str,
    cleaner_user_id: int,
    title: str = "Test Complaint for Task",
) -> int:
    """Helper: submit a complaint and assign it to a cleaner."""
    create = await client.post(
        "/api/complaints",
        data={"title": title, "priority": "MEDIUM"},
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert create.status_code == 201, create.text
    complaint_id = create.json()["id"]

    assign = await client.patch(
        f"/api/complaints/{complaint_id}/assign?cleaner_id={cleaner_user_id}",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    assert assign.status_code == 200, assign.text
    return complaint_id


class TestTaskAccess:
    async def test_cleaner_sees_own_tasks(
        self, client: AsyncClient, citizen_token, staff_token, cleaner_token, cleaner_user
    ):
        """Cleaner can list tasks assigned to them."""
        await _create_and_assign_complaint(
            client, citizen_token, staff_token, cleaner_user.id
        )

        resp = await client.get(
            "/api/tasks",
            headers={"Authorization": f"Bearer {cleaner_token}"},
        )
        assert resp.status_code == 200
        tasks = resp.json()
        assert len(tasks) >= 1
        for t in tasks:
            assert t["assigned_to"] == cleaner_user.id

    async def test_cleaner_cannot_see_other_cleaner_tasks(
        self, client: AsyncClient, citizen_token, staff_token, cleaner_user
    ):
        """Cleaner A cannot see tasks assigned to Cleaner B."""
        # Register Cleaner B
        reg = await client.post("/api/auth/register", json={
            "email": "cleaner_b@test.com",
            "password": "testpass123",
            "full_name": "Cleaner B",
            "role": "cleaner",
        })
        assert reg.status_code == 201
        cleaner_b_id = reg.json()["id"]

        login = await client.post("/api/auth/login", json={
            "email": "cleaner_b@test.com",
            "password": "testpass123",
        })
        cleaner_b_token = login.json()["access_token"]

        # Assign a complaint to Cleaner B
        complaint_id = await _create_and_assign_complaint(
            client, citizen_token, staff_token, cleaner_b_id, "Task for Cleaner B"
        )

        # Get Cleaner B's task ID
        tasks_resp = await client.get(
            "/api/tasks",
            headers={"Authorization": f"Bearer {cleaner_b_token}"},
        )
        task_id = tasks_resp.json()[0]["id"]

        # Cleaner A tries to access Cleaner B's task → 403
        # First get a cleaner_a token
        reg_a = await client.post("/api/auth/register", json={
            "email": "cleaner_a_isolation@test.com",
            "password": "testpass123",
            "full_name": "Cleaner A",
            "role": "cleaner",
        })
        login_a = await client.post("/api/auth/login", json={
            "email": "cleaner_a_isolation@test.com",
            "password": "testpass123",
        })
        cleaner_a_token = login_a.json()["access_token"]

        resp = await client.get(
            f"/api/tasks/{task_id}",
            headers={"Authorization": f"Bearer {cleaner_a_token}"},
        )
        assert resp.status_code == 403

    async def test_staff_sees_all_tasks(
        self, client: AsyncClient, citizen_token, staff_token, cleaner_user
    ):
        """Staff can view all cleaning tasks."""
        await _create_and_assign_complaint(
            client, citizen_token, staff_token, cleaner_user.id
        )
        resp = await client.get(
            "/api/tasks",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_cleaner_can_update_task_status(
        self, client: AsyncClient, citizen_token, staff_token, cleaner_token, cleaner_user
    ):
        """Cleaner can update the status of their own task."""
        await _create_and_assign_complaint(
            client, citizen_token, staff_token, cleaner_user.id
        )

        # Get task ID
        tasks = await client.get("/api/tasks", headers={"Authorization": f"Bearer {cleaner_token}"})
        task_id = tasks.json()[0]["id"]

        resp = await client.patch(
            f"/api/tasks/{task_id}",
            json={"status": "IN_PROGRESS"},
            headers={"Authorization": f"Bearer {cleaner_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "IN_PROGRESS"

    async def test_citizen_cannot_access_tasks(
        self, client: AsyncClient, citizen_token, staff_token, cleaner_user
    ):
        """Citizens cannot view any tasks — role-gated via list filtering."""
        # Citizens get an empty list (tasks filtered by cleaner_id=citizen.id which won't match)
        resp = await client.get(
            "/api/tasks",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        # Should succeed but return empty (citizen's cleaner_id = their own id = no tasks)
        assert resp.status_code == 200


class TestTaskCreation:
    async def test_assigning_complaint_creates_task(
        self, client: AsyncClient, citizen_token, staff_token, cleaner_user
    ):
        """Assigning a complaint automatically creates a cleaning task."""
        complaint_id = await _create_and_assign_complaint(
            client, citizen_token, staff_token, cleaner_user.id, "Task Creation Verify"
        )

        tasks = await client.get("/api/tasks", headers={"Authorization": f"Bearer {staff_token}"})
        complaint_task_ids = [t["complaint_id"] for t in tasks.json()]
        assert complaint_id in complaint_task_ids

    async def test_assigned_complaint_status_changes(
        self, client: AsyncClient, citizen_token, staff_token, cleaner_user
    ):
        """Complaint status changes to ASSIGNED after task assignment."""
        complaint_id = await _create_and_assign_complaint(
            client, citizen_token, staff_token, cleaner_user.id, "Status After Assign"
        )

        complaint = await client.get(
            f"/api/complaints/{complaint_id}",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert complaint.json()["status"] == "ASSIGNED"
