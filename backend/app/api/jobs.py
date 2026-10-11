from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from typing import List, Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models.job import Job
from app.schemas.job import JobResponse, JobUpdate, JobFilter
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=List[JobResponse])
async def get_jobs(
    source: Optional[str] = Query(None, description="Filter by source"),
    job_type: Optional[str] = Query(None, description="Filter by job_type (gig/job)"),
    min_score: Optional[int] = Query(None, description="Minimum AI score"),
    max_score: Optional[int] = Query(None, description="Maximum AI score"),
    stack: Optional[str] = Query(None, description="Filter by technology stack"),
    status: Optional[str] = Query(None, description="Filter by status"),
    min_budget: Optional[float] = Query(None, description="Minimum budget"),
    max_budget: Optional[float] = Query(None, description="Maximum budget"),
    limit: int = Query(50, le=200, description="Results limit"),
    offset: int = Query(0, description="Results offset"),
    db: AsyncSession = Depends(get_db)
):
    """Get jobs with filters."""
    try:
        query = select(Job)
        
        # Build filters
        filters = []
        
        if source:
            filters.append(Job.source == source)
        
        if job_type:
            filters.append(Job.job_type == job_type)
        
        if min_score is not None:
            filters.append(Job.ai_score >= min_score)
        
        if max_score is not None:
            filters.append(Job.ai_score <= max_score)
        
        if status:
            filters.append(Job.status == status)
        
        if min_budget is not None:
            filters.append(Job.budget >= min_budget)
        
        if max_budget is not None:
            filters.append(Job.budget <= max_budget)
        
        if stack:
            # Check if stack array contains the technology
            filters.append(Job.stack.contains([stack]))
        
        if filters:
            query = query.where(and_(*filters))
        
        # Order by score desc, then by created_at desc
        query = query.order_by(desc(Job.ai_score), desc(Job.created_at))
        query = query.limit(limit).offset(offset)
        
        result = await db.execute(query)
        jobs = result.scalars().all()
        
        return jobs
        
    except Exception as e:
        logger.error(f"Error fetching jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching jobs: {str(e)}")


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get job by ID."""
    try:
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching job: {str(e)}")


@router.patch("/{job_id}/status", response_model=JobResponse)
async def update_job_status(
    job_id: int,
    job_update: JobUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update job status."""
    try:
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Update fields
        if job_update.status is not None:
            job.status = job_update.status
        
        if job_update.ai_score is not None:
            job.ai_score = job_update.ai_score
        
        if job_update.ai_reason is not None:
            job.ai_reason = job_update.ai_reason
        
        if job_update.should_apply is not None:
            job.should_apply = job_update.should_apply
        
        job.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(job)
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating job: {str(e)}")


@router.delete("/{job_id}")
async def delete_job(
    job_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Delete job by ID."""
    try:
        result = await db.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        await db.delete(job)
        await db.commit()
        
        return {"message": "Job deleted successfully", "id": job_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting job: {str(e)}")
