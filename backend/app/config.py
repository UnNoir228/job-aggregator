from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql+asyncpg://jobagg:jobagg@localhost:5432/jobagg"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    # AI Scoring
    groq_api_key: str
    groq_model: str = "openai/gpt-oss-120b"
    groq_temperature: float = 0.2
    
        # Telegram Bot
    telegram_bot_token: str
    telegram_owner_chat_id: str
    telegram_channels: List[str] = []

    # Каналы по группам
    ru_channels: List[str] = [
        "it_vakansii_jobs",
        "ya_jobs",
        "Getitrussia",
        "alfadigital_jobs",
        "huggabletalents",
        "job_javadevs",
        "forfrontend",
        "mobiledevjob",
        "foranalysts",
        "not_boring_ds_jobs",
    ]
    western_channels: List[str] = [
        "zarubezhom_jobs",
        "pythonjobs",
    ]
    
    # Reddit (optional)
    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_user_agent: str = "JobAggregator/1.0"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Parsing
    parse_interval_minutes: int = 30
    rate_limit_delay: float = 2.0  # seconds between requests
    
    # User profile for AI scoring
    user_stack: List[str] = ["React", "TypeScript", "Python", "aiogram", "FastAPI"]
    user_min_gig_budget: int = 3000
    user_min_job_budget: int = 30000
    user_location: str = "remote"
    
    # Scoring thresholds
    notification_score_threshold: int = 80
    min_display_score: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
