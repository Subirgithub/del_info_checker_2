# Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# --- STEP 1: INSTALL SYSTEM DEPENDENCIES & GOOGLE CHROME ---
# Install essential packages, including wget and gnupg for adding repositories
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    # Browser dependencies
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libatspi2.0-0 \
    libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxkbcommon0 \
    libpango-1.0-0 libcairo2 libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Add Google's official GPG key to trust the repository
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -

# Add the Chrome repository to the system's sources list
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'

# Update sources and install the official Google Chrome browser
RUN apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*


# --- STEP 2: INSTALL PYTHON REQUIREMENTS ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# We do not need to run 'playwright install' as we are using the system's Chrome


# --- STEP 3: COPY YOUR APP AND RUN IT ---
COPY . .
# The CMD no longer needs xvfb-run
CMD ["streamlit", "run", "app.py", "--server.port", "10000", "--server.address", "0.0.0.0"]