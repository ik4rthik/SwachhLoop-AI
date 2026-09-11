"""
SwachhLoop AI — API Dependencies
==================================
FastAPI dependency injection stubs.

These are the shared dependencies (auth, db session, etc.) that will be
injected into route handlers. Phase 1 provides the skeleton; real
implementations come in Phase 2 (auth) and Phase 2 (DB).
"""

from fastapi import Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db  # noqa: F401 — re-exported for convenience


# ---------------------------------------------------------------------------
# Authentication stub (Phase 2)
# ---------------------------------------------------------------------------

async def get_current_user(
    authorization: str | None = Header(default=None),
) -> dict:
    """
    Phase 2: Replace this stub with real JWT verification.

    For now, returns a dummy user so routes can be developed
    without a working auth system.
    """
    # TODO: Phase 2 — decode JWT, look up user in DB, return User model
    if authorization is None:
        # In Phase 1, we allow unauthenticated access to all routes
        return {"id": None, "role": "anonymous"}

    raise HTTPException(
        status_code=501,
        detail="Authentication not yet implemented. Coming in Phase 2.",
    )


async def require_role(required_role: str, user: dict) -> dict:
    """
    Phase 2: Enforce role-based access control.

    Usage in route:
        user = Depends(get_current_user)
        await require_role("admin", user)
    """
    # TODO: Phase 2 — check user["role"] against required_role
    return user
