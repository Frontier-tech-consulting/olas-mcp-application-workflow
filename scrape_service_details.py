import os
import json
import time
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
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

# Load the existing mechs data
def load_mechs_data(file_path: str = "./mechs_data.json") -> List[Dict[str, Any]]:
    """Load the existing mechs data from JSON file."""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            return data.get("services", [])
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return []
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in file: {file_path}")
        return []

def get_text_safe(page, selector: str, timeout: int = 5000) -> str:
    """Safely get text content from a selector with a timeout."""
    try:
        element = page.wait_for_selector(selector, timeout=timeout)
        if element:
            return element.text_content().strip()
        return ""
    except Exception as e:
        logger.debug(f"Error getting text from {selector}: {str(e)}")
        return ""

def get_attribute_safe(page, selector: str, attribute: str, timeout: int = 5000) -> str:
    """Safely get attribute from a selector with a timeout."""
    try:
        element = page.wait_for_selector(selector, timeout=timeout)
        if element:
            return element.get_attribute(attribute) or ""
        return ""
    except Exception as e:
        logger.debug(f"Error getting attribute {attribute} from {selector}: {str(e)}")
        return ""

def extract_service_details(page, service_id: str) -> Dict[str, Any]:
    """Extract detailed information from a service page based on the given HTML structure."""
    logger.info(f"Extracting details for service {service_id}")
    
    # Initialize details dictionary
    details = {
        "service_id": service_id,
        "description": "",
        "codebase_link": "",
        "hash_link": "",
        "threshold": "",
        "state_change_json": "",
        "owner_address": "",
        "version": "",
        "safe_address": ""
    }
    
    try:
        # Wait for page to load key elements - service title header
        page.wait_for_selector("h2.ant-typography", timeout=50000)
        
        # Extract description - based on the provided HTML structure
        description_selector = "div[data-testid='description']"
        details["description"] = get_text_safe(page, description_selector)
        
        # Extract hash link - from the "View Hash" link
        hash_link_selector = "a[data-testid='view-hash-link']"
        details["hash_link"] = get_attribute_safe(page, hash_link_selector, "href")
        
        # Extract codebase link - from the "View Code" link
        codebase_link_selector = "a[data-testid='view-code-link']"
        details["codebase_link"] = get_attribute_safe(page, codebase_link_selector, "href")
        
        # Extract threshold
        threshold_selector = "span:has-text('Threshold') + div"
        details["threshold"] = get_text_safe(page, threshold_selector)
        
        # Extract owner address
        owner_address_selector = "div[data-testid='owner-address']"
        details["owner_address"] = get_text_safe(page, owner_address_selector)
        
        # Extract version
        version_selector = "div[data-testid='version']"
        details["version"] = get_text_safe(page, version_selector)
        
        # Extract Safe address - this is in the deployed section
        safe_address_text = get_text_safe(page, ".ant-flex:has-text('Safe contract address:')")
        if safe_address_text:
            # Extract just the address part
            parts = safe_address_text.split(":")
            if len(parts) > 1:
                # The address text includes the '↗' symbol, so we'll clean it
                address_part = parts[1].strip()
                # Remove the arrow symbol if present
                details["safe_address"] = address_part.replace("↗", "").strip()
        
        # Extract state change JSON - looking for a pre tag within a collapsible content box
        # Note: The HTML doesn't show the actual state change JSON, so we need to look for it
        # This might be visible when clicking on something or in a different section
        state_change_selector = "div.ant-collapse-content-box pre"
        state_change_text = get_text_safe(page, state_change_selector)
        
        if state_change_text:
            details["state_change_json"] = state_change_text.strip()
        else:
            # As a fallback, try to find any JSON-like content in the page
            # Look for a pre tag that might contain JSON
            pre_tags = page.query_selector_all("pre")
            for pre in pre_tags:
                text = pre.text_content().strip()
                if text.startswith("{") and text.endswith("}"):
                    details["state_change_json"] = text
                    break
        
        # Get service status
        status_selector = "div[data-testid='service-status'] span"
        details["status"] = get_text_safe(page, status_selector)
        
        logger.info(f"Successfully extracted details for service {service_id}")
    except Exception as e:
        logger.error(f"Error extracting details for service {service_id}: {str(e)}")
    
    return details

def run(playwright: Playwright, services: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run the scraping process for all service pages."""
    # Create a session on Browserbase
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
        timeout=60000  # 60 seconds connection timeout
    )
    
    enriched_services = []
    
    try:
        # Get the context and page
        context = browser.contexts[0]
        page = context.pages[0]
        
        # Set a reasonable default timeout for page operations
        page.set_default_timeout(30000)  # 30 seconds
        
        # Keep track of processed services to save progress incrementally
        processed_count = 0
        
        for service in services:
            service_id = service.get("service_id")
            url = service.get("url")
            
            if not url:
                logger.warning(f"No URL found for service {service_id}, skipping")
                enriched_services.append(service)
                continue
            
            try:
                # Navigate to the service page
                logger.info(f"Navigating to service page: {url}")
                page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Extract details from the service page
                service_details = extract_service_details(page, service_id)
                
                # Merge the original service data with the new details
                enriched_service = {**service, **service_details}
                enriched_services.append(enriched_service)
                
                # Save progress every 2 services to avoid data loss
                processed_count += 1
                if processed_count % 2 == 0:
                    try:
                        output_path = "./enriched_services_data.json"
                        with open(output_path, "w") as f:
                            json.dump({"services": enriched_services}, f, indent=2)
                        logger.info(f"Progress saved after processing {processed_count} services")
                    except Exception as save_error:
                        logger.error(f"Failed to save progress: {str(save_error)}")
                
                # Add a small delay between page navigations
                time.sleep(1.5)
                
            except Exception as e:
                logger.error(f"Error processing service {service_id}: {str(e)}")
                # If there's an error, keep the original service data
                enriched_services.append(service)
                
                # Take a screenshot to help debug the issue
                try:
                    screenshot_path = f"error_service_{service_id}.png"
                    page.screenshot(path=screenshot_path)
                    logger.info(f"Screenshot saved to {screenshot_path}")
                except:
                    logger.error("Could not save error screenshot")
        
        logger.info(f"Processed {len(enriched_services)} services")
        return enriched_services
    
    except PlaywrightTimeoutError as e:
        logger.error(f"Timeout error: {str(e)}")
        # Take a screenshot to help debug the issue
        try:
            page.screenshot(path="timeout_error.png")
            logger.info("Screenshot saved to timeout_error.png")
        except:
            logger.error("Could not save timeout error screenshot")
        return enriched_services  # Return whatever data we collected so far
    
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        # Take a screenshot to help debug the issue
        try:
            page.screenshot(path="error_screenshot.png")
            logger.info("Screenshot saved to error_screenshot.png")
        except:
            logger.error("Could not save error screenshot")
        return enriched_services  # Return whatever data we collected so far
    
    finally:
        # Always clean up resources
        logger.info("Cleaning up resources...")
        try:
            browser.close()
            # Fix: Add the required project_id parameter
            bb.sessions.update(
                id=session.id, 
                project_id=browserbase_project_id,
                status="REQUEST_RELEASE"
            )
            logger.info("Browser closed and session released")
        except Exception as cleanup_error:
            logger.error(f"Error during resource cleanup: {str(cleanup_error)}")

def main():
    """Main function with a single attempt for each service."""
    # Load the existing mechs data
    services = load_mechs_data()
    
    if not services:
        logger.error("No services found in mechs_data.json")
        return
    
    logger.info(f"Loaded {len(services)} services from mechs_data.json")
    
    enriched_services = []
    
    try:
        logger.info("Starting to scrape service details")
        with sync_playwright() as playwright:
            enriched_services = run(playwright, services)
            
            # Save the enriched data to a new JSON file
            output_path = "./enriched_services_data.json"
            with open(output_path, "w") as f:
                json.dump({"services": enriched_services}, f, indent=2)
            
            logger.info(f"Enriched data saved to {output_path}")
    except Exception as e:
        logger.error(f"Scraping failed: {str(e)}")
    finally:
        # Always save whatever data we have, even if there was an error
        if enriched_services:
            try:
                output_path = "./enriched_services_data.json"
                with open(output_path, "w") as f:
                    json.dump({"services": enriched_services}, f, indent=2)
                logger.info(f"Data saved to {output_path} in finally block")
            except Exception as save_error:
                logger.error(f"Failed to save data in finally block: {str(save_error)}")

if __name__ == "__main__":
    main()
