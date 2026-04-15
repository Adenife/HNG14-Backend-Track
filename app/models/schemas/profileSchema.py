from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import List, Optional


class ProfileCreateRequest(BaseModel):
    name: str


class ProfileDataSchema(BaseModel):
    id: str | UUID
    name: str
    gender: str
    gender_probability: float
    sample_size: int
    age: int
    age_group: str
    country_id: str
    country_probability: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProfileResponse(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    status: str
    data: ProfileDataSchema


class ProfileAlreadyExistsResponse(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    status: str
    message: str
    data: ProfileDataSchema


class ProfileListResponse(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    status: str
    count: int
    data: List[ProfileDataSchema]


class ErrorResponse(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    status: str
    message: str
