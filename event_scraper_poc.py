#!/usr/bin/env python3
"""
Event Scraper PoC (Refactored)
==============================

Scrapes speaker information by visiting individual detail pages on Athar Festival.

Author: AI Assistant
"""

import logging
import time
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse, urljoin

import pandas as pd
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- DOM Selectors ---
SELECTOR_CARD_LINK = "section.speakers a[href^='/speakers/detail/']"
SELECTOR_DETAIL_CONTAINER = ".detail-content"
SELECTOR_DETAIL_NAME = "h3"
SELECTOR_DETAIL_TITLE_COMPANY = "p" # First <p> after h3

def extract_text(element, selector: str) -> str:
    """Helper to safely extract text from a sub-element."""
    try:
        sub_el = element.query_selector(selector)
        return sub_el.inner_text().strip() if sub_el else ""
    except Exception:
        return ""

def determine_category(url: str) -> str:
    url_lower = url.lower()
    if "speaker" in url_lower:
        return "Speaker"
    elif "exhibitor" in url_lower:
        return "Exhibitor"
    elif "sponsor" in url_lower:
        return "Sponsor"
    return "Other"

def is_decision_maker(job_title: str) -> bool:
    """
    Checks if a job title indicates a decision maker role.
    Looks for: Directors, Management, C-level (CEO, CMO, CIO, CTO, CFO, etc.)
    """
    if not job_title:
        return False
    
    title_lower = job_title.lower()
    
    # C-level keywords
    c_level_keywords = ["ceo", "cmo", "cio", "cto", "cfo", "coo", "chief", "president"]
    
    # Director/Management keywords
    director_keywords = ["director", "managing director", "executive director", "general manager"]
    
    # VP/SVP level
    vp_keywords = ["vice president", "vp", "svp", "evp"]
    
    # Partner/Founder level
    partner_keywords = ["managing partner", "partner", "founder"]
    
    # Head of... (senior leadership roles)
    head_keywords = ["head of"]
    
    # Check for any matches
    all_keywords = c_level_keywords + director_keywords + vp_keywords + partner_keywords + head_keywords
    
    for keyword in all_keywords:
        if keyword in title_lower:
            return True
    
    return False

def split_title_company(text: str):
    """
    Heuristic to split 'CEO, Rotana Media Group' or 'CEO at Rotana'
    """
    if not text:
        return "", ""
    
    # Common separators
    separators = [",", " at ", " - ", "|"]
    
    for sep in separators:
        if sep in text:
            parts = text.split(sep, 1)
            title = parts[0].strip()
            company = parts[1].strip()
            # Clean trailing chars like &
            if company.endswith("&"):
                company = company[:-1].strip()
            return title, company
            
    # Fallback: assume whole string is title, company empty? 
    # Or try to be smart? For now, return as title.
    return text, ""

def fetch_and_parse(url: str, limit: int) -> List[Dict]:
    """
    1. Visits main list
    2. Collects detail URLs
    3. Visits each detail page to extract info
    """
    contacts = []
    
    with sync_playwright() as p:
        logger.info(f"Launching browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        try:
            logger.info(f"Navigating to main list: {url}")
            page.goto(url, timeout=60000, wait_until='domcontentloaded')
            
            # Wait for list
            try:
                page.wait_for_selector(SELECTOR_CARD_LINK, timeout=15000)
            except PlaywrightTimeoutError:
                logger.warning("Timeout waiting for speaker links.")
                
            # Scroll to load more items (lazy loading)
            # We want to collect at least 'limit' links
            links = set()
            max_scrolls = 10
            
            for i in range(max_scrolls):
                elements = page.query_selector_all(SELECTOR_CARD_LINK)
                for el in elements:
                    href = el.get_attribute("href")
                    if href:
                        full_url = urljoin(url, href)
                        links.add(full_url)
                
                if len(links) >= limit:
                    break
                    
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1.5)
                
            logger.info(f"Found {len(links)} detail pages. Visiting first {limit}...")
            
            # Convert to list and slice
            target_links = list(links)[:limit]
            
            event_name = "Athar Festival" # Fallback
            page_title = page.title()
            if "-" in page_title:
                event_name = page_title.split("-")[1].strip()

            # Visit each detail page
            for i, link in enumerate(target_links):
                try:
                    logger.info(f"[{i+1}/{len(target_links)}] Visiting {link}")
                    page.goto(link, timeout=30000, wait_until='domcontentloaded')
                    
                    # Wait for detail content
                    try:
                        page.wait_for_selector(SELECTOR_DETAIL_CONTAINER, timeout=10000)
                    except:
                        logger.warning(f"Could not find content for {link}")
                        continue
                        
                    container = page.query_selector(SELECTOR_DETAIL_CONTAINER)
                    if not container:
                        continue
                        
                    # Extract Name
                    name_el = container.query_selector("h3")
                    name = name_el.inner_text().strip() if name_el else "Unknown"
                    
                    # Extract Title/Company from <p> tags
                    # Logic: Check first 2 paragraphs.
                    # Case A: <p>Title, Company</p>
                    # Case B: <p>Title</p> <p>Company</p>
                    # Case C: <p>Title</p> <div class="agendaDescTxt">...</div> (Company missing/in desc)
                    
                    p_tags = container.query_selector_all("p")
                    raw_text_1 = p_tags[0].inner_text().strip() if len(p_tags) > 0 else ""
                    raw_text_2 = p_tags[1].inner_text().strip() if len(p_tags) > 1 else ""
                    
                    job_title = ""
                    company_name = ""
                    
                    # Heuristic: If 2nd p is short and seemingly a name (not a bio), assume it's company
                    # Bios usually longer than 50 chars
                    if raw_text_2 and len(raw_text_2) < 60 and not " is a " in raw_text_2:
                        job_title = raw_text_1
                        company_name = raw_text_2
                    else:
                        # Fallback to splitting the first line
                        job_title, company_name = split_title_company(raw_text_1)
                        
                        # If split failed (company empty) and we have a second line that MIGHT be company
                        # (even if slightly long, but let's be careful not to grab bio)
                        if not company_name and raw_text_2 and len(raw_text_2) < 100:
                             # Double check it's not a bio start
                             if not any(x in raw_text_2.lower() for x in [" is ", " has ", "joined", "graduated"]):
                                 company_name = raw_text_2

                    # Clean company name
                    if company_name and company_name.endswith("&"):
                         company_name = company_name[:-1].strip()
                    
                    # Basic name split
                    parts = name.split()
                    first_name = parts[0] if parts else ""
                    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
                    
                    # Determine category: Decision Maker takes priority
                    if is_decision_maker(job_title):
                        category = "Decision Maker"
                    else:
                        category = determine_category(url)
                    
                    contact = {
                        "event_name": event_name,
                        "event_url": url,
                        "source_page": link,
                        "person_full_name": name,
                        "first_name": first_name,
                        "last_name": last_name,
                        "job_title": job_title,
                        "company_name": company_name,
                        "country": "",
                        "category": category,
                        "email": "",
                        "phone": "",
                        "linkedin_url": "", # Will be enriched later if enabled
                        "company_website": "",
                        "scraped_at": datetime.now().isoformat()
                    }
                    contacts.append(contact)
                    
                    # Polite delay
                    # time.sleep(0.5) 
                    
                except Exception as e:
                    logger.error(f"Error scraping detail page {link}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Global scraping error: {e}")
            
        finally:
            browser.close()
            
    return contacts

# Keep export function for compatibility
def export_to_excel(data: List[Dict], filename: str, sheet_name: str):
    if not data: return
    df = pd.DataFrame(data)
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
