import hashlib
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class Deduplicator:
    """Service for detecting duplicate jobs."""
    
    def calculate_hash(self, job_data: Dict[str, Any]) -> str:
        """
        Calculate SHA256 hash for job to detect duplicates.
        
        Uses: title + first 200 chars of description + budget
        
        Args:
            job_data: Job dictionary
            
        Returns:
            64-character hex string (SHA256 hash)
        """
        title = job_data.get("title", "").strip().lower()
        description = job_data.get("description", "").strip().lower()[:200]
        budget = str(job_data.get("budget", "")).strip()
        source_url = job_data.get("source_url", "").strip().lower()
        
        # Primary hash: based on content
        hash_string = f"{title}|{description}|{budget}"
        content_hash = hashlib.sha256(hash_string.encode()).hexdigest()
        
        # If we have a unique source URL, use it for better deduplication
        if source_url and source_url != "":
            url_hash = hashlib.sha256(source_url.encode()).hexdigest()
            # Combine both hashes
            final_hash = hashlib.sha256(f"{content_hash}{url_hash}".encode()).hexdigest()
            return final_hash
        
        return content_hash
    
    def is_similar(self, text1: str, text2: str, threshold: float = 0.8) -> bool:
        """
        Check if two texts are similar using simple word overlap.
        
        Args:
            text1: First text
            text2: Second text
            threshold: Similarity threshold (0.0 to 1.0)
            
        Returns:
            True if texts are similar
        """
        if not text1 or not text2:
            return False
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return False
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        similarity = intersection / union if union > 0 else 0
        
        return similarity >= threshold
    
    def find_duplicates(self, jobs: list[Dict[str, Any]]) -> list[tuple[int, int]]:
        """
        Find duplicate jobs in a list.
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            List of tuples (index1, index2) indicating duplicates
        """
        duplicates = []
        
        for i in range(len(jobs)):
            for j in range(i + 1, len(jobs)):
                title1 = jobs[i].get("title", "")
                title2 = jobs[j].get("title", "")
                
                if self.is_similar(title1, title2, threshold=0.7):
                    duplicates.append((i, j))
                    logger.debug(f"Found duplicate: '{title1[:50]}' vs '{title2[:50]}'")
        
        return duplicates
    
    def remove_duplicates(self, jobs: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """
        Remove duplicate jobs from list, keeping first occurrence.
        
        Args:
            jobs: List of job dictionaries
            
        Returns:
            List of unique jobs
        """
        seen_hashes = set()
        unique_jobs = []
        
        for job in jobs:
            job_hash = self.calculate_hash(job)
            if job_hash not in seen_hashes:
                seen_hashes.add(job_hash)
                unique_jobs.append(job)
            else:
                logger.debug(f"Skipping duplicate: {job.get('title', '')[:50]}")
        
        logger.info(f"Removed {len(jobs) - len(unique_jobs)} duplicates from {len(jobs)} jobs")
        return unique_jobs


deduplicator = Deduplicator()
