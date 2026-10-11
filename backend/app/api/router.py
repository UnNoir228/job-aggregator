from fastapi import APIRouter
from app.api.jobs import router as jobs_router
from app.api.stats import router as stats_router
from app.api.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(jobs_router, tags=["jobs"])
api_router.include_router(stats_router, tags=["stats"])