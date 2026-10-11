import asyncio
from sqlalchemy import select
from app.database import async_session_maker, init_db
from app.models.job import Job
from app.services.ai_scorer import ai_scorer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def rescore_all():
    await init_db()
    async with async_session_maker() as db:
        from sqlalchemy import or_
        result = await db.execute(
            select(Job).where(Job.ai_reason.like('%Unable to score%'))
        )
        jobs = result.scalars().all()
        logger.info(f"=== Found {len(jobs)} jobs to rescore ===")

        for i, job in enumerate(jobs):
            job_data = {
                "title": job.title,
                "description": job.description or "",
                "budget": float(job.budget) if job.budget else None,
                "currency": job.currency,
                "source": job.source,
                "job_type": job.job_type,
                "stack": job.stack or [],
            }
            score = await ai_scorer.score_job(job_data)
            job.ai_score = score["score"]
            job.ai_reason = score["reason"]
            job.should_apply = 1 if score["should_apply"] else 0
            logger.info(f"[{i+1}/{len(jobs)}] score={score['score']} | {job.title[:50]}")
            await asyncio.sleep(4.0)

        await db.commit()
        logger.info("=== RESCORE COMPLETE ===")


if __name__ == "__main__":
    asyncio.run(rescore_all())