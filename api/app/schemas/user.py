"""Pydantic schemas for user resources."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

RoleName = Literal["analyst", "manager", "admin"]


class UserBase(BaseModel):
    email: EmailStr
    full_name: str | None = None
    roles: list[RoleName] = Field(default_factory=list)
    is_active: bool = True
    is_superuser: bool = False


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    full_name: str | None = None
    password: str | None = None
    roles: list[RoleName] | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None


class UserRead(UserBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    access_token_expires_in: int
    refresh_token_expires_in: int


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str
    exp: int
    jti: str | None = None
