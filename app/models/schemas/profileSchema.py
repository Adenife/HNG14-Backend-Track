from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from uuid import UUID
from typing import List, Optional


class ProfileCreateRequest(BaseModel):
    name: str = Field(
        ..., description="The name of the profile to be created", max_length=100
    )


class ProfileDataSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID | None = None
    name: str
    gender: str
    gender_probability: float
    sample_size: Optional[int] = None
    age: int
    age_group: str
    country_id: str
    country_name: Optional[str] = None
    country_probability: float
    created_at: datetime | None = None


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    message: Optional[str] = None
    data: ProfileDataSchema


class PaginationLinks(BaseModel):
    self: str
    next: Optional[str] = None
    prev: Optional[str] = None


class ProfileListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    page: int
    limit: int
    total: int
    total_pages: int
    links: PaginationLinks
    data: List[ProfileDataSchema]


# Kept for backwards-compatible /profiles/old endpoint
class ProfileListResponse_Old(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    count: int
    data: List[ProfileDataSchema]


class ErrorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    message: str
