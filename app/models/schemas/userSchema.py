from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    github_id: str
    username: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime


class TokenResponse(BaseModel):
    status: str = "success"
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class WhoAmIResponse(BaseModel):
    status: str = "success"
    data: UserResponse
