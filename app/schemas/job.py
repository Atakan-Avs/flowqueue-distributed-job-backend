import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class JobCreate(BaseModel):
    job_type: str = Field(..., min_length=1, max_length=100)
    payload: str = Field(..., min_length=1)


class JobResponse(BaseModel):
    id: uuid.UUID
    job_type: str
    status: str
    payload: str
    result: str | None
    error_message: str | None
    retry_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    items: list[JobResponse]
    total: int
    skip: int
    limit: int