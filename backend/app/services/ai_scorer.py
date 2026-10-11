from typing import Dict, Any, Optional
import httpx
import json
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class AIScorer:
    """Service for scoring jobs using Groq AI API."""
    
    def __init__(self):
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.api_key = settings.groq_api_key
        self.model = settings.groq_model
        self.temperature = settings.groq_temperature
    
    async def score_job(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score a job using AI.
        
        Args:
            job_data: Job dictionary with title, description, budget, etc.
            
        Returns:
            Dictionary with keys: score (int 0-100), reason (str), should_apply (bool)
        """
        try:
            prompt = self._build_prompt(job_data)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "system",
                                "content": self._get_system_prompt()
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": self.temperature,
                        "max_tokens": 500,
                        "response_format": {"type": "json_object"}
                    }
                )
                
                response.raise_for_status()
                data = response.json()
                
                # Parse AI response
                content = data["choices"][0]["message"]["content"]
                result = json.loads(content)
                
                return {
                    "score": int(result.get("score", 0)),
                    "reason": result.get("reason", "No reason provided"),
                    "should_apply": bool(result.get("should_apply", False))
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Groq API HTTP error: {e.response.status_code} - {e.response.text}")
            return self._default_score()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {str(e)}")
            return self._default_score()
        except Exception as e:
            logger.error(f"Error scoring job with AI: {str(e)}")
            return self._default_score()
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for AI scoring."""
        stack_str = ", ".join(settings.user_stack)
        
        return f"""You are an assistant helping a junior developer find suitable work opportunities.

Developer Profile:
- Stack: {stack_str}
- Looking for: Freelance gigs (parsing, bots, landing pages) or junior positions
- Budget expectations: 
  - Gigs: from {settings.user_min_gig_budget} RUB
  - Full-time: from {settings.user_min_job_budget} RUB/month
- Location: {settings.user_location}

Evaluate job postings and return a JSON response with:
{{
  "score": <0-100>,
  "reason": "<1-2 sentence explanation>",
  "should_apply": <true/false>
}}

Scoring criteria (total 100 points):
- Stack relevance (0-60): MUST include React, TypeScript, JavaScript, Python, or FastAPI. If NO match → score 0-10.
- Junior-friendly (0-20): Explicitly junior/middle/intern. If senior/lead → score 0-5.
- Budget (0-15): Adequate compensation. If no budget info → score 5.
- Urgency/freshness (0-5): Recent.

CRITICAL RULES:
- If posting is NOT a job (article, ad, announcement, digest) → score 0-5.
- If stack is Java/Go/C++/PHP/1C/DevOps/Analytics without Python/React → score 0-10.
- If title is vague ("Что-то вкусное", "Возможностей удаленки не счесть") → score 0-5.

Be honest and concise. Return only valid JSON."""
    
    def _build_prompt(self, job_data: Dict[str, Any]) -> str:
        """Build the user prompt for a specific job."""
        title = job_data.get("title", "No title")
        description = job_data.get("description", "No description")[:1000]  # Limit length
        budget = job_data.get("budget")
        currency = job_data.get("currency", "RUB")
        source = job_data.get("source", "unknown")
        job_type = job_data.get("job_type", "unknown")
        stack = job_data.get("stack", [])
        
        budget_str = f"{budget} {currency}" if budget else "Not specified"
        stack_str = ", ".join(stack) if stack else "Not specified"
        
        return f"""Evaluate this job posting:

Title: {title}

Description: {description}

Budget: {budget_str}
Type: {job_type}
Source: {source}
Stack detected: {stack_str}

Provide your evaluation in JSON format."""
    
    def _default_score(self) -> Dict[str, Any]:
        """Return default score when AI scoring fails."""
        return {
            "score": 50,
            "reason": "Unable to score with AI, default score assigned",
            "should_apply": False
        }
    
    async def batch_score_jobs(self, jobs: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """
        Score multiple jobs (with rate limiting).
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            List of scored jobs with ai_score, ai_reason, should_apply fields
        """
        import asyncio
        
        scored_jobs = []
        
        for i, job in enumerate(jobs):
            try:
                score_result = await self.score_job(job)
                job["ai_score"] = score_result["score"]
                job["ai_reason"] = score_result["reason"]
                job["should_apply"] = 1 if score_result["should_apply"] else 0
                scored_jobs.append(job)
                
                # Rate limiting: delay between requests
                if i < len(jobs) - 1:
                    await asyncio.sleep(1.0)
                    
            except Exception as e:
                logger.error(f"Error scoring job {job.get('title', '')}: {str(e)}")
                job["ai_score"] = 50
                job["ai_reason"] = "Scoring failed"
                job["should_apply"] = 0
                scored_jobs.append(job)
        
        return scored_jobs


ai_scorer = AIScorer()
