"""
SwachhLoop AI — Audit Log Tests
===================================
Tests that critical actions are recorded in audit_logs.
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestAuditLog:
    async def test_login_creates_audit_entry(self, client: AsyncClient, admin_token, admin_user):
        """Login action creates an audit log entry visible to admin."""
        # Login already happened (admin_token fixture), now check audit log
        resp = await client.get(
            "/api/admin/audit-log",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        actions = [entry["action"] for entry in resp.json()]
        assert "LOGIN" in actions

    async def test_complaint_submission_creates_audit_entry(
        self, client: AsyncClient, citizen_token, admin_token
    ):
        """Submitting a complaint creates an audit log entry."""
        await client.post(
            "/api/complaints",
            data={"title": "Audit Test Complaint", "priority": "LOW"},
            headers={"Authorization": f"Bearer {citizen_token}"},
        )

        resp = await client.get(
            "/api/admin/audit-log",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        actions = [entry["action"] for entry in resp.json()]
        assert "SUBMIT_COMPLAINT" in actions

    async def test_audit_log_requires_admin(self, client: AsyncClient, citizen_token):
        """Non-admin cannot access audit log."""
        resp = await client.get(
            "/api/admin/audit-log",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert resp.status_code == 403

    async def test_admin_users_endpoint(self, client: AsyncClient, admin_token):
        """Admin can list all users."""
        resp = await client.get(
            "/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_system_health_requires_admin(self, client: AsyncClient, citizen_token, admin_token):
        """System health endpoint is admin-only."""
        citizen_resp = await client.get(
            "/api/admin/health",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert citizen_resp.status_code == 403

        admin_resp = await client.get(
            "/api/admin/health",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert admin_resp.status_code == 200
        # DB should be online
        services = {s["service"]: s["status"] for s in admin_resp.json()}
        assert services["Database"] == "Online"
