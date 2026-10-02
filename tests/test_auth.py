"""
SwachhLoop AI — Authentication Tests
========================================
Tests:
  1. User registration (success + duplicate email)
  2. Login (success + wrong password + unknown email)
  3. GET /me (valid token + invalid token)
  4. Role information comes from server, not client
  5. Token expiry is enforced (tested via invalid signature)
"""

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestRegister:
    async def test_register_citizen_success(self, client: AsyncClient):
        """A new citizen account can be registered."""
        resp = await client.post("/api/auth/register", json={
            "email": "new_citizen@test.com",
            "password": "securepass123",
            "full_name": "New Citizen",
            "role": "citizen",
        })
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["email"] == "new_citizen@test.com"
        assert data["role"] == "citizen"
        assert "hashed_password" not in data  # Never exposed

    async def test_register_duplicate_email(self, client: AsyncClient):
        """Registering with an existing email returns 409."""
        payload = {
            "email": "dup@test.com",
            "password": "securepass123",
            "full_name": "Dup User",
            "role": "citizen",
        }
        r1 = await client.post("/api/auth/register", json=payload)
        assert r1.status_code == 201

        r2 = await client.post("/api/auth/register", json=payload)
        assert r2.status_code == 409
        assert "already exists" in r2.json()["detail"].lower()

    async def test_register_privileged_roles_forbidden(self, client: AsyncClient):
        """Public registration cannot self-assign privileged roles (admin, cleaner, staff)."""
        for privileged_role in ["admin", "cleaner", "municipal_staff"]:
            resp = await client.post("/api/auth/register", json={
                "email": f"hacker_{privileged_role}@test.com",
                "password": "securepass123",
                "full_name": "Privilege Escalation Attempt",
                "role": privileged_role,
            })
            assert resp.status_code == 403, f"Expected 403 for role {privileged_role}, got {resp.status_code}"
            assert "restricted to citizens" in resp.json()["detail"].lower()

    async def test_register_arbitrary_role_forbidden(self, client: AsyncClient):
        """Registering with an invalid role returns 403."""
        resp = await client.post("/api/auth/register", json={
            "email": "badrole@test.com",
            "password": "securepass123",
            "full_name": "Bad Role",
            "role": "superuser",
        })
        assert resp.status_code == 403

    async def test_register_weak_password(self, client: AsyncClient):
        """Password shorter than 8 characters is rejected with 422."""
        resp = await client.post("/api/auth/register", json={
            "email": "weak@test.com",
            "password": "short",  # < 8 chars
            "full_name": "Weak Pass",
            "role": "citizen",
        })
        assert resp.status_code == 422


class TestLogin:
    async def test_login_success(self, client: AsyncClient, citizen_user):
        """Valid credentials return a JWT token and user profile."""
        resp = await client.post("/api/auth/login", json={
            "email": citizen_user.email,
            "password": "testpass123",
        })
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == citizen_user.email
        assert data["user"]["role"] == "citizen"
        # Password must never appear in response
        assert "password" not in str(data)
        assert "hashed_password" not in str(data)

    async def test_login_wrong_password(self, client: AsyncClient, citizen_user):
        """Wrong password returns 401."""
        resp = await client.post("/api/auth/login", json={
            "email": citizen_user.email,
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    async def test_login_unknown_email(self, client: AsyncClient):
        """Unknown email returns 401 (same error as wrong password — no email enumeration)."""
        resp = await client.post("/api/auth/login", json={
            "email": "nobody@nowhere.com",
            "password": "somepassword",
        })
        assert resp.status_code == 401

    async def test_login_returns_server_role(self, client: AsyncClient, admin_user):
        """The role in the token response comes from the database, not the client."""
        resp = await client.post("/api/auth/login", json={
            "email": admin_user.email,
            "password": "testpass123",
        })
        assert resp.status_code == 200
        # Server returns the real role from DB
        assert resp.json()["user"]["role"] == "admin"

    async def test_login_inactive_account(self, client: AsyncClient, db_session, citizen_user):
        """Deactivated user account cannot log in (returns 403)."""
        citizen_user.is_active = False
        await db_session.flush()

        resp = await client.post("/api/auth/login", json={
            "email": citizen_user.email,
            "password": "testpass123",
        })
        assert resp.status_code == 403
        assert "deactivated" in resp.json()["detail"].lower()


class TestMe:
    async def test_me_with_valid_token(self, client: AsyncClient, citizen_token, citizen_user):
        """GET /me returns current user with a valid token."""
        resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["user"]["email"] == citizen_user.email

    async def test_me_without_token(self, client: AsyncClient):
        """GET /me without token returns 401."""
        resp = await client.get("/api/auth/me")
        assert resp.status_code == 401

    async def test_me_with_invalid_token(self, client: AsyncClient):
        """GET /me with a tampered token returns 401."""
        resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer this.is.not.a.valid.jwt"},
        )
        assert resp.status_code == 401

    async def test_me_with_expired_token(self, client: AsyncClient, citizen_user):
        """Expired JWT token returns 401."""
        from datetime import timedelta
        from backend.services.auth_service import create_access_token
        expired_token = create_access_token(
            {"sub": str(citizen_user.id), "role": "citizen"},
            expires_delta=timedelta(seconds=-10),
        )
        resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert resp.status_code == 401

    async def test_me_with_tampered_signature(self, client: AsyncClient, citizen_user):
        """Token signed with wrong secret key returns 401."""
        from jose import jwt
        fake_token = jwt.encode(
            {"sub": str(citizen_user.id), "role": "citizen"},
            "wrong_secret_key_12345678901234567890",
            algorithm="HS256",
        )
        resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {fake_token}"},
        )
        assert resp.status_code == 401

    async def test_me_inactive_user(self, client: AsyncClient, db_session, citizen_token, citizen_user):
        """Token for a user who was subsequently deactivated returns 403."""
        citizen_user.is_active = False
        await db_session.flush()

        resp = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {citizen_token}"},
        )
        assert resp.status_code == 403
        assert "deactivated" in resp.json()["detail"].lower()

    async def test_database_persistence(self, client: AsyncClient):
        """Registered user can be fetched via /me — proves DB persistence."""
        reg = await client.post("/api/auth/register", json={
            "email": "persist_test@test.com",
            "password": "persistpass123",
            "full_name": "Persist Test",
            "role": "citizen",
        })
        assert reg.status_code == 201

        login = await client.post("/api/auth/login", json={
            "email": "persist_test@test.com",
            "password": "persistpass123",
        })
        assert login.status_code == 200
        token = login.json()["access_token"]

        me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["user"]["full_name"] == "Persist Test"

