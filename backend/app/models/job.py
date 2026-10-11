from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ARRAY, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Job(Base):
    """Job model for storing parsed job listings and gigs."""
    
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), nullable=False, index=True)  # kwork | hh | telegram | reddit
    source_url = Column(String(500), unique=True, nullable=False)
    title = Column(String(300), nullable=False)
    description = Column(Text)
    budget = Column(Numeric(10, 2), nullable=True)
    currency = Column(String(3), default="RUB")
    job_type = Column(String(20), index=True)  # gig | job
    stack = Column(ARRAY(String), default=list)
    location = Column(String(100))
    posted_at = Column(DateTime, nullable=True)
    raw_hash = Column(String(64), unique=True, nullable=False, index=True)
    ai_score = Column(Integer, nullable=True, index=True)  # 0-100
    ai_reason = Column(Text, nullable=True)
    should_apply = Column(Integer, default=0)  # 0 or 1 (boolean)
    status = Column(String(20), default="new", index=True)  # new | seen | applied | rejected
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, title='{self.title[:30]}...', source='{self.source}', score={self.ai_score})>"
