import os
import json
import time
import logging
from playwright.sync_api import Playwright, sync_playwright, TimeoutError as PlaywrightTimeoutError
from dotenv import load_dotenv
from browserbase import Browserbase

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Browserbase client
browserbase_api_key = os.getenv('BROWSERBASE_API_KEY')
browserbase_project_id = os.getenv('BROWSERBASE_PROJECT_ID')

if not browserbase_api_key or not browserbase_project_id:
    raise ValueError("BROWSERBASE_API_KEY and BROWSERBASE_PROJECT_ID must be set in environment or .env file")

bb = Browserbase(api_key=browserbase_api_key)

def wait_for_table_to_load(page, timeout=5000):
    """
    Wait for the table to fully load with a shorter timeout.
    Uses a polling approach to detect the table quickly.
    """
    logger.info("Waiting for table to load...")
    
    # Define different possible selectors to identify the table
    table_selectors = [
        "table",                       # Basic table element
        "table tbody tr",              # Table rows 
        ".ant-table-tbody tr",         # Ant Design specific rows
        "table tbody tr td",           # Table cells
        "table tbody tr:not(.ant-table-measure-row)", # Non-measure rows
    ]
    
    # Try multiple quick checks for the table
    start_time = time.time()
    end_time = start_time + (timeout / 1000)
    poll_interval = 0.1  # 100ms
    
    while time.time() < end_time:
        # Try each selector until one works
        for selector in table_selectors:
            try:
                elements = page.query_selector_all(selector)
                if elements and len(elements) > 1:  # More than header row
                    elapsed = time.time() - start_time
                    logger.info(f"Table found with selector '{selector}' in {elapsed:.2f} seconds")
                    return True
            except Exception:
                continue
                
        # Alternative method: check via JavaScript
        try:
            row_count = page.evaluate("""() => {
                const rows = document.querySelectorAll('table tbody tr:not(.ant-table-measure-row)');
                return rows.length;
            }""")
            
            if row_count > 0:
                elapsed = time.time() - start_time
                logger.info(f"Table with {row_count} rows found via JavaScript in {elapsed:.2f} seconds")
                return True
        except Exception:
            pass
            
        # Wait a bit before trying again
        time.sleep(poll_interval)
    
    # Final check with broader selector
    try:
        # Look for any table-like structure
        any_table = page.evaluate("""() => {
            return Boolean(
                document.querySelector('table') || 
                document.querySelector('.ant-table') ||
                document.querySelector('[role="table"]') ||
                document.querySelector('.ant-table-container')
            );
        }""")
        
        if any_table:
            logger.info("Found table-like structure with final check")
            return True
    except Exception:
        pass
        
    logger.warning(f"Table not detected within {timeout/1000} seconds")
    return False

def get_copied_text(page, button_selector, max_attempts=2, delay=0.3):
    """
    Get text by clicking the copy button and reading from clipboard.
    Includes retry logic with shorter delays.
    """
    for attempt in range(max_attempts):
        try:
            # Clear clipboard first
            page.evaluate("navigator.clipboard.writeText('')")
            
            # Click the copy button
            page.locator(button_selector).click()
            time.sleep(delay)  # Small delay for clipboard to update
            
            # Get content from clipboard
            clipboard_text = page.evaluate("navigator.clipboard.readText()")
            
            if clipboard_text and clipboard_text.startswith("0x"):
                return clipboard_text
                
            logger.warning(f"Attempt {attempt+1}: Empty or invalid clipboard content")
            time.sleep(delay)  # Delay before retry
            
        except Exception as e:
            logger.warning(f"Attempt {attempt+1} failed: {str(e)}")
            time.sleep(delay)  # Delay before retry
    
    # Return a placeholder if all attempts fail
    return "0x...unavailable"

