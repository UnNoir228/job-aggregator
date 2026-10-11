import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import async_session_maker
from app.models.job import Job
from app.parsers import TelegramParser
from app.services import normalizer, deduplicator, ai_scorer
from app.bot.telegram_bot import notify_new_job

from sqlalchemy import select

logger = logging.getLogger(__name__)


async def run_parsers(mode: str = "western") -> int:
    """
    mode: "western" | "ru" | "all"
    Возвращает: количество новых заказов.
    """
    logger.info(f"=== Parser run (mode={mode}) ===")

    parsers = []

    if mode in ("western", "all"):
        parsers.append(TelegramParser(channels=settings.western_channels))

    if mode in ("ru", "all"):
        parsers.append(TelegramParser(channels=settings.ru_channels))

    all_jobs = []
    for parser in parsers:
        try:
            jobs = await parser.safe_parse()
            all_jobs.extend(jobs)
            logger.info(f"{parser.source_name}: parsed {len(jobs)}")
        except Exception as e:
            logger.error(f"Parser {parser.source_name} failed: {e}")

    if not all_jobs:
        logger.info("No jobs parsed")
        return 0

    # Normalize + dedup
    normalized = [normalizer.normalize(j) for j in all_jobs]
    unique = deduplicator.remove_duplicates(normalized)
    logger.info(f"After dedup: {len(unique)} unique jobs")

    # Save new
    new_job_ids = []
    async with async_session_maker() as db:
        for job_data in unique:
            raw_hash = deduplicator.calculate_hash(job_data)
            existing = await db.execute(select(Job).where(Job.raw_hash == raw_hash))
            if existing.scalar_one_or_none():
                continue

            job = Job(
                source=job_data["source"],
                source_url=job_data["source_url"],
                title=job_data["title"][:300],
                description=job_data.get("description", ""),
                budget=job_data.get("budget"),
                currency=job_data.get("currency", "RUB"),
                job_type=job_data.get("job_type"),
                stack=job_data.get("stack", []),
                location=job_data.get("location"),
                posted_at=job_data.get("posted_at"),
                raw_hash=raw_hash,
                status="new",
            )
            db.add(job)
            await db.flush()
            new_job_ids.append(job.id)

        await db.commit()

    logger.info(f"Saved {len(new_job_ids)} new jobs (mode={mode})")

    # Score new jobs
    if new_job_ids:
        async with async_session_maker() as db:
            result = await db.execute(select(Job).where(Job.id.in_(new_job_ids)))
            jobs_to_score = result.scalars().all()

            for job in jobs_to_score:
                job_data = {
                    "title": job.title,
                    "description": job.description,
                    "budget": float(job.budget) if job.budget else None,
                    "currency": job.currency,
                    "source": job.source,
                    "job_type": job.job_type,
                    "stack": job.stack,
                }
                score = await ai_scorer.score_job(job_data)
                job.ai_score = score["score"]
                job.ai_reason = score["reason"]
                job.should_apply = 1 if score["should_apply"] else 0
                await asyncio.sleep(2.0)

            await db.commit()

            # Notify about high-score jobs
            for job in jobs_to_score:
                if (job.ai_score or 0) >= settings.notification_score_threshold:
                    try:
                        await notify_new_job(job.id)
                    except Exception as e:
                        logger.error(f"Notify failed: {e}")

    logger.info(f"Parser run complete (mode={mode})")
    return len(new_job_ids)


def start_scheduler() -> AsyncIOScheduler:
    """Запускает scheduler, но БЕЗ автопарсинга."""
    scheduler = AsyncIOScheduler()

    # Автопарсинг ВЫКЛЮЧЕН — парсинг только вручную через бота
    # Если хочешь вернуть автопарсинг RU раз в 30 минут — раскомментируй:
    # scheduler.add_job(
    #     run_parsers,
    #     "interval",
    #     minutes=30,
    #     kwargs={"mode": "ru"},
    #     id="parse_jobs_ru",
    #     max_instances=1,
    # )

    scheduler.start()
    logger.info("Scheduler started (manual mode)")

    return scheduler