"""
SwachhLoop AI — Authentication Schemas
========================================
Pydantic request/response models for the /api/auth/* endpoints.
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class LoginRequest(BaseModel):
    """POST /api/auth/login"""
    email: EmailStr
    password: str = Field(min_length=1)


class RegisterRequest(BaseModel):
    """POST /api/auth/register"""
    email: EmailStr
    password: str = Field(min_length=8, description="Minimum 8 characters")
    full_name: str = Field(min_length=2, max_length=255)
    role: str = Field(default="citizen", description="citizen | cleaner | municipal_staff | admin")
    phone: str | None = Field(default=None, max_length=20)
    ward: str | None = Field(default=None, max_length=100)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed = {"citizen", "cleaner", "municipal_staff", "admin"}
        if v not in allowed:
            raise ValueError(f"role must be one of: {', '.join(sorted(allowed))}")
        return v


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class UserResponse(BaseModel):
    """Public representation of a user — never includes hashed_password."""
    id: int
    email: str
    full_name: str
    role: str
    phone: str | None = None
    ward: str | None = None
    employee_id: str | None = None
    department: str | None = None
    avatar_initials: str | None = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    """Response returned by /api/auth/login"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MeResponse(BaseModel):
    """Response returned by GET /api/auth/me"""
    user: UserResponse
