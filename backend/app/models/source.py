from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.models.job import Base


class Source(Base):
    """Source model for tracking job sources and their configuration."""
    
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # kwork | hh | telegram | reddit
    display_name = Column(String(100), nullable=False)
    source_type = Column(String(20), nullable=False)  # api | scraper | telegram
    url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    parse_interval_minutes = Column(Integer, default=30)
    last_parsed_at = Column(DateTime, nullable=True)
    total_jobs_parsed = Column(Integer, default=0)
    config = Column(String(1000), nullable=True)  # JSON string for source-specific config
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<Source(id={self.id}, name='{self.name}', active={self.is_active})>"
