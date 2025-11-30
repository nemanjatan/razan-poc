#!/bin/bash
# Setup script for Railway deployment
# Installs Playwright browsers after pip install

echo "Installing Playwright browsers..."
playwright install chromium
playwright install-deps chromium

echo "Setup complete!"

