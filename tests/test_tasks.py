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
        self, client: AsyncClient, db_session, citizen_token, staff_token, cleaner_token, cleaner_user
    ):
        """Cleaner A cannot see tasks assigned to Cleaner B."""
        from backend.repositories.user_repo import create_user
        from backend.services.auth_service import hash_password
        from backend.models.user import UserRole

        # Create Cleaner B directly in DB
        cleaner_b = await create_user(
            db=db_session,
            email="cleaner_b_iso@test.com",
            hashed_password=hash_password("testpass123"),
            full_name="Cleaner B",
            role=UserRole.CLEANER,
            employee_id="CLN-B",
        )

        login = await client.post("/api/auth/login", json={
            "email": "cleaner_b_iso@test.com",
            "password": "testpass123",
        })
        assert login.status_code == 200
        cleaner_b_token = login.json()["access_token"]

        # Assign a complaint to Cleaner B
        complaint_id = await _create_and_assign_complaint(
            client, citizen_token, staff_token, cleaner_b.id, "Task for Cleaner B"
        )

        # Get Cleaner B's task ID
        tasks_resp = await client.get(
            "/api/tasks",
            headers={"Authorization": f"Bearer {cleaner_b_token}"},
        )
        assert tasks_resp.status_code == 200
        task_id = tasks_resp.json()[0]["id"]

        # Cleaner A tries to view Cleaner B's task → 403
        resp = await client.get(
            f"/api/tasks/{task_id}",
            headers={"Authorization": f"Bearer {cleaner_token}"},
        )
        assert resp.status_code == 403

        # Cleaner A tries to update Cleaner B's task → 403
        patch_resp = await client.patch(
            f"/api/tasks/{task_id}",
            json={"status": "IN_PROGRESS"},
            headers={"Authorization": f"Bearer {cleaner_token}"},
        )
        assert patch_resp.status_code == 403

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

    async def test_cleaner_can_update_task_status_and_sync_complaint(
        self, client: AsyncClient, citizen_token, staff_token, cleaner_token, cleaner_user
    ):
        """Cleaner can update task status, which syncs the complaint status (CLEANING, VERIFICATION)."""
        complaint_id = await _create_and_assign_complaint(
            client, citizen_token, staff_token, cleaner_user.id
        )

        # Get task ID
        tasks = await client.get("/api/tasks", headers={"Authorization": f"Bearer {cleaner_token}"})
        task_id = tasks.json()[0]["id"]

        # 1. Update to IN_PROGRESS -> complaint should become CLEANING
        resp = await client.patch(
            f"/api/tasks/{task_id}",
            json={"status": "IN_PROGRESS"},
            headers={"Authorization": f"Bearer {cleaner_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "IN_PROGRESS"

        c_resp = await client.get(f"/api/complaints/{complaint_id}", headers={"Authorization": f"Bearer {staff_token}"})
        assert c_resp.json()["status"] == "CLEANING"

        # 2. Update to COMPLETED -> complaint should become VERIFICATION
        resp2 = await client.patch(
            f"/api/tasks/{task_id}",
            json={"status": "COMPLETED"},
            headers={"Authorization": f"Bearer {cleaner_token}"},
        )
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "COMPLETED"

        c_resp2 = await client.get(f"/api/complaints/{complaint_id}", headers={"Authorization": f"Bearer {staff_token}"})
        assert c_resp2.json()["status"] == "VERIFICATION"

    async def test_citizen_cannot_access_tasks(
        self, client: AsyncClient, citizen_token, staff_token, cleaner_user
    ):
        """Citizens cannot view or modify any cleaning tasks (403 Forbidden)."""
        # 1. List tasks
        resp = await client.get(
            "/api/tasks",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert resp.status_code == 403

        # Create a task to test single task endpoints
        complaint_id = await _create_and_assign_complaint(
            client, citizen_token, staff_token, cleaner_user.id
        )
        tasks = await client.get("/api/tasks", headers={"Authorization": f"Bearer {staff_token}"})
        task_id = tasks.json()[0]["id"]

        # 2. Get task by ID
        get_resp = await client.get(
            f"/api/tasks/{task_id}",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert get_resp.status_code == 403

        # 3. Patch task
        patch_resp = await client.patch(
            f"/api/tasks/{task_id}",
            json={"status": "IN_PROGRESS"},
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert patch_resp.status_code == 403

    async def test_list_cleaners_endpoint(
        self, client: AsyncClient, staff_token, citizen_token, cleaner_user
    ):
        """Staff can list active cleaners; citizens are forbidden."""
        staff_resp = await client.get(
            "/api/tasks/cleaners",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert staff_resp.status_code == 200
        cleaner_emails = [c["email"] for c in staff_resp.json()]
        assert cleaner_user.email in cleaner_emails

        citizen_resp = await client.get(
            "/api/tasks/cleaners",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert citizen_resp.status_code == 403



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
