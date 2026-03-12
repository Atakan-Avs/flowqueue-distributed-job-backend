from pydantic import BaseModel


class JobMetricsResponse(BaseModel):
    total_jobs: int
    pending: int
    processing: int
    completed: int
    failed: int