import logging
import os
from typing import Optional, Dict
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

def find_company_details(company_name: str) -> Dict[str, str]:
    """
    Uses SerpAPI to find company details:
    - Website domain
    - LinkedIn company page
    - City and Country (headquarters location)
    """
    if not SERPAPI_KEY or not company_name:
        return {
            "website": "",
            "linkedin": "",
            "city": "",
            "country": ""
        }
    
    results = {
        "website": "",
        "linkedin": "",
        "city": "",
        "country": ""
    }
    
    try:
        # Search 1: Company website
        query1 = f'"{company_name}" official website'
        params1 = {
            "q": query1,
            "api_key": SERPAPI_KEY,
            "num": 5,
            "hl": "en",
            "gl": "us"
        }
        
        search1 = GoogleSearch(params1)
        results1 = search1.get_dict()
        
        if "organic_results" in results1:
            for item in results1["organic_results"][:3]:
                link = item.get("link", "")
                # Look for company website (not LinkedIn, not social media)
                if link and "linkedin.com" not in link and "facebook.com" not in link and "twitter.com" not in link:
                    # Extract domain
                    from urllib.parse import urlparse
                    domain = urlparse(link).netloc.replace("www.", "")
                    if domain:
                        results["website"] = domain
                        break
        
        # Search 2: Company LinkedIn page
        query2 = f'"{company_name}" site:linkedin.com/company'
        params2 = {
            "q": query2,
            "api_key": SERPAPI_KEY,
            "num": 5,
            "hl": "en",
            "gl": "us"
        }
        
        search2 = GoogleSearch(params2)
        results2 = search2.get_dict()
        
        if "organic_results" in results2:
            for item in results2["organic_results"]:
                link = item.get("link", "")
                if "linkedin.com/company" in link:
                    results["linkedin"] = link
                    break
        
        # Search 3: Company location/headquarters
        query3 = f'"{company_name}" headquarters location city country'
        params3 = {
            "q": query3,
            "api_key": SERPAPI_KEY,
            "num": 3,
            "hl": "en",
            "gl": "us"
        }
        
        search3 = GoogleSearch(params3)
        results3 = search3.get_dict()
        
        # Try to extract location from snippets
        if "organic_results" in results3:
            for item in results3["organic_results"]:
                snippet = item.get("snippet", "").lower()
                title = item.get("title", "").lower()
                combined = f"{title} {snippet}"
                
                # Look for common city/country patterns
                # This is basic - could be enhanced with NLP
                cities = ["dubai", "riyadh", "jeddah", "cairo", "london", "new york", "san francisco"]
                countries = ["uae", "saudi arabia", "egypt", "uk", "usa", "united states", "united kingdom"]
                
                for city in cities:
                    if city in combined:
                        results["city"] = city.title()
                        break
                
                for country in countries:
                    if country in combined:
                        results["country"] = country.title()
                        break
                
                if results["city"] or results["country"]:
                    break
        
        logger.info(f"Company details for {company_name}: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error finding company details for {company_name}: {e}")
        return results
