from abc import ABC, abstractmethod
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """Base class for all job parsers."""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.logger = logging.getLogger(f"{__name__}.{source_name}")
    
    @abstractmethod
    async def parse(self) -> List[Dict[str, Any]]:
        """
        Parse jobs from the source.
        
        Returns:
            List of job dictionaries with standardized fields:
            - source: str
            - source_url: str
            - title: str
            - description: str
            - budget: float or None
            - currency: str
            - job_type: str or None
            - stack: List[str]
            - location: str or None
            - posted_at: datetime or None
        """
        pass
    
    def create_job_dict(
        self,
        source_url: str,
        title: str,
        description: str = "",
        budget: float = None,
        currency: str = "RUB",
        job_type: str = None,
        stack: List[str] = None,
        location: str = None,
        posted_at: datetime = None
    ) -> Dict[str, Any]:
        """Create a standardized job dictionary."""
        return {
            "source": self.source_name,
            "source_url": source_url,
            "title": title,
            "description": description or "",
            "budget": budget,
            "currency": currency,
            "job_type": job_type,
            "stack": stack or [],
            "location": location,
            "posted_at": posted_at or datetime.utcnow()
        }
    
    async def safe_parse(self) -> List[Dict[str, Any]]:
        """Parse with error handling."""
        try:
            jobs = await self.parse()
            self.logger.info(f"Parsed {len(jobs)} jobs from {self.source_name}")
            return jobs
        except Exception as e:
            self.logger.error(f"Error parsing {self.source_name}: {str(e)}", exc_info=True)
            return []
