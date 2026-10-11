from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import settings
from app.database import init_db, close_db
from app.api.router import api_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Job Aggregator...")
    await init_db()
    logger.info("Database initialized")

    # Start Telegram bot in background
    from app.bot.telegram_bot import start_bot
    import asyncio
    bot_task = asyncio.create_task(start_bot())

    # Start scheduler
    from app.tasks.scheduler import start_scheduler
    scheduler = start_scheduler()

    yield

    logger.info("Shutting down...")
    scheduler.shutdown()
    bot_task.cancel()
    await close_db()


app = FastAPI(
    title="Job Aggregator API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    return {"service": "job-aggregator", "status": "ok", "docs": "/docs"}