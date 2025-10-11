# Dockerfile

# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# --- STEP 1: INSTALL SYSTEM DEPENDENCIES & GOOGLE CHROME ---
# This single RUN command is more efficient and reliable.
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    # Browser dependencies
    libnss3 libatk1.0-0 libatk-bridge2.0-0 libatspi2.0-0 \
    libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxkbcommon0 \
    libpango-1.0-0 libcairo2 libasound2 \
    && \
    # --- Modern and robust way to add Google's key and repository ---
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome-keyring.gpg && \
    sh -c 'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list' && \
    # --- End of new method ---
    apt-get update && apt-get install -y google-chrome-stable && \
    # Clean up apt caches to reduce image size
    rm -rf /var/lib/apt/lists/*


# --- STEP 2: INSTALL PYTHON REQUIREMENTS ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# We do not need to run 'playwright install' as we are using the system's Chrome


# --- STEP 3: COPY YOUR APP AND RUN IT ---
COPY . .
# The CMD no longer needs xvfb-run
CMD ["streamlit", "run", "app.py", "--server.port", "10000", "--server.address", "0.0.0.0"]