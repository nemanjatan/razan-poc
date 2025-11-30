import logging
import json
import time
import re
from typing import List, Dict, Optional

from google import genai
from google.genai.types import (
    GenerateContentConfig,
    GoogleSearch,
    Tool,
    HttpOptions
)

# Configure logging
logger = logging.getLogger(__name__)

class GeminiEnrichmentService:
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("Gemini API Key is required")
        
        # Initialize Client using the new SDK standard
        # v1alpha is often required for experimental grounding features in google-genai SDK
        # but the user requested 'v1' in the prompt snippet. We'll use v1 as requested.
        self.client = genai.Client(
            api_key=api_key,
            http_options=HttpOptions(api_version="v1alpha") # Grounding often requires alpha/beta in this new SDK
        )
        
        self.model_name = "gemini-2.0-flash-exp" 
        
        # Configure Tools using the new typed objects
        self.tools = [
            Tool(
                google_search=GoogleSearch()
            )
        ]

    def find_speaker_linkedin(self, name: str, company: str, title: str) -> str:
        """
        Finds the specific LinkedIn profile for the speaker.
        """
        if not name:
            return ""
            
        prompt = f"""
        Perform a Google Search to find the LinkedIn profile for:
        Name: {name}
        Role: {title}
        Organization: {company}
        
        Task: Return the most likely LinkedIn public profile URL.
        
        Rules:
        1. If you find a likely match in the search results, return JUST the URL.
        2. If multiple exist, return the one that matches the Role/Organization best.
        3. Do not be overly cautious. If a profile looks correct (same name + same/similar company), return it.
        4. Output format: Just the URL string (e.g. https://www.linkedin.com/in/username).
        """
        
        try:
            logger.info(f"Prompt: {prompt}")
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=GenerateContentConfig(
                    tools=self.tools,
                    temperature=0.1 # Low temp for factual extraction
                )
            )
            
            text = response.text if response.text else ""
            logger.info(f"Response: {text}")
            
            # 1. Direct match check
            clean_text = text.strip()
            if clean_text.startswith("http") and "linkedin.com/in/" in clean_text:
                return clean_text.split()[0] # Return first token if it's a URL
                
            # 2. Regex Extraction (fallback if model chats)
            # Looks for https://[www.]linkedin.com/in/[slug]
            match = re.search(r'(https?://(www\.)?linkedin\.com/in/[a-zA-Z0-9%\-_]+)', text)
            if match:
                return match.group(1)
                
            return ""
        except Exception as e:
            logger.error(f"Error finding LinkedIn for {name}: {e}")
            return ""

    def find_decision_makers(self, company_name: str, location: str = "United States") -> List[Dict]:
        """
        Uses Gemini with Google Search Grounding to find decision makers.
        """
        if not company_name:
            return []

        prompt = f"""
        Research the company "{company_name}".
        Find 5 key decision makers (Marketing, IT, Procurement, Management).
        Also find company details (Website, Phone, Address, LinkedIn Page).
        
        Format as JSON:
        {{
            "company_name": "...",
            "website": "...",
            "linkedin_url": "...",
            "phone_number": "...",
            "address": {{ "street": "...", "city": "...", "country": "..." }},
            "decision_makers": [
                {{ "full_name": "...", "job_title": "...", "linkedin_url": "..." }}
            ]
        }}
        """

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=GenerateContentConfig(
                    tools=self.tools,
                    temperature=0.1
                )
            )
            
            text_content = response.text
            if not text_content:
                return []
                
            text_content = text_content.replace("```json", "").replace("```", "").strip()
            data = json.loads(text_content)
            
            results = []
            company_info = {
                "company_website": data.get("website", ""),
                "company_phone": data.get("phone_number", ""),
                "company_linkedin": data.get("linkedin_url", ""),
                "company_address": json.dumps(data.get("address", {}))
            }
            
            for dm in data.get("decision_makers", []):
                contact = {
                    "company_name": data.get("company_name", company_name),
                    "person_full_name": dm.get("full_name"),
                    "job_title": dm.get("job_title"),
                    "linkedin_url": dm.get("linkedin_url"),
                    "category": "Enriched / Decision Maker",
                    "source_page": "Gemini Search",
                    "email": "",
                    "phone": company_info["company_phone"],
                    "company_website": company_info["company_website"],
                    "first_name": dm.get("full_name", "").split(" ")[0] if dm.get("full_name") else "",
                    "last_name": " ".join(dm.get("full_name", "").split(" ")[1:]) if dm.get("full_name") else ""
                }
                results.append(contact)
            return results

        except Exception as e:
            logger.error(f"Gemini Enrichment Failed for {company_name}: {e}")
            return []

# Helper functions for existing code compatibility
def find_decision_makers_gemini(company_name: str, api_key: str) -> List[Dict]:
    service = GeminiEnrichmentService(api_key)
    return service.find_decision_makers(company_name)

def find_speaker_linkedin_gemini(name: str, company: str, title: str, api_key: str) -> str:
    service = GeminiEnrichmentService(api_key)
    return service.find_speaker_linkedin(name, company, title)
