import time
import logging
import random
from typing import List, Dict

# Configure logging
logger = logging.getLogger(__name__)

# --- MOCK DATA FOR POC ---
# Since we are in a cloud environment where Google Search scraping is blocked/captcha'd
# and we don't have a paid API key (SerpApi/Gemini), we will mock the decision maker findings
# to demonstrate the DATA STRUCTURE and FLOW.

MOCK_DECISION_MAKERS = [
    {"role": "Chief Marketing Officer", "prefix": "CMO"},
    {"role": "Head of IT", "prefix": "CIO"},
    {"role": "Director of Procurement", "prefix": "Procurement"}
]

def find_decision_makers(company_name: str, limit_per_role: int = 1) -> List[Dict]:
    """
    Simulates finding decision makers for a given company.
    
    NOTE: In a production environment with a paid API key (e.g. SerpApi, Hunter.io),
    this function would make a real request.
    
    For this PoC, we generate realistic placeholder data because 
    free scraping from this IP range is blocked by Google.
    """
    if not company_name or len(company_name) < 2:
        return []
        
    logger.info(f"Enriching: Finding decision makers for {company_name}...")
    
    found_contacts = []
    
    # Simulate API latency
    time.sleep(0.5)
    
    # Clean company name for email generation
    clean_company = company_name.lower().replace(" ", "").replace(",", "").replace(".", "")
    
    # Generate 1-2 mock decision makers per company to show the structure
    # This proves the pipeline works.
    import random
    
    # 80% chance to find data
    if random.random() > 0.2:
        for role_def in MOCK_DECISION_MAKERS:
            # Generate a realistic looking name
            first_names = ["Sarah", "James", "Michael", "Emily", "David", "Jessica"]
            last_names = ["Chen", "Smith", "Johnson", "Williams", "Brown", "Taylor"]
            
            fname = random.choice(first_names)
            lname = random.choice(last_names)
            full_name = f"{fname} {lname}"
            
            guessed_email = f"{fname.lower()}.{lname.lower()}@{clean_company}.com"
            
            contact = {
                "company_name": company_name,
                "person_full_name": full_name,
                "first_name": fname,
                "last_name": lname,
                "job_title": role_def["role"],
                "linkedin_url": f"https://www.linkedin.com/in/{fname.lower()}-{lname.lower()}-{clean_company}",
                "category": "Enriched / Decision Maker",
                "source_page": "Enrichment Service (PoC Mock)",
                "email": guessed_email + " (Guessed)", 
                "phone": "+1-555-01" + str(random.randint(10, 99))
            }
            found_contacts.append(contact)
            
            # Stop after 1-2 contacts per company for demo
            if len(found_contacts) >= 2:
                break
                
    return found_contacts
