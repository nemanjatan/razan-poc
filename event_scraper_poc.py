#!/usr/bin/env python3
"""
Event Scraper PoC
=================

A Proof-of-Concept Python script to scrape contact information (speakers, etc.)
from event websites using Playwright and export the data to Excel.

Dependencies:
    - python >= 3.8
    - playwright
    - pandas
    - openpyxl

Installation:
    pip install playwright pandas openpyxl
    playwright install chromium

Usage:
    python event_scraper_poc.py --url "https://atharfestival.evsreg.com/speakers" --limit 20

    # For a different limit:
    python event_scraper_poc.py --limit 50

    # For a different URL (if structure is similar):
    python event_scraper_poc.py --url "https://another-event.com/speakers"

Author: AI Assistant
"""

import argparse
import logging
import sys
import time
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse

import pandas as pd
from playwright.sync_api import sync_playwright, Page, TimeoutError as PlaywrightTimeoutError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- DOM Selectors (Documented for maintainability) ---
# These selectors are based on the 'atharfestival.evsreg.com' structure.
# If the target website changes, update these constants.
SELECTOR_SPEAKER_CARD = ".card"  # The container for each person
SELECTOR_NAME = "h3"             # Name is usually in an h3 tag inside the card
SELECTOR_JOB_TITLE = "p"         # Job title follows name in a p tag
# Note: The second <p> often contains company or is empty. Logic handles this.

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Scrape event contacts to Excel.")
    parser.add_argument(
        "--url",
        type=str,
        default="https://atharfestival.evsreg.com/speakers",
        help="Target URL to scrape (default: Athar Festival Speakers)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Minimum number of contacts to scrape (default: 20)"
    )
    return parser.parse_args()

def extract_text(element, selector: str) -> str:
    """Helper to safely extract text from a sub-element."""
    try:
        sub_el = element.query_selector(selector)
        return sub_el.inner_text().strip() if sub_el else ""
    except Exception:
        return ""

def determine_category(url: str, text_content: str) -> str:
    """Infer category (Speaker, Exhibitor, Sponsor) from URL or page content."""
    url_lower = url.lower()
    if "speaker" in url_lower:
        return "Speaker"
    elif "exhibitor" in url_lower:
        return "Exhibitor"
    elif "sponsor" in url_lower:
        return "Sponsor"
    return "Other"

def fetch_and_parse(url: str, limit: int) -> List[Dict]:
    """
    Launches browser, navigates to URL, scrolls to load content, and extracts data.
    """
    contacts = []
    
    with sync_playwright() as p:
        logger.info(f"Launching browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        try:
            logger.info(f"Navigating to {url}...")
            # Use domcontentloaded to avoid waiting for every single image/analytic script
            page.goto(url, timeout=60000, wait_until='domcontentloaded')
            
            # Wait for the main list to load. 
            # We look for at least one card element to appear.
            try:
                page.wait_for_selector(SELECTOR_SPEAKER_CARD, timeout=15000)
                logger.info("Initial content loaded.")
            except PlaywrightTimeoutError:
                logger.warning("Timeout waiting for cards. Page structure might be different or empty.")
                # We continue, maybe static content is there or we can take a snapshot for debugging
                
            # Scroll to load more items if necessary (Lazy Loading)
            # Simple scrolling logic: scroll down a few times until we hit limit or stop finding new ones
            last_count = 0
            max_scroll_attempts = 10
            
            for i in range(max_scroll_attempts):
                # Check how many we have visible
                cards = page.query_selector_all(SELECTOR_SPEAKER_CARD)
                current_count = len(cards)
                logger.info(f"Found {current_count} cards so far...")

                if current_count >= limit:
                    break
                
                if current_count == last_count and i > 0:
                    # No new items loaded after scroll
                    logger.info("No new items loaded after scroll. Stopping scroll.")
                    break
                
                last_count = current_count
                
                # Scroll to bottom
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2) # Wait for network/rendering

            # --- Extraction Phase ---
            logger.info("Extracting data from DOM...")
            cards = page.query_selector_all(SELECTOR_SPEAKER_CARD)
            
            event_name = "Athar Festival" # Default/fallback
            # Try to grab title from page title
            page_title = page.title()
            if page_title:
                parts = page_title.split("-")
                if len(parts) > 1:
                    # e.g. "Speakers - Athar Festival of Creativity" -> "Athar Festival of Creativity"
                    event_name = parts[1].strip()
                else:
                    event_name = parts[0].strip()

            category = determine_category(url, "")

            for card in cards:
                if len(contacts) >= limit:
                    break
                
                # Extract Name
                # Selector looks for h3 inside the card-body
                name = extract_text(card, SELECTOR_NAME)
                if not name:
                    continue # Skip empty cards
                
                # Extract Description/Role/Company
                # Usually parsing <p> tags.
                # Example DOM: <h3>Name</h3> <p>Title</p> <p>Company</p>
                # But sometimes Company is merged or missing.
                p_tags = card.query_selector_all("p")
                job_title = ""
                company_name = ""
                
                if len(p_tags) > 0:
                    job_title = p_tags[0].inner_text().strip()
                if len(p_tags) > 1:
                    company_name = p_tags[1].inner_text().strip()
                
                # Basic normalization
                first_name = ""
                last_name = ""
                if name:
                    parts = name.split()
                    if len(parts) == 1:
                        first_name = parts[0]
                    elif len(parts) >= 2:
                        first_name = parts[0]
                        last_name = " ".join(parts[1:])
                
                contact = {
                    "event_name": event_name,
                    "event_url": url,
                    "source_page": url,
                    "person_full_name": name,
                    "first_name": first_name,
                    "last_name": last_name,
                    "job_title": job_title,
                    "company_name": company_name,
                    "country": "", # Not easily visible on card surface usually
                    "category": category,
                    "email": "",
                    "phone": "",
                    "linkedin_url": "",
                    "company_website": "",
                    "scraped_at": datetime.now().isoformat()
                }
                contacts.append(contact)

        except Exception as e:
            logger.error(f"An error occurred during scraping: {e}")
            # We don't raise here, we want to return whatever we got so far
            
        finally:
            browser.close()
            logger.info("Browser closed.")
            
    return contacts

def export_to_excel(data: List[Dict], filename: str, sheet_name: str):
    """Export list of dicts to Excel."""
    if not data:
        logger.warning("No data to export.")
        return

    df = pd.DataFrame(data)
    
    # Ensure all columns from requirements exist even if empty
    required_columns = [
        "event_name", "event_url", "source_page", "person_full_name",
        "first_name", "last_name", "job_title", "company_name",
        "country", "category", "email", "phone", "linkedin_url",
        "company_website", "scraped_at"
    ]
    
    # Reorder/Add missing cols
    for col in required_columns:
        if col not in df.columns:
            df[col] = ""
            
    df = df[required_columns]
    
    try:
        logger.info(f"Saving to {filename}...")
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        logger.info(f"Successfully exported {len(df)} contacts to {filename}")
    except Exception as e:
        logger.error(f"Failed to write Excel file: {e}")

def main():
    args = parse_arguments()
    
    logger.info(f"Starting scrape for {args.url} (Target limit: {args.limit})")
    
    contacts = fetch_and_parse(args.url, args.limit)
    
    logger.info(f"Scraped {len(contacts)} contacts.")
    
    if contacts:
        # Derive filename from domain
        domain = urlparse(args.url).netloc.replace("www.", "").split(".")[0]
        filename = f"poc_{domain}_speakers.xlsx"
        sheet_name = f"{domain}_speakers"[:31] # Excel sheet limit 31 chars
        
        export_to_excel(contacts, filename, sheet_name)
    else:
        logger.error("No contacts found. Please check the URL or selectors.")

if __name__ == "__main__":
    main()

