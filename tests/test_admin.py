"""
SwachhLoop AI — Admin & User Management Tests
===============================================
Tests:
  1. Admin can create privileged accounts (cleaner, staff, admin) - HTTP 201
  2. Non-admin cannot create users via admin endpoint - HTTP 403
  3. Unauthenticated cannot create users - HTTP 401
  4. Creating user with existing email returns HTTP 409
  5. Creating user with invalid role returns HTTP 422
  6. Admin can list all users - HTTP 200
  7. Admin can toggle user active status - HTTP 200
  8. Admin cannot deactivate own account - HTTP 400
  9. Deactivating non-existent user returns HTTP 404
 10. System health check returns component status - HTTP 200
 11. Municipal stats endpoint returns real metrics - HTTP 200
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestAdminUserManagement:
    async def test_admin_can_create_cleaner(self, client: AsyncClient, admin_token):
        """Admin can successfully create a cleaner account (HTTP 201)."""
        resp = await client.post(
            "/api/admin/users",
            json={
                "email": "created_cleaner@swachhloop.ai",
                "password": "cleanerpass123",
                "full_name": "Created Cleaner",
                "role": "cleaner",
                "employee_id": "CLN-999",
                "ward": "Ward 12",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["email"] == "created_cleaner@swachhloop.ai"
        assert data["role"] == "cleaner"
        assert data["employee_id"] == "CLN-999"
        assert data["is_active"] is True

    async def test_admin_can_create_staff(self, client: AsyncClient, admin_token):
        """Admin can successfully create a municipal staff account (HTTP 201)."""
        resp = await client.post(
            "/api/admin/users",
            json={
                "email": "created_staff@swachhloop.ai",
                "password": "staffpass123",
                "full_name": "Created Staff",
                "role": "municipal_staff",
                "department": "Sanitation",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "created_staff@swachhloop.ai"
        assert data["role"] == "municipal_staff"

    async def test_admin_can_create_admin(self, client: AsyncClient, admin_token):
        """Admin can create another admin account (HTTP 201)."""
        resp = await client.post(
            "/api/admin/users",
            json={
                "email": "second_admin@swachhloop.ai",
                "password": "adminpass123",
                "full_name": "Second Admin",
                "role": "admin",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 201
        assert resp.json()["role"] == "admin"

    async def test_non_admin_cannot_create_user(self, client: AsyncClient, citizen_token):
        """Citizens and non-admins receive HTTP 403 Forbidden when creating users."""
        resp = await client.post(
            "/api/admin/users",
            json={
                "email": "illegal_user@test.com",
                "password": "somepass123",
                "full_name": "Illegal User",
                "role": "admin",
            },
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert resp.status_code == 403

    async def test_unauthenticated_cannot_create_user(self, client: AsyncClient):
        """Unauthenticated request returns HTTP 401 Unauthorized."""
        resp = await client.post(
            "/api/admin/users",
            json={
                "email": "noauth@test.com",
                "password": "somepass123",
                "full_name": "No Auth",
                "role": "cleaner",
            },
        )
        assert resp.status_code == 401

    async def test_admin_create_duplicate_email(self, client: AsyncClient, admin_token, citizen_user):
        """Attempting to create user with existing email returns HTTP 409 Conflict."""
        resp = await client.post(
            "/api/admin/users",
            json={
                "email": citizen_user.email,
                "password": "somepass123",
                "full_name": "Duplicate Attempt",
                "role": "cleaner",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 409
        assert "already exists" in resp.json()["detail"].lower()

    async def test_admin_create_invalid_role(self, client: AsyncClient, admin_token):
        """Invalid role returns HTTP 422 Unprocessable Entity."""
        resp = await client.post(
            "/api/admin/users",
            json={
                "email": "invalid_role@test.com",
                "password": "somepass123",
                "full_name": "Invalid Role",
                "role": "overlord",
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 422

    async def test_admin_list_users(self, client: AsyncClient, admin_token, citizen_user):
        """Admin can list all registered users (HTTP 200)."""
        resp = await client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        emails = [u["email"] for u in resp.json()]
        assert citizen_user.email in emails

    async def test_admin_toggle_user_active(self, client: AsyncClient, admin_token, citizen_user):
        """Admin can deactivate and reactivate a user account (HTTP 200)."""
        # Deactivate
        resp = await client.patch(
            f"/api/admin/users/{citizen_user.id}?is_active=false",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

        # Reactivate
        resp2 = await client.patch(
            f"/api/admin/users/{citizen_user.id}?is_active=true",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp2.status_code == 200
        assert resp2.json()["is_active"] is True

    async def test_admin_cannot_deactivate_self(self, client: AsyncClient, admin_token, admin_user):
        """Admin cannot deactivate their own account (HTTP 400 Bad Request)."""
        resp = await client.patch(
            f"/api/admin/users/{admin_user.id}?is_active=false",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 400
        assert "cannot deactivate your own account" in resp.json()["detail"].lower()

    async def test_admin_deactivate_nonexistent_user(self, client: AsyncClient, admin_token):
        """Deactivating non-existent user returns HTTP 404 Not Found."""
        resp = await client.patch(
            "/api/admin/users/999999?is_active=false",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 404


class TestAdminSystemStats:
    async def test_system_health(self, client: AsyncClient, admin_token):
        """Admin can inspect system health components (HTTP 200)."""
        resp = await client.get(
            "/api/admin/health",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        services = {s["service"]: s["status"] for s in resp.json()}
        assert "Database" in services
        assert "Backend API" in services

    async def test_municipal_stats(self, client: AsyncClient, staff_token):
        """Municipal staff can retrieve municipal stats (HTTP 200)."""
        resp = await client.get(
            "/api/stats/municipal",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_complaints" in data
        assert "cleaners_available" in data
        assert "pending" in data
