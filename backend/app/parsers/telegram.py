from typing import List, Dict, Any
from datetime import datetime, timedelta
import asyncio
import logging
import re
import tgscraper as tg

from app.parsers.base import BaseParser
from app.config import settings

logger = logging.getLogger(__name__)


class TelegramParser(BaseParser):
    """Parser for public Telegram channels using telegram-channel-scraper."""

    def __init__(self, channels: list = None):
        super().__init__("telegram")
        self.channels = channels or settings.telegram_channels or [
            "freelance_tasks",
            "python_jobs",
            "web_projects",
        ]

    async def parse(self) -> List[Dict[str, Any]]:
        jobs = []
        for channel in self.channels:
            try:
                channel_name = channel.lstrip("@").replace("https://t.me/", "")
                logger.info(f"Scraping channel: {channel_name}")

                loop = asyncio.get_event_loop()
                posts = await loop.run_in_executor(
                    None,
                    lambda: tg.scrape(channel_name, limit=20)
                )

                fresh_count = 0
                for post in posts:
                    job = self._parse_post(post, channel_name)
                    if job:
                        jobs.append(job)
                        fresh_count += 1

                logger.info(f"Parsed {len(posts)} posts from {channel_name}, {fresh_count} fresh matches")
                await asyncio.sleep(settings.rate_limit_delay)

            except Exception as e:
                logger.error(f"Error scraping channel {channel}: {str(e)}")
                continue

        return jobs

    def _parse_post(self, post, channel):
        try:
            posted_at = datetime.utcnow()
            date_str = post.date if hasattr(post, 'date') else post.get("date")
            if date_str:
                try:
                    if isinstance(date_str, datetime):
                        posted_at = date_str.replace(tzinfo=None)
                    else:
                        posted_at = datetime.fromisoformat(
                            str(date_str).replace("Z", "+00:00")
                        ).replace(tzinfo=None)
                except (ValueError, AttributeError):
                    pass

            age = datetime.utcnow() - posted_at
            if age > timedelta(days=30):
                return None

            text = post.text if hasattr(post, 'text') else post.get("text", "")
            if not text or len(text) < 50:
                return None

            job_keywords = ["заказ", "проект", "вакансия", "ищу", "требуется",
                            "нужен", "freelance", "job", "hiring"]
            if not any(kw in text.lower() for kw in job_keywords):
                return None

            lines = text.split("\n")
            title = lines[0].strip()[:100]

            budget = None
            currency = "RUB"
            patterns = [
                (r'(\d+[\s\xa0]*(?:000|к|k)?)[\s\xa0]*(?:руб|₽|rub)', "RUB"),
                (r'\$[\s\xa0]*(\d+)', "USD"),
                (r'(\d+)[\s\xa0]*(?:тыс|тысяч)', "RUB"),
            ]
            for pattern, curr in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    budget_str = match.group(1).replace(" ", "").replace("\xa0", "")
                    budget_str = budget_str.replace("к", "000").replace("k", "000")
                    try:
                        budget = float(budget_str)
                        if "тыс" in text.lower() or "тысяч" in text.lower():
                            budget *= 1000
                        currency = curr
                        break
                    except ValueError:
                        pass

            source_url = post.url if hasattr(post, 'url') else post.get("url", f"https://t.me/{channel}")

            return self.create_job_dict(
                source_url=source_url,
                title=title,
                description=text,
                budget=budget,
                currency=currency,
                job_type=None,
                stack=[],
                location="remote",
                posted_at=posted_at,
            )

        except Exception as e:
            logger.error(f"Error parsing post: {str(e)}")
            return None