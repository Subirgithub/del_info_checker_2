# Dockerfile

# Start from a stable Python base image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# 1. Copy requirements file and install Python packages first
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Install xvfb and Playwright's bundled Chromium with its dependencies
RUN apt-get update && apt-get install -y xvfb && \
    python -m playwright install --with-deps chromium && \
    rm -rf /var/lib/apt/lists/*

# 3. Copy your startup script and all your application code
COPY start.sh .
COPY . .

# Make the startup script executable
RUN chmod +x ./start.sh

# 4. Set the command to run the startup script when the container launches
CMD ["./start.sh"]