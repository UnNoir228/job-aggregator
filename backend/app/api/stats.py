from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from app.database import get_db
from app.models.job import Job
from app.schemas.job import StatsResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get aggregated statistics."""
    try:
        # Total jobs
        total_result = await db.execute(select(func.count(Job.id)))
        total_jobs = total_result.scalar()
        
        # Jobs by source
        by_source_result = await db.execute(
            select(Job.source, func.count(Job.id))
            .group_by(Job.source)
        )
        by_source = {row[0]: row[1] for row in by_source_result.all()}
        
        # Jobs by status
        by_status_result = await db.execute(
            select(Job.status, func.count(Job.id))
            .group_by(Job.status)
        )
        by_status = {row[0]: row[1] for row in by_status_result.all()}
        
        # Average score (only for jobs with scores)
        avg_score_result = await db.execute(
            select(func.avg(Job.ai_score))
            .where(Job.ai_score.isnot(None))
        )
        average_score = avg_score_result.scalar()
        
        # High score jobs (>= 80)
        high_score_result = await db.execute(
            select(func.count(Job.id))
            .where(Job.ai_score >= 80)
        )
        high_score_jobs = high_score_result.scalar()
        
        # Jobs today
        today = datetime.utcnow().date()
        jobs_today_result = await db.execute(
            select(func.count(Job.id))
            .where(func.date(Job.created_at) == today)
        )
        jobs_today = jobs_today_result.scalar()
        
        return StatsResponse(
            total_jobs=total_jobs,
            by_source=by_source,
            by_status=by_status,
            average_score=float(average_score) if average_score else None,
            high_score_jobs=high_score_jobs,
            jobs_today=jobs_today
        )
        
    except Exception as e:
        logger.error(f"Error fetching stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")
