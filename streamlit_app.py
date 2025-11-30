import streamlit as st
import pandas as pd
import time
from event_scraper_poc import fetch_and_parse
# Import both mock and real services
from enrichment_service import find_decision_makers as find_decision_makers_mock
from event_scraper_poc import fetch_and_parse
# Import services
from google_search_service import google_search_linkedin
from urllib.parse import urlparse
import io

# Page config
st.set_page_config(
    page_title="Event Contact Scraper",
    page_icon="🔍",
    layout="wide"
)

# Title and description
st.title("🔍 Event Contact Scraper & Enricher")
st.markdown("""
This tool visits speaker detail pages to extract precise info and uses **Google Search** to find LinkedIn profiles.
""")

# Sidebar for configuration
with st.sidebar:
    st.header("Scraping Settings")
    url_input = st.text_input(
        "Event URL",
        value="https://atharfestival.evsreg.com/speakers",
        help="The URL of the page containing the list of speakers",
        disabled=True
    )
    
    limit_input = st.number_input(
        "Max Initial Contacts",
        min_value=1,
        max_value=20,
        value=5,
        step=1,
        help="Number of speakers to visit (maximum 20, each visit takes time)"
    )
    
    st.markdown("---")
    st.header("Enrichment Settings")
    
    enable_linkedin_lookup = st.checkbox(
        "Find Speaker LinkedIn",
        value=True,
        help="Use Google Search API to find LinkedIn for the scraped speakers"
    )
    
    st.info("ℹ️ Decision makers (Directors, C-level, Management) are automatically detected from job titles during scraping.")

# Main content area
if st.button("🚀 Start Process", type="primary"):
    if not url_input:
        st.error("Please enter a URL")
    else:
        try:
            # --- PHASE 1: SCRAPING ---
            with st.status("Step 1: Scraping Detail Pages...", expanded=True) as status:
                st.write(f"Collecting links from {url_input}...")
                start_time = time.time()
                
                # Run the scraper
                base_contacts = fetch_and_parse(url_input, limit_input)
                
                if not base_contacts:
                    status.update(label="Scraping failed or found no contacts.", state="error")
                    st.stop()
                    
                status.update(label=f"✅ Scraped {len(base_contacts)} speakers via detail pages!", state="complete", expanded=False)

            # --- PHASE 2: SPEAKER ENRICHMENT (LinkedIn via Google Search) ---
            if enable_linkedin_lookup:
                with st.status("Step 2: Finding Speaker LinkedIn Profiles (Google Search)...", expanded=True) as status:
                    progress_bar = st.progress(0)
                    for i, contact in enumerate(base_contacts):
                        st.write(f"Searching for: **{contact['person_full_name']}** at **{contact['company_name']}**")
                        
                        # Use new Google Search Service
                        linkedin = google_search_linkedin(
                            contact['person_full_name'],
                            contact['company_name'],
                            contact['job_title']
                        )
                        
                        if linkedin:
                            contact['linkedin_url'] = linkedin
                            st.write(f"Found: [{linkedin}]({linkedin})")
                        else:
                            st.write("Not found.")
                            
                        progress_bar.progress((i + 1) / len(base_contacts))
                    status.update(label="✅ Speaker LinkedIn lookup complete!", state="complete", expanded=False)

            # --- DISPLAY & EXPORT ---
            final_data = base_contacts
            duration = time.time() - start_time
            df = pd.DataFrame(final_data)
            
            # Ensure all columns exist
            required_columns = [
                "event_name", "event_url", "source_page", "person_full_name",
                "first_name", "last_name", "job_title", "company_name",
                "country", "category", "email", "phone", "linkedin_url",
                "company_website", "scraped_at"
            ]
            for col in required_columns:
                if col not in df.columns:
                    df[col] = ""
            df = df[required_columns]
            
            st.success(f"🎉 Process complete in {duration:.2f} seconds! Total records: {len(df)}")
            
            # Metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Records", len(df))
            col2.metric("Decision Makers", len(df[df['category'] == 'Decision Maker']))
            col3.metric("With LinkedIn", len(df[df['linkedin_url'] != '']))
            
            # Preview
            st.subheader("Data Preview")
            st.dataframe(df, use_container_width=True)
            
            # Download
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                sheet_name = urlparse(url_input).netloc.replace("www.", "").split(".")[0][:31]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            st.download_button(
                label="📥 Download Excel Report",
                data=buffer.getvalue(),
                file_name=f"enriched_contacts_{int(time.time())}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

