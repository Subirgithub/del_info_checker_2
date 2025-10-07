import streamlit as st
import subprocess
import sys

# Use a Streamlit decorator to run this only once, when the app starts.
@st.cache_resource
def install_playwright():
    """Installs playwright browsers."""
    print("Starting Playwright browser installation...")
    # The command Playwright itself recommended in the error logs
    subprocess.run([f"{sys.executable}", "-m", "playwright", "install"], check=True)
    print("Playwright browsers installed successfully.")

# Call the installation function at the start of the app
install_playwright()

import pandas as pd
import asyncio
from Scraper_nykaa import main_scraper_func  # Assume you refactor your main() into this

st.set_page_config(layout="wide")
st.title("🛍️ Nykaa Delivery Speed Checker")

st.write("Enter a product to search for and the pincodes to check.")

# --- 1. User Inputs ---
search_term = st.text_input("Product Search Term", "H&M Women Straight High Jeans")
pincodes_input = st.text_area("Enter Pincodes (one per line)", "201301\n700020\n600100")

# --- 2. Run Button ---
if st.button("🚀 Get Delivery Speeds"):
    if not search_term or not pincodes_input:
        st.error("Please provide both a search term and at least one pincode.")
    else:
        # --- 3. Process Inputs and Run Scraper ---
        pincode_list = [p.strip() for p in pincodes_input.split('\n') if p.strip()]
        
        # Create a DataFrame in the format your scraper expects
        input_data = {
            'site_name': ['Nykaa'] * len(pincode_list),
            'style_name': [search_term] * len(pincode_list),
            'pincode': pincode_list
        }
        input_df = pd.DataFrame(input_data)
        
        with st.spinner(f"Scraping delivery speeds for '{search_term}'... Please wait."):
            # Run your async scraper function
            # Note: Streamlit requires a bit of care with asyncio
            results_df = asyncio.run(main_scraper_func(input_df))
            
            # --- 4. Display Results ---
            st.success("Scraping complete!")
            st.dataframe(results_df)

            # Optional: Add a download button for the results
            csv = results_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Results as CSV",
                data=csv,
                file_name=f'{search_term.replace(" ", "_")}_delivery_speeds.csv',
                mime='text/csv',
            )