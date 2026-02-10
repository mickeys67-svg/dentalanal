# Use official Playwright Python image as base (Ubuntu-based)
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

WORKDIR /app

# The official image already has playwright and browsers installed,
# but we need our python dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ensure playwright is ready for the installed version
RUN playwright install chromium

COPY . .

# Set environment variables for production if not passed
ENV MOUNT_PATH=/app
ENV PORT=8080

# Cloud Run sets the PORT environment variable.
# We use shell form to allow the variable to be expanded.
# We also add --proxy-headers for real IP detection and --workers 1 for consistency in small instances.
CMD python3 -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers --workers 1 --log-level info
