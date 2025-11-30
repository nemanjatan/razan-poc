import streamlit as st
import pandas as pd
import time
from event_scraper_poc import fetch_and_parse, determine_category
from urllib.parse import urlparse
import io

# Page config
st.set_page_config(
    page_title="Event Contact Scraper",
    page_icon="🔍",
    layout="wide"
)

# Title and description
st.title("🔍 Event Contact Scraper")
st.markdown("""
This tool scrapes speaker/contact information from event websites.
Enter the URL below to start scraping.
""")

# Sidebar for configuration
with st.sidebar:
    st.header("Settings")
    url_input = st.text_input(
        "Event URL",
        value="https://atharfestival.evsreg.com/speakers",
        help="The URL of the page containing the list of speakers"
    )
    
    limit_input = st.number_input(
        "Max Contacts",
        min_value=1,
        max_value=1000,
        value=20,
        step=10,
        help="Maximum number of contacts to scrape"
    )
    
    st.markdown("---")
    st.markdown("### About")
    st.markdown("This PoC uses Playwright to scrape dynamic content and exports structured data to Excel.")

# Main content area
if st.button("🚀 Start Scraping", type="primary"):
    if not url_input:
        st.error("Please enter a URL")
    else:
        try:
            with st.status("Scraping in progress...", expanded=True) as status:
                st.write("Initializing browser...")
                
                # Progress container
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # We need to modify fetch_and_parse to accept a callback for progress or just run it
                # For now, we'll run it directly. In a real app, we might want async or detailed callbacks.
                st.write(f"Navigating to {url_input}...")
                
                # Run the scraper
                # Note: synchronous playwright might block the UI thread slightly, 
                # but acceptable for this PoC.
                start_time = time.time()
                contacts = fetch_and_parse(url_input, limit_input)
                
                duration = time.time() - start_time
                status.update(label="Scraping complete!", state="complete", expanded=False)
                
            if contacts:
                df = pd.DataFrame(contacts)
                
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
                
                # Success message
                st.success(f"✅ Successfully scraped {len(df)} contacts in {duration:.2f} seconds!")
                
                # Display metrics
                col1, col2, col3 = st.columns(3)
                col1.metric("Total Contacts", len(df))
                col1.metric("Event Name", df['event_name'].iloc[0] if not df.empty else "N/A")
                col1.metric("Category", df['category'].iloc[0] if not df.empty else "N/A")
                
                # Preview data
                st.subheader("Data Preview")
                st.dataframe(df, use_container_width=True)
                
                # Export options
                st.subheader("Download")
                
                # Create Excel buffer
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    sheet_name = urlparse(url_input).netloc.replace("www.", "").split(".")[0][:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                st.download_button(
                    label="📥 Download as Excel",
                    data=buffer.getvalue(),
                    file_name=f"scraped_contacts_{int(time.time())}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            else:
                st.warning("No contacts found. Please check the URL or try a different page.")
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")

