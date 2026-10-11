from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class JobBase(BaseModel):
    """Base schema for Job."""
    source: str = Field(..., max_length=50)
    source_url: str = Field(..., max_length=500)
    title: str = Field(..., max_length=300)
    description: Optional[str] = None
    budget: Optional[Decimal] = None
    currency: str = Field(default="RUB", max_length=3)
    job_type: Optional[str] = Field(None, max_length=20)
    stack: List[str] = Field(default_factory=list)
    location: Optional[str] = Field(None, max_length=100)
    posted_at: Optional[datetime] = None


class JobCreate(JobBase):
    """Schema for creating a new job."""
    raw_hash: str = Field(..., max_length=64)


class JobUpdate(BaseModel):
    """Schema for updating job status."""
    status: Optional[str] = Field(None, max_length=20)
    ai_score: Optional[int] = None
    ai_reason: Optional[str] = None
    should_apply: Optional[int] = None


class JobResponse(JobBase):
    """Schema for job response."""
    id: int
    raw_hash: str
    ai_score: Optional[int] = None
    ai_reason: Optional[str] = None
    should_apply: int = 0
    status: str = "new"
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class JobFilter(BaseModel):
    """Schema for filtering jobs."""
    source: Optional[str] = None
    job_type: Optional[str] = None
    min_score: Optional[int] = None
    max_score: Optional[int] = None
    stack: Optional[str] = None
    status: Optional[str] = None
    min_budget: Optional[float] = None
    max_budget: Optional[float] = None
    limit: int = 50
    offset: int = 0


class StatsResponse(BaseModel):
    """Schema for statistics response."""
    total_jobs: int
    by_source: dict
    by_status: dict
    average_score: Optional[float] = None
    high_score_jobs: int  # score >= 80
    jobs_today: int
