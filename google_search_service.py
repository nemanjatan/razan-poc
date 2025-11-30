import logging
import os
from typing import Optional
from dotenv import load_dotenv
from serpapi import GoogleSearch

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# SerpAPI Key from environment variable
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

def google_search_linkedin(name: str, company: str, title: str) -> str:
    """
    Uses SerpAPI to find a LinkedIn profile.
    """
    if not SERPAPI_KEY:
        logger.error("SERPAPI_KEY not found in environment variables")
        return ""
        
    if not name:
        return ""
        
    # Construct query: Name Title Company + site:linkedin.com/in/
    query = f"{name} {title} {company} site:linkedin.com/in/"
    
    try:
        params = {
            "q": query,
            "api_key": SERPAPI_KEY,
            "num": 10,  # Request up to 10 results
            "hl": "en",  # Language
            "gl": "us"   # Country
        }
        
        logger.info(f"SerpAPI search for: {query}")
        
        search = GoogleSearch(params)
        results_dict = search.get_dict()
        
        # Check for errors
        if "error" in results_dict:
            logger.error(f"SerpAPI error: {results_dict['error']}")
            return ""
        
        # Extract organic results
        organic_results = results_dict.get("organic_results", [])
        
        if not organic_results:
            logger.info("No results found")
            return ""
        
        # Look for LinkedIn profile URLs
        for result in organic_results:
            link = result.get("link", "")
            # Verify it's a profile URL (not a post or company page)
            if "linkedin.com/in/" in link:
                logger.info(f"Found LinkedIn: {link}")
                return link
        
        logger.info("No LinkedIn profiles found in results")
        return ""
        
    except Exception as e:
        logger.error(f"SerpAPI search error for {name}: {e}")
        return ""
