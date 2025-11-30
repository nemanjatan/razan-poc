FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
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

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers and dependencies
RUN playwright install chromium && \
    playwright install-deps chromium

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Create entrypoint script that handles PORT variable
RUN echo '#!/bin/bash\n\
PORT=${PORT:-8080}\n\
exec streamlit run streamlit_app.py --server.address=0.0.0.0 --server.headless=true' > /entrypoint.sh && \
    chmod +x /entrypoint.sh

# Run via entrypoint
ENTRYPOINT ["/entrypoint.sh"]

