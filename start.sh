#!/bin/bash
# start.sh

# Exit immediately if a command exits with a non-zero status
set -e

# Run the Streamlit app using xvfb-run
# This command starts the virtual display and then runs your streamlit app inside it.
# It correctly uses the $PORT variable provided by Render.
streamlit run app.py --server.port $PORT --server.headless true