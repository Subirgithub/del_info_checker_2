#!/usr/bin/env python
# coding: utf-8

import traceback
import asyncio
import pandas as pd
import io
import re
import time
from datetime import date,datetime
from playwright.async_api import async_playwright, TimeoutError, expect
#from playwright_stealth import Stealth
import traceback
import os
import random

# --- Proxy Configuration ---
# IMPORTANT: It's best practice to store these in your Render Environment Variables.
PROXY_USERNAME = os.environ.get('PROXY_USERNAME', 'brd-customer-hl_7103f8de-zone-pincode_scraper')
PROXY_PASSWORD = os.environ.get('PROXY_PASSWORD', 'i7rk9k9oaw9y')
PROXY_HOST = 'brd.superproxy.io'
PROXY_PORT = 33335

proxy_server_url = f'http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}'

#creating the input dataframe for crawling Nykaa
data = {
    'style_name': ['M.A.C MACximal Matte Lipstick'],
    'site_name': ['Nykaa'],
    'product_url': ['https://www.nykaa.com/m-a-c-macximal-matte-lipstick/p/13784071?productId=13784071&pps=1&skuId=13784061']
}
# Create the DataFrame
df_temp = pd.DataFrame(data)


# In[139]:


# 1. Create a list of your pincodes
pincodes = [191121,175123,226010]
# 2. Convert the list into a pandas DataFrame
pincode_df = pd.DataFrame(pincodes, columns=['pincode'])
#3. Perform the cross join
final_df = df_temp.merge(pincode_df, how='cross')
#print(final_df)


# In[140]:


async def human_like_scroll(page):
    """Scrolls the page to mimic human behavior."""
    print("--- Scrolling page to appear more human...")
    await page.evaluate("window.scrollTo(0, 0)")
    await page.wait_for_timeout(random.uniform(500, 1000))
    # Scroll down a random amount
    scroll_amount = random.randint(300, 600)
    await page.mouse.wheel(0, scroll_amount)
    await page.wait_for_timeout(random.uniform(1000, 2500))

    # --- THIS LINE IS NOW FIXED ---
    # Scroll back up a little by a random amount
    scroll_amount = random.randint(-250, -100) 
    # --- END OF FIX ---

    await page.mouse.wheel(0, scroll_amount)
    await page.wait_for_timeout(random.uniform(500, 1000))


# In[ ]:


async def check_and_close_intermittent_popup(page):
    """Looks for and closes the 'Push Notifications' pop-up."""
    # This is the correct selector for the "No thanks" button.
    no_thanks_selector = "#wzrk-cancel" 

    try:
        # Use a short timeout as this pop-up is intermittent
        await page.locator(no_thanks_selector).click(timeout=2000)
        print("--- Closed 'Push Notifications' pop-up. ---")
        await page.wait_for_timeout(1000) # Wait a moment for it to disappear
    except Exception:
        pass # This is normal, it just means no pop-up was found        


# In[ ]:


# --- CONFIGURATION: UPDATE SELECTORS HERE WHEN THEY BREAK ---
SITE_CONFIG = {
    "Amazon": {
        "initial_popup_close_selector": None,
        "pre_pincode_click_selector": "#contextualIngressPtLabel_deliveryShortLine",
        "pincode_container_selector": None,
        "pincode_input_selector": "#GLUXZipUpdateInput",
        "pincode_submit_selector": "input[aria-labelledby='GLUXZipUpdate-announce']",
        # --- ADD THIS NEW KEY ---
        "unavailable_selector": "#availability span:has-text('Currently unavailable.')",
        "delivery_info_selector": {
            "primary": "span[data-csa-c-content-id='DEXUnifiedCXPDM']",
            "secondary": "span[data-csa-c-content-id='DEXUnifiedCXSDM']"
        }
},
    "Flipkart": {
    "initial_popup_close_selector": "button._2KpZ6l._2doB4z",
    # This selector is for the pre-selected pincode div that needs to be clicked
    "pre_pincode_click_selector": "div.JqZtEs",
    "pincode_input_selector": "input[placeholder='Enter delivery pincode']",
    "pincode_submit_selector": "//span[text()='Check']",
    "delivery_info_selector": "div.hVvnXm"
},
    "Myntra": {
        "initial_popup_close_selector": None,
        # This is the selector for the 'Change' button
        "pre_pincode_click_selector": "button.pincode-check-another-pincode",
        "pincode_input_selector": "input[placeholder='Enter pincode']",
        "pincode_submit_selector": "input[value='Check']",
        "delivery_info_selector": "h4.pincode-serviceabilityTitle"
    },
    # In your SITE_CONFIG dictionary
    "Nykaa": {
    "initial_popup_close_selector": None,
    "pre_pincode_click_selector": "//button[text()='Change']",
    "pincode_input_selector": "input[placeholder='Enter pincode']",
    "pincode_submit_selector": "//button[text()='Check']",
    "unavailable_selector": "//button[normalize-space()='Notify Me']",    
    #"delivery_info_selector": "//span[contains(text(), 'Delivery by')]"
    "delivery_info_selectors": [
        {
            "type": "unserviceable", 
            "selector": "//span[contains(text(), 'Does not ship to pincode')]"
        },
        {
            "type": "primary_delivery", 
            "selector": "//span[contains(text(), 'Delivery by')]"
        },
        {
            "type": "secondary_info", 
            "selector": "//span[contains(text(), 'COD available')]"
        }
    ]    
},
    "Nykaafashion": {
    "initial_popup_close_selector": None,
    "pre_pincode_click_selector": "//button[text()='Edit']",
    "pincode_input_selector": "[data-at='pincode-input']",
    # This XPath selector is more reliable than a CSS class.
    "pincode_submit_selector": "//button[text()='Apply']",
    # This selector is also more robust.
    "unavailable_selector": "//button[normalize-space()='Notify Me']",    
    "delivery_info_selector": "//h3[contains(text(), 'Delivery by')]"
},

    "Ajio": {
        "initial_popup_close_selector": None, # No known pop-up
        "pre_pincode_click_selector": '//div[@aria-label="Enter Pin-code To Know Estimated Delivery Date"]',
        "pincode_input_selector": "//input[@name='pincode']",
        "pincode_submit_selector": "//button[text()='CONFIRM PINCODE']",
        "delivery_info_selector": "//div[contains(@class, 'edd-message-container')]//span"
},
    "Meesho": {
        "initial_popup_close_selector": None,
        "pre_pincode_click_selector": None,
        "pincode_container_selector": None,
        "pincode_input_selector": "#pin", # Using the stable ID attribute
        "pincode_submit_selector": "//span[text()='CHECK']", # Finding the span by its text
        "delivery_info_selector": "//span[contains(text(), 'Delivery by')]" # Finding by partial text
    }
}



def extract_delivery_date(row):
    """
    Parses a date from various text formats ("Same day", "Next day", "28 Sep")
    and returns a datetime object.
    """
    delivery_text = str(row['delivery_info'])
    scrape_date = row['scrape_date']

    # --- NEW: Handle text-based delivery times ---
    # It checks for these patterns first, ignoring case.
    if re.search(r'in 2 hrs|same day|today', delivery_text, re.IGNORECASE):
        return scrape_date

    elif re.search(r'next day|tomorrow', delivery_text, re.IGNORECASE):
        return scrape_date + timedelta(days=1)

    # --- Fallback to original logic if no text match is found ---
    month_pattern = r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    date_pattern = r"(\d{1,2})\s+" + month_pattern

    match = re.search(date_pattern, delivery_text, re.IGNORECASE)

    if not match:
        return pd.NaT

    day = int(match.group(1))
    month_str = match.group(2)

    try:
        date_str = f"{day} {month_str} {scrape_date.year}"
        delivery_dt = datetime.strptime(date_str, '%d %B %Y')
    except ValueError:
        try:
            delivery_dt = datetime.strptime(date_str, '%d %b %Y')
        except ValueError:
            return pd.NaT

    # Year Crossover Logic
    if delivery_dt.date() < scrape_date.date():
        delivery_dt = delivery_dt.replace(year=scrape_date.year + 1)

    return delivery_dt


# In[ ]:


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
]


# In[142]:


async def scrape_pincode_on_page(page, site, pincode):
    """
    Attempts to enter a pincode using a deliberate, multi-step process to handle dynamic elements.
    """
    #print("entered function")
    config = SITE_CONFIG.get(site)
    if not config:
        return {"primary": "Site not configured", "secondary": ""}

    # MODIFIED: Loop for up to 2 attempts (1 initial + 1 retries)
    max_attempts = 2
    for attempt in range(max_attempts):
        try:
            # On retries (attempt > 0), the page is already reloaded by the except block.
            if attempt > 0:
                print(f"--- Starting Retry Attempt {attempt + 1}/{max_attempts} for pincode {pincode} ---")

            pre_click_selector = config.get("pre_pincode_click_selector")
            if pre_click_selector:
                try:
                    # Use a short timeout as this button may not be present on the first run.
                    await page.locator(pre_click_selector).first.click(timeout=3000)
                    #print("--- Clicked 'Change' button to enter a new pincode. ---")
                except Exception:
                    # This is expected if it's the first pincode check for this URL.
                    #print("--- No 'Change' button found, proceeding directly. ---")
                    pass

            # --- START OF MODIFICATION ---
            # STEP 2: Enter the pincode by typing character by character.
            pincode_input_element = page.locator(config["pincode_input_selector"]).first

            # --- ADD THIS LINE ---
            # Explicitly wait for the input box to be visible before interacting.
            #print("--- Waiting for pincode input to be visible... ---")
            await pincode_input_element.wait_for(state="visible", timeout=7000)

            #print("--- Pincode input is ready. Typing now. ---")
            await pincode_input_element.clear()

            await pincode_input_element.fill(pincode)
            await page.wait_for_timeout(500)

           # for char in pincode:
           #     await pincode_input_element.press(char, delay=random.randint(80, 250))
            # --- END OF MODIFICATION ---

            # pincode_input_element = page.locator(config["pincode_input_selector"]).first
            # pincode_container_selector = config.get("pincode_container_selector")

            # if pincode_container_selector:
            #     await page.locator(pincode_container_selector).first.click()

            # await pincode_input_element.hover()
            # await pincode_input_element.clear()
            # for char in pincode:
            #     await pincode_input_element.press(char, delay=random.randint(80, 250))

            #await page.wait_for_timeout(500)

            # --- STEP 2: Click the submit/check button ---
            if config.get("pincode_submit_selector"):
                await page.locator(config["pincode_submit_selector"]).first.click()

            # --- Data Extraction ---
            # Initialize a dictionary to hold the results.
            results = {"primary": "Not found", "secondary": ""}

            # Get the prioritized list of selectors from your config.
            delivery_selectors = config.get("delivery_info_selectors", [])

            # Loop through each selector in the order they are listed.
            for item in delivery_selectors:
                item_type = item["type"]
                selector = item["selector"]

                try:
                    # Use a short timeout to quickly check if the element is visible.
                    element = page.locator(selector).first
                    await element.wait_for(state="visible", timeout=5000)

                    # If the element is found, grab its text.
                    text_content = (await element.inner_text()).strip()

                    if item_type == "primary_delivery":
                        results["primary"] = text_content

                    elif item_type == "unserviceable":
                        results["primary"] = text_content
                        # This is a final status. We can stop checking.
                        break

                    elif item_type == "secondary_info":
                        results["secondary"] = text_content

                except Exception:
                    # It's normal for a selector not to be found. Just move to the next one.
                    pass

            # If we reach here, the attempt was successful.
            return results

        except Exception as e:
            # MODIFIED: Handle failure and decide whether to retry or fail permanently.
            print(f"--- Attempt {attempt + 1} for pincode {pincode} failed: {type(e).__name__} ---")
            if attempt < max_attempts - 1: # If this wasn't the last attempt
                print(f"--- Refreshing page and preparing for retry... ---")
                await page.reload(wait_until="domcontentloaded", timeout=60000)
            else: # This was the final attempt
                print(f"--- Final attempt for pincode {pincode} also failed.")
                return {"primary": f"Error: Failed after {max_attempts} attempts", "secondary": ""}

    # This is reached if all attempts in the loop fail
    return {"primary": "Error: All retry attempts failed.", "secondary": ""}


