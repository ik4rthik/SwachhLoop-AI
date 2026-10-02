"""
SwachhLoop AI — Authentication Routes
========================================
Endpoints:
    POST /api/auth/register  — create a new account
    POST /api/auth/login     — exchange credentials for JWT
    GET  /api/auth/me        — return current user's profile
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user
from backend.db.session import get_db
from backend.models.user import User, UserRole
from backend.repositories import user_repo
from backend.schemas.auth import LoginRequest, MeResponse, RegisterRequest, TokenResponse, UserResponse
from backend.services.audit_service import ACTION_LOGIN, ACTION_REGISTER, log_event
from backend.services.auth_service import create_user_token, hash_password, verify_password

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# POST /api/auth/register
# ---------------------------------------------------------------------------

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new account",
)
async def register(
    body: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Create a new user account.

    - Citizens can self-register.
    - Other roles (cleaner, staff, admin) can be created here for demo/dev.
      In production, restrict non-citizen registration to admin-only.
    """
    # Check email uniqueness
    existing = await user_repo.get_user_by_email(db, body.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    try:
        role = UserRole(body.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid role: {body.role!r}",
        )

    user = await user_repo.create_user(
        db=db,
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=role,
        phone=body.phone,
        ward=body.ward,
    )

    await log_event(
        db,
        action=ACTION_REGISTER,
        actor_id=user.id,
        resource_type="user",
        resource_id=str(user.id),
        detail=f"New {role.value} account: {user.email}",
        ip_address=request.client.host if request.client else None,
    )

    logger.info(f"New user registered: {user.email} ({role.value})")
    return UserResponse.model_validate(user)


# ---------------------------------------------------------------------------
# POST /api/auth/login
# ---------------------------------------------------------------------------

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login and receive JWT token",
)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate with email + password.
    Returns a JWT Bearer token and the user's profile.
    """
    # Generic error — don't reveal whether email or password was wrong
    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user = await user_repo.get_user_by_email(db, body.email)
    if user is None or not verify_password(body.password, user.hashed_password):
        raise auth_error

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact your administrator.",
        )

    token = create_user_token(user.id, user.role.value)

    await log_event(
        db,
        action=ACTION_LOGIN,
        actor_id=user.id,
        resource_type="user",
        resource_id=str(user.id),
        detail=f"Login: {user.email}",
        ip_address=request.client.host if request.client else None,
    )

    logger.info(f"User logged in: {user.email} ({user.role.value})")
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


# ---------------------------------------------------------------------------
# GET /api/auth/me
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=MeResponse,
    summary="Get current user profile",
)
async def me(current_user: User = Depends(get_current_user)) -> MeResponse:
    """Return the profile of the currently authenticated user."""
    return MeResponse(user=UserResponse.model_validate(current_user))
