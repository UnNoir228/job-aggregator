from typing import List, Dict, Any
from datetime import datetime
import asyncio
from app.parsers.base import BaseParser
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class KworkParser(BaseParser):
    """Parser for kwork.ru using Playwright."""
    
    def __init__(self):
        super().__init__("kwork")
        self.base_url = "https://kwork.ru/projects"
    
    async def parse(self) -> List[Dict[str, Any]]:
        """Parse gigs from kwork.ru."""
        jobs = []
        
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                page = await context.new_page()
                
                # Categories to search
                categories = [
                    "?c=41",  # Programming
                    "?c=42",  # Websites
                    "?c=11",  # Scripts & Bots
                ]
                
                for category in categories:
                    try:
                        url = f"{self.base_url}{category}"
                        await page.goto(url, wait_until="networkidle", timeout=30000)
                        await asyncio.sleep(2)
                        
                        # Parse project cards
                        cards = await page.query_selector_all(".project-card, .wants-card, [data-project-id]")
                        
                        for card in cards[:10]:  # Limit to 10 per category
                            try:
                                job = await self._parse_card(card, page)
                                if job:
                                    jobs.append(job)
                                    await asyncio.sleep(0.5)
                            except Exception as e:
                                self.logger.error(f"Error parsing card: {str(e)}")
                                continue
                        
                        self.logger.info(f"Parsed category {category}: {len(cards)} cards")
                        await asyncio.sleep(settings.rate_limit_delay)
                        
                    except Exception as e:
                        self.logger.error(f"Error loading category {category}: {str(e)}")
                        continue
                
                await browser.close()
                
        except ImportError:
            self.logger.error("Playwright not installed. Install with: pip install playwright && playwright install")
            return []
        except Exception as e:
            self.logger.error(f"Error in KworkParser: {str(e)}")
            return []
        
        return jobs
    
    async def _parse_card(self, card, page) -> Dict[str, Any]:
        """Parse individual project card."""
        try:
            # Extract title
            title_elem = await card.query_selector(".wants-card__header-title, .project-card__title, h3")
            title = await title_elem.inner_text() if title_elem else "No title"
            title = title.strip()
            
            # Extract description
            desc_elem = await card.query_selector(".wants-card__description, .project-card__description, .description")
            description = await desc_elem.inner_text() if desc_elem else ""
            description = description.strip()
            
            # Extract budget
            budget = None
            price_elem = await card.query_selector(".wants-card__price, .project-card__price, .price")
            if price_elem:
                price_text = await price_elem.inner_text()
                # Extract number from text like "5000 ₽" or "5 000 руб"
                import re
                numbers = re.findall(r'[\d\s]+', price_text)
                if numbers:
                    budget_str = numbers[0].replace(" ", "").replace("\xa0", "")
                    try:
                        budget = float(budget_str)
                    except:
                        pass
            
            # Extract URL
            link_elem = await card.query_selector("a[href*='/projects/'], a[href*='/wants/']")
            relative_url = await link_elem.get_attribute("href") if link_elem else None
            source_url = f"https://kwork.ru{relative_url}" if relative_url else self.base_url
            
            # Check if it's a unique URL
            if not relative_url or relative_url == "#":
                return None
            
            return self.create_job_dict(
                source_url=source_url,
                title=title,
                description=description,
                budget=budget,
                currency="RUB",
                job_type="gig",
                stack=[],  # Will be extracted by normalizer
                location="remote",
                posted_at=datetime.utcnow()
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing kwork card: {str(e)}")
            return None
