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
    country_name: str
    country_probability: float
    created_at: datetime | None = None


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    model_config = {"arbitrary_types_allowed": True}

    status: str
    message: Optional[str] = None
    data: ProfileDataSchema


class ProfileListResponse_Old(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    model_config = {"arbitrary_types_allowed": True}

    status: str
    count: int
    data: List[ProfileDataSchema]


class ProfileListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    model_config = {"arbitrary_types_allowed": True}

    status: str
    page: Optional[int] = None
    limit: Optional[int] = None
    total: Optional[int] = None
    message: Optional[str] = None
    data: List[ProfileDataSchema]


class ErrorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    model_config = {"arbitrary_types_allowed": True}

    status: str
    message: str