def run(playwright: Playwright):
    # Create a session on Browserbase with extended timeout
    logger.info("Creating Browserbase session...")
    session = bb.sessions.create(
        project_id=browserbase_project_id,
        api_timeout=300  # 5 minutes
    )
    
    logger.info(f"Session created with ID: {session.id}")
    logger.info(f"Connect URL: {session.connect_url}")
    
    # Connect to the browser
    browser = playwright.chromium.connect_over_cdp(
        session.connect_url,
        timeout=30000  # 30 seconds connection timeout
    )
    
    try:
        # Get the context and page
        context = browser.contexts[0]
        page = context.pages[0]
        
        # Set a shorter default timeout for operations
        page.set_default_timeout(15000)  # 15 seconds
        
        # Navigate to the mechs page
        logger.info("Navigating to mechs page...")
        page.goto("https://mech.olas.network/gnosis/mechs", wait_until="domcontentloaded")
        
        # Use our optimized table detection with a 5-second timeout
        table_found = wait_for_table_to_load(page, timeout=5000)
        
        if not table_found:
            # Take a screenshot to see what's on the page
            page.screenshot(path="table_not_found.png")
            logger.warning("Table not detected within 5 seconds, but continuing anyway")
        
        # Even if detection didn't succeed, we'll try to get data
        logger.info("Attempting to extract data from table...")
        
        # Get rows that are not measure rows
        visible_rows = page.query_selector_all("table tbody tr:not(.ant-table-measure-row)")
        if not visible_rows:
            # Try an alternative selector if the first one fails
            visible_rows = page.query_selector_all(".ant-table-tbody tr")
        
        if not visible_rows:
            # Last resort: get any row-like elements
            visible_rows = page.query_selector_all("table tbody tr")
        
        # Filter out any invisible rows
        filtered_rows = [row for row in visible_rows if row.is_visible()]
        logger.info(f"Found {len(filtered_rows)} visible rows")
        
        results = []
        
        # Process each row one by one
        for i, row in enumerate(filtered_rows):
            try:
                # Get cells in this row
                cells = row.query_selector_all("td")
                if not cells or len(cells) < 5:
                    logger.warning(f"Row {i+1} has fewer than 5 cells, skipping")
                    continue
                
                # Extract service ID from the first cell
                service_id_cell = cells[0]
                service_id_link = service_id_cell.query_selector("a")
                if service_id_link:
                    service_id = service_id_link.text_content().strip()
                    service_url = service_id_link.get_attribute("href") or ""
                else:
                    service_id = service_id_cell.text_content().strip()
                    service_url = ""
                
                # Extract owner address by clicking its copy button (cell 1)
                owner_copy_button = cells[1].query_selector("button[aria-label='copy'], .anticon-copy")
                owner_address = "0x..."
                if owner_copy_button:
                    owner_copy_button.click()
                    time.sleep(0.3)
                    owner_address = page.evaluate("navigator.clipboard.readText()")
                else:
                    # Try to get the abbreviated address from the text
                    owner_text = cells[1].text_content().strip()
                    if "0x" in owner_text:
                        owner_address = owner_text
                
                # Extract hash (cell 2)
                hash_cell = cells[2]
                hash_text = hash_cell.text_content().strip()
                hash_value = hash_text if hash_text.lower() != "n/a" else ""
                
                # Extract mech address (cell 3)
                mech_copy_button = cells[3].query_selector("button[aria-label='copy'], .anticon-copy")
                mech_address = "0x..."
                if mech_copy_button:
                    mech_copy_button.click()
                    time.sleep(0.3)
                    mech_address = page.evaluate("navigator.clipboard.readText()")
                else:
                    # Try to get the abbreviated address from the text
                    mech_text = cells[3].text_content().strip()
                    if "0x" in mech_text:
                        mech_address = mech_text
                
                # Extract mech factory (cell 4)
                factory_copy_button = cells[4].query_selector("button[aria-label='copy'], .anticon-copy")
                factory_address = "0x..."
                if factory_copy_button:
                    factory_copy_button.click()
                    time.sleep(0.3)
                    factory_address = page.evaluate("navigator.clipboard.readText()")
                else:
                    # Try to get the abbreviated address from the text
                    factory_text = cells[4].text_content().strip()
                    if "0x" in factory_text:
                        factory_address = factory_text
                
                # Create result object
                result = {
                    "service_id": service_id,
                    "url": service_url,
                    "owner_address": owner_address,
                    "hash": hash_value,
                    "mech_address": mech_address,
                    "mech_factory_address": factory_address
                }
                
                results.append(result)
                logger.info(f"Processed row {i+1}: Service ID {service_id}")
                
            except Exception as e:
                logger.error(f"Error processing row {i+1}: {str(e)}")
                # Continue with the next row
        
        # Format the final output to match list-mech.json structure
        output = {"services": results}
        
        # Save results to JSON file
        output_path = "./mechs_data.json"
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)
        logger.info(f"Data saved to {output_path}")
        
        return output
    
    except PlaywrightTimeoutError as e:
        logger.error(f"Timeout error: {str(e)}")
        # Take a screenshot to help with debugging
        page.screenshot(path="timeout_error.png")
        logger.info("Screenshot saved to timeout_error.png")
        raise
    
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        # Take a screenshot to help with debugging
        try:
            page.screenshot(path="error_screenshot.png")
            logger.info("Screenshot saved to error_screenshot.png")
        except:
            logger.error("Could not save error screenshot")
        raise
    
    finally:
        # Close browser and release Browserbase session
        logger.info("Cleaning up resources...")
        browser.close()
        bb.sessions.update(id=session.id, status="REQUEST_RELEASE")
        logger.info("Browser closed and session released")

def main():
    """
    Main function with retry logic
    """
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            logger.info(f"Attempt {attempt+1}/{max_attempts} to scrape data")
            with sync_playwright() as playwright:
                result = run(playwright)
                logger.info("Scraping completed successfully")
                return result
        except Exception as e:
            logger.error(f"Attempt {attempt+1} failed: {str(e)}")
            if attempt < max_attempts - 1:
                wait_time = 10 * (attempt + 1)  # Increase wait time with each attempt
                logger.info(f"Waiting {wait_time} seconds before next attempt")
                time.sleep(wait_time)
            else:
                logger.error("All attempts failed")
                raise

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
