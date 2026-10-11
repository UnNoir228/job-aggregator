from sqlalchemy import Column, Integer, String, DateTime, func, JSON
from app.models.job import Base


class User(Base):
    """User model for storing user preferences and filters."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String(50), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    is_active = Column(Integer, default=1)  # 0 or 1
    
    # User preferences
    min_score = Column(Integer, default=70)
    preferred_sources = Column(JSON, default=list)  # ["kwork", "hh"]
    preferred_stack = Column(JSON, default=list)  # ["react", "python"]
    min_budget = Column(Integer, default=3000)
    max_budget = Column(Integer, nullable=True)
    preferred_job_types = Column(JSON, default=list)  # ["gig", "job"]
    notification_enabled = Column(Integer, default=1)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id='{self.telegram_id}', username='{self.username}')>"
