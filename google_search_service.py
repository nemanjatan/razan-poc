import logging
from typing import Optional
from serpapi import GoogleSearch

logger = logging.getLogger(__name__)

# SerpAPI Key (hardcoded as requested)
SERPAPI_KEY = "a56127f5ab6c83ea01714dc7ada944ba71de777d4f03f466f7a825d711f193fa"

def google_search_linkedin(name: str, company: str, title: str) -> str:
    """
    Uses SerpAPI to find a LinkedIn profile.
    """
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
