from datetime import datetime
from pydantic import BaseModel


class GenderBaseSchema(BaseModel):
    name: str | None = None


class GenderDataSchema(GenderBaseSchema):
    gender: str
    probability: float
    sample_size: int
    is_confident: bool
    processed_at: str


class GenderResponseSchema(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    status: str
    data: GenderDataSchema
