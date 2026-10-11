from typing import List, Dict, Any
from datetime import datetime
import httpx
import asyncio
from app.parsers.base import BaseParser
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class HhParser(BaseParser):
    """Parser for hh.ru API."""
    
    def __init__(self):
        super().__init__("hh")
        self.api_url = "https://api.hh.ru/vacancies"
        self.headers = {
            "User-Agent": "JobAggregator/1.0 (gradfor13@gmail.com)"
        }
    
    async def parse(self) -> List[Dict[str, Any]]:
        """Parse jobs from hh.ru API."""
        jobs = []
        
        # Search parameters for junior developer positions
        search_params = [
            {"text": "junior python", "per_page": 20},
            {"text": "junior react", "per_page": 20},
            {"text": "junior typescript", "per_page": 20},
            {"text": "python remote", "per_page": 20},
        ]
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for params in search_params:
                try:
                    await asyncio.sleep(settings.rate_limit_delay)
                    
                    response = await client.get(
                        self.api_url,
                        params=params,
                        headers=self.headers
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    for item in data.get("items", []):
                        job = await self._parse_vacancy(item)
                        if job:
                            jobs.append(job)
                    
                    self.logger.info(f"Parsed {len(data.get('items', []))} jobs for query: {params.get('text')}")
                    
                except Exception as e:
                    self.logger.error(f"Error parsing hh.ru with params {params}: {str(e)}")
                    continue
        
        # Remove duplicates by URL
        unique_jobs = {job["source_url"]: job for job in jobs}
        return list(unique_jobs.values())
    
    async def _parse_vacancy(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Parse individual vacancy from API response."""
        try:
            # Extract salary
            salary = item.get("salary")
            budget = None
            currency = "RUB"
            
            if salary:
                if salary.get("from"):
                    budget = float(salary["from"])
                elif salary.get("to"):
                    budget = float(salary["to"])
                currency = salary.get("currency", "RUB")
            
            # Extract location
            location = "remote"
            area = item.get("area", {})
            if area:
                location = area.get("name", "remote")
            
            # Check if remote
            schedule = item.get("schedule", {})
            if schedule and schedule.get("id") == "remote":
                location = "remote"
            
            # Extract posted date
            posted_at = None
            published_at = item.get("published_at")
            if published_at:
                try:
                    posted_at = datetime.fromisoformat(published_at.replace("Z", "+00:00")).replace(tzinfo=None)
                except Exception:
                    posted_at = datetime.utcnow()
            
            # Extract snippet as description
            snippet = item.get("snippet", {})
            description = f"{snippet.get('requirement', '')} {snippet.get('responsibility', '')}"
            
            return self.create_job_dict(
                source_url=item.get("alternate_url", item.get("url", "")),
                title=item.get("name", ""),
                description=description.strip(),
                budget=budget,
                currency=currency,
                job_type="job",
                stack=[],  # Will be extracted by normalizer
                location=location,
                posted_at=posted_at
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing vacancy: {str(e)}")
            return None
