# Dockerfile

# Start from a stable Python base image
FROM python:3.10-slim

# Set environment variables to prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# 1. Install system dependencies needed for xvfb and Playwright's browser
RUN apt-get update && apt-get install -y \
    xvfb \
    # Playwright's recommended dependencies for Chromium
    libnss3 libnspr4 libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libatspi2.0-0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libxkbcommon0 libpango-1.0-0 \
    libcairo2 libasound2 \
    # Clean up apt cache
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# 2. Copy requirements file and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. Install the Playwright browser binaries into the Docker image
# This is the step that replaces the function you removed from app.py
RUN python -m playwright install chromium

# 4. Copy your startup script and all your application code
COPY start.sh .
COPY . .

# Make the startup script executable
RUN chmod +x ./start.sh

# 5. Set the command to run the startup script when the container launches
CMD ["./start.sh"]