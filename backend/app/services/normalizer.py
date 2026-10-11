from typing import Dict, Any, List
import re
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class Normalizer:
    """Service for normalizing parsed jobs to standard format."""
    
    # Technology keywords for stack extraction
    TECH_KEYWORDS = {
        "python": ["python", "django", "flask", "fastapi", "asyncio", "пайтон"],
        "javascript": ["javascript", "js", "node", "nodejs", "джаваскрипт"],
        "typescript": ["typescript", "ts"],
        "react": ["react", "reactjs", "react.js", "реакт"],
        "vue": ["vue", "vuejs", "vue.js"],
        "angular": ["angular"],
        "next": ["next.js", "nextjs", "next"],
        "nuxt": ["nuxt.js", "nuxtjs", "nuxt"],
        "php": ["php"],
        "java": ["java", "spring"],
        "go": ["golang", "go"],
        "rust": ["rust"],
        "docker": ["docker", "докер"],
        "kubernetes": ["kubernetes", "k8s"],
        "postgresql": ["postgres", "postgresql"],
        "mysql": ["mysql"],
        "mongodb": ["mongodb", "mongo"],
        "redis": ["redis"],
        "aws": ["aws", "amazon web services"],
        "gcp": ["gcp", "google cloud"],
        "telegram": ["telegram", "telethon", "aiogram", "телеграм"],
        "bot": ["bot", "бот", "чат-бот", "chatbot"],
        "parse": ["парсинг", "parsing", "scraping", "парсер"],
        "html": ["html", "html5"],
        "css": ["css", "css3", "tailwind", "bootstrap"],
        "api": ["api", "rest", "graphql"],
        "ml": ["machine learning", "ml", "ai", "pytorch", "tensorflow"],
    }
    
    # Job type keywords
    GIG_KEYWORDS = [
        "заказ", "проект", "разовая работа", "фриланс", "freelance", 
        "нужен исполнитель", "ищу специалиста", "сделать", "разработать"
    ]
    
    JOB_KEYWORDS = [
        "вакансия", "vacancy", "работа", "должность", "в команду", 
        "на постоянной основе", "full-time", "part-time", "офис", "удаленная работа"
    ]
    
    # Location keywords
    REMOTE_KEYWORDS = ["remote", "удаленно", "удаленная", "remotely", "anywhere"]
    
    def normalize(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize job data: extract stack, determine job_type, normalize location.
        
        Args:
            job_data: Raw job dictionary from parser
            
        Returns:
            Normalized job dictionary
        """
        normalized = job_data.copy()
        
        # Extract stack from title and description
        if not normalized.get("stack"):
            normalized["stack"] = self._extract_stack(
                normalized.get("title", ""),
                normalized.get("description", "")
            )
        
        # Determine job type if not set
        if not normalized.get("job_type"):
            normalized["job_type"] = self._determine_job_type(
                normalized.get("title", ""),
                normalized.get("description", ""),
                normalized.get("source", "")
            )
        
        # Normalize location
        normalized["location"] = self._normalize_location(normalized.get("location", ""))
        
        # Normalize currency and budget
        if normalized.get("budget") and normalized.get("currency"):
            normalized["budget"], normalized["currency"] = self._normalize_budget(
                normalized["budget"],
                normalized["currency"]
            )
        
        return normalized
    
    def _extract_stack(self, title: str, description: str) -> List[str]:
        """Extract technology stack from text."""
        text = f"{title} {description}".lower()
        stack = []
        
        for tech, keywords in self.TECH_KEYWORDS.items():
            for keyword in keywords:
                if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', text):
                    stack.append(tech)
                    break
        
        return list(set(stack))  # Remove duplicates
    
    def _determine_job_type(self, title: str, description: str, source: str) -> str:
        """Determine if it's a gig or full-time job."""
        text = f"{title} {description}".lower()
        
        # Source-based heuristics
        if source == "kwork":
            return "gig"
        
        # Keyword-based detection
        gig_score = sum(1 for kw in self.GIG_KEYWORDS if kw in text)
        job_score = sum(1 for kw in self.JOB_KEYWORDS if kw in text)
        
        if gig_score > job_score:
            return "gig"
        elif job_score > gig_score:
            return "job"
        
        # Default based on source
        if source in ["hh", "habr"]:
            return "job"
        
        return "gig"
    
    def _normalize_location(self, location: str) -> str:
        """Normalize location string."""
        if not location:
            return "remote"
        
        location_lower = location.lower()
        
        # Check for remote keywords
        if any(kw in location_lower for kw in self.REMOTE_KEYWORDS):
            return "remote"
        
        # Common cities
        city_map = {
            "москва": "moscow",
            "moscow": "moscow",
            "санкт-петербург": "spb",
            "petersburg": "spb",
            "спб": "spb",
            "екатеринбург": "ekaterinburg",
            "новосибирск": "novosibirsk",
        }
        
        for key, value in city_map.items():
            if key in location_lower:
                return value
        
        return location.lower()
    
    def _normalize_budget(self, budget: float, currency: str) -> tuple:
        """Normalize budget to single currency (RUB)."""
        if not budget:
            return None, "RUB"
        
        # Convert to RUB
        exchange_rates = {
            "RUB": 1.0,
            "USD": 95.0,
            "EUR": 105.0,
            "UAH": 2.5,
            "KZT": 0.2,
        }
        
        rate = exchange_rates.get(currency.upper(), 1.0)
        normalized_budget = float(budget) * rate
        
        return normalized_budget, "RUB"


normalizer = Normalizer()