# In[1]:


async def main_scraper_func(input_df: pd.DataFrame) -> pd.DataFrame:
    """Main function with corrected advanced failure handling and pop-up handling."""
    start_time = time.monotonic()

    # try:
    #     input_df = pd.read_csv("input_file_test.csv")
    #    # print("Loaded file 'input_file.csv' ")
    # except FileNotFoundError:
    #     print("Error: 'input_file.csv' not found. Please create it and run again.")
    #     return

    input_df = final_df.copy()

    all_results_list = []

    # --- Two-pass retry loop ---
    for pass_num in [1, 2]:
        if pass_num == 1:
            tasks_df = input_df
            print("\n" + "="*20 + " STARTING PASS 1 " + "="*20)
        else:
            pass_1_df = pd.DataFrame(all_results_list)
            tasks_df = pass_1_df[pass_1_df['delivery_info'].str.startswith("Error:", na=False)].copy()

            if tasks_df.empty:
                print("\nNo failed tasks to retry. All tasks succeeded in the first pass.")
                break

            # Rebuild the main list to only contain the SUCCEEDED tasks from Pass 1.
            # This prevents duplicate entries for failed tasks.
            successful_pass_1_df = pass_1_df[~pass_1_df['delivery_info'].str.startswith("Error:", na=False)]
            all_results_list = successful_pass_1_df.to_dict('records')

            print("\n" + "="*20 + f" STARTING PASS 2: RETRYING {len(tasks_df)} FAILED TASKS " + "="*20)

        consecutive_url_failures = 0

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True,
                                              proxy={"server": proxy_server_url})

            for url, group in tasks_df.groupby('product_url'):
                if consecutive_url_failures >= 3:
                    print("\n!!! 3 consecutive URL failures. Aborting this pass. !!!")
                    break

                context = await browser.new_context(user_agent=random.choice(USER_AGENTS),
                                                    ignore_https_errors=True)
                page = await context.new_page()

                try:
                    site = group.iloc[0]["site_name"]
                    style_name = group.iloc[0]["style_name"]
                    print(f"\n[Pass {pass_num}] Navigating to {style_name} on {site}...")

                    await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                    consecutive_url_failures = 0

                    # Check if the product is unavailable before checking pincodes.
                    config = SITE_CONFIG.get(site, {})
                    unavailable_selector = config.get("unavailable_selector")
                    if unavailable_selector:
                        try:
                            # Use a short timeout to quickly check for the "Notify Me" button.
                            await page.locator(unavailable_selector).first.wait_for(state="visible", timeout=1000)
                            print(f"--- Product is unavailable. Skipping all pincodes for this URL. ---")
                            # Mark all pincodes for this URL as unavailable and continue to the next URL.
                            for _, row in group.iterrows():
                                all_results_list.append({
                                   # "master_category": row["master_category"], "article_type": row["article_type"],
                                    "style_name": row["style_name"], "site_name": site,
                                    "product_url": url, "pincode": row["pincode"],
                                    "delivery_info": "Product Unavailable", "secondary_delivery_info": ""
                                })
                            continue # Skip to the next product URL
                        except Exception:
                            # If the selector is not found, the product is available. Proceed normally.
                            pass

                    # *** ADDED POP-UP CHECK HERE ***
                    # After the page has loaded, check for and close any pop-ups.
                    await check_and_close_intermittent_popup(page)

                    consecutive_pincode_failures = 0

                    for index, row in group.iterrows():
                        if consecutive_pincode_failures >= 3:
                            print(f"--- 3 consecutive pincode failures for {style_name}. ABORTING THIS URL. ---")
                            remaining_rows = group.iloc[index:]
                            for _, remaining_row in remaining_rows.iterrows():
                                all_results_list.append({
                                   # "master_category": remaining_row["master_category"], "article_type": remaining_row["article_type"],
                                    "style_name": remaining_row["style_name"], "site_name": remaining_row["site_name"],
                                    "product_url": url, "pincode": remaining_row["pincode"],
                                    "delivery_info": "Error: Aborted due to 3 consecutive pincode failures", "secondary_delivery_info": ""
                                })
                            break

                        pincode = str(row["pincode"])
                        delivery_data = await scrape_pincode_on_page(page, site, pincode)

                        result = {
                           # "master_category": row["master_category"], "article_type": row["article_type"],
                            "style_name": row["style_name"], "site_name": site,
                            "product_url": url, "pincode": pincode,
                            "delivery_info": delivery_data.get("primary", ""),
                            "secondary_delivery_info": delivery_data.get("secondary", "")
                        }
                        all_results_list.append(result)

                        if "Error" in result["delivery_info"] or "Not found" in result["delivery_info"]:
                            consecutive_pincode_failures += 1
                        else:
                            consecutive_pincode_failures = 0

                except Exception as e:
                    print(f"!!! Failed to process URL {url}. Error: {e}")
                    consecutive_url_failures += 1
                    for _, row in group.iterrows():
                        all_results_list.append({
                           # "master_category": row["master_category"], "article_type": row["article_type"],
                            "style_name": row["style_name"], "site_name": row["site_name"],
                            "product_url": url, "pincode": row["pincode"],
                            "delivery_info": f"Error: Failed to load page - {e}", "secondary_delivery_info": ""
                        })
                finally:
                    await context.close()

            await browser.close()

        # if pass_num == 2 and consecutive_url_failures >= 3:
        #     print("\n!!! Aborted Pass 2 due to 3 consecutive URL failures. Exiting program. !!!")
        #     final_df = pd.DataFrame(all_results_list).drop_duplicates(subset=['product_url', 'pincode'], keep='last')

        #     final_df['scrape_date'] = pd.to_datetime(date.today())
        #     final_df['delivery_date'] = final_df.apply(extract_delivery_date, axis=1)
        #     delivery_dates = pd.to_datetime(final_df['delivery_date'], errors='coerce')
        #     final_df['days_to_delivery'] = (delivery_dates - final_df['scrape_date']).dt.days

        #     final_df.to_csv("delivery_speed_output_INCOMPLETE_nykaa.csv", index=False)
        #     print("\nScraping partially done. Results saved to 'delivery_speed_output_INCOMPLETE.csv'")
        #     duration = time.monotonic() - start_time
        #     minutes = int(duration // 60)
        #     seconds = int(duration % 60)

        #     print("\n" + "="*50)
        #     print(f"Total script execution time: {minutes} minutes and {seconds} seconds.")
        #     print("="*50)
        #     return

    final_results_df = pd.DataFrame(all_results_list).drop_duplicates(subset=['product_url', 'pincode'], keep='last')

    final_results_df['scrape_date'] = pd.to_datetime(date.today())
    final_results_df['delivery_date'] = final_results_df.apply(extract_delivery_date, axis=1)
    delivery_dates = pd.to_datetime(final_results_df['delivery_date'], errors='coerce')
    final_results_df['days_to_delivery'] = (delivery_dates - final_results_df['scrape_date']).dt.days

    final_results_df.to_csv("serviceability_check_nykaa.csv", index=False)
    print("\nScraping complete. Results saved to 'serviceability_check_nykaa.csv'")

    duration = time.monotonic() - start_time
    minutes = int(duration // 60)
    seconds = int(duration % 60)

    print("\n" + "="*50)
    print(f"Total script execution time: {minutes} minutes and {seconds} seconds.")
    print("="*50)

    return final_results_df




