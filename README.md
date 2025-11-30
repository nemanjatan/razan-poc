# Event Contact Scraper

A Streamlit web application that scrapes speaker/contact information from event websites using Playwright.

## Features

- Web scraping using Playwright for dynamic content
- Export scraped data to Excel format
- User-friendly Streamlit interface
- Configurable scraping limits

## Local Development

### Prerequisites

- Python 3.10+
- pip

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install chromium
```

3. Run the application:
```bash
streamlit run streamlit_app.py
```

## Railway Deployment

This app is configured for deployment on Railway.app.

### Deployment Steps

1. Push your code to a Git repository (GitHub, GitLab, etc.)
2. Connect your repository to Railway.app
3. Railway will automatically detect the configuration files:
   - `Procfile` - Defines how to run the app
   - `requirements.txt` - Python dependencies
   - `runtime.txt` - Python version
   - `railway.json` - Railway-specific configuration

### Railway Configuration

The app is configured to:
- Install all Python dependencies
- Install Playwright Chromium browser and system dependencies
- Run Streamlit on the port provided by Railway
- Bind to `0.0.0.0` to accept external connections

### Environment Variables

No environment variables are required for basic operation. The app will use Railway's automatically provided `PORT` environment variable.

## Project Structure

- `streamlit_app.py` - Main Streamlit application
- `event_scraper_poc.py` - Web scraping logic using Playwright
- `requirements.txt` - Python dependencies
- `Procfile` - Process file for Railway deployment
- `runtime.txt` - Python version specification
- `railway.json` - Railway deployment configuration

## Usage

1. Enter the event URL in the sidebar
2. Set the maximum number of contacts to scrape
3. Click "Start Scraping"
4. Download the results as an Excel file

