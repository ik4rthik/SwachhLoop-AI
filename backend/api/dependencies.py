"""
SwachhLoop AI — API Dependencies
==================================
FastAPI dependency injection for authentication and role authorization.

Phase 3: Real JWT-based authentication replacing the Phase 1 stubs.

Usage in route handlers:
    @router.get("/protected")
    async def protected(user: User = Depends(get_current_user)):
        ...

    @router.get("/admin-only")
    async def admin_route(user: User = Depends(require_admin)):
        ...
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.models.user import User, UserRole
from backend.services.auth_service import decode_access_token

# OAuth2 scheme — looks for "Authorization: Bearer <token>" header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=True)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


# ---------------------------------------------------------------------------
# Core dependency: decode token → fetch user from DB
# ---------------------------------------------------------------------------

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Decode the Bearer JWT, look up the user in the database, and return the
    User ORM instance.

    Raises HTTP 401 if:
      - Token is missing
      - Token is expired or malformed
      - User no longer exists in DB
      - User account is deactivated
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exc
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exc

    # Avoid circular import at module level
    from backend.repositories.user_repo import get_user_by_id
    user = await get_user_by_id(db, user_id)

    if user is None:
        raise credentials_exc
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact your administrator.",
        )

    return user


# ---------------------------------------------------------------------------
# Role-specific dependencies
# ---------------------------------------------------------------------------

def _require_role(required_role: UserRole):
    """Factory: returns a dependency that enforces a specific role."""
    async def _dependency(user: User = Depends(get_current_user)) -> User:
        if user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to {required_role.value} accounts.",
            )
        return user
    return _dependency


def _require_any_role(*roles: UserRole):
    """Factory: returns a dependency that accepts any of the given roles."""
    async def _dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            allowed = ", ".join(r.value for r in roles)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access restricted to: {allowed}.",
            )
        return user
    return _dependency


require_citizen = _require_role(UserRole.CITIZEN)
require_cleaner = _require_role(UserRole.CLEANER)
require_staff = _require_role(UserRole.MUNICIPAL_STAFF)
require_admin = _require_role(UserRole.ADMIN)

require_staff_or_admin = _require_any_role(UserRole.MUNICIPAL_STAFF, UserRole.ADMIN)
require_authenticated = get_current_user  # Alias for clarity
