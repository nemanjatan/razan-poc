FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    gnupg \
    ca-certificates \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# Install Playwright browsers and dependencies
RUN playwright install chromium && \
    playwright install-deps chromium

# Copy application code (includes csv-templates directory)
COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:${PORT:-8501}/_stcore/health || exit 1

# Simple entrypoint to set STREAMLIT_SERVER_PORT from Railway's PORT
RUN echo '#!/bin/sh\nexport STREAMLIT_SERVER_PORT=${PORT:-8501}\nexec streamlit run streamlit_app.py --server.address=0.0.0.0 --server.headless=true' > /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
