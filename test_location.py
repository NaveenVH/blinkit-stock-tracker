from playwright.sync_api import sync_playwright
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

def test_location_resolution():
    # Bangalore coordinates
    lat, lon = 12.9716, 77.5946
    
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            geolocation={"latitude": lat, "longitude": lon},
            permissions=["geolocation"]
        )
        page = context.new_page()
        
        print("Navigating to homepage...")
        page.goto("https://blinkit.com/", wait_until="domcontentloaded")
        time.sleep(3)
        
        # Take initial screenshot
        page.screenshot(path="loc_1_initial.png")
        
        # Print initial resolved address text
        body_text = page.locator("body").inner_text()
        print("Initial page text (first 500 chars):")
        print(body_text[:500].replace('\n', ' | '))
        
        # Trigger location detection
        try:
            # Let's check if the address modal is open or if we have a direct button
            detect_btn = page.locator("button:has-text('Detect my location'), [class*='Location']:has-text('Detect')").first
            if detect_btn.is_visible():
                print("Clicking visible 'Detect my location' button...")
                detect_btn.click()
            else:
                print("'Detect my location' button not directly visible. Clicking address header...")
                # Find the location display. It usually says "Delivering in" or "Delivery to" or displays the current address at the top.
                # Let's search for the element that has the current address (e.g. "Sector 50" or "Gurugram" or "Delivering")
                # We can click the header address container.
                # Let's find any element containing "TOWER-C" or "Gurugram" or "Delivering" and click it
                location_header = page.locator("div:has-text('Delivering to'), div:has-text('Delivery in'), div:has-text('Gurugram')").first
                location_header.click()
                time.sleep(2)
                page.screenshot(path="loc_2_modal_open.png")
                
                print("Clicking 'Detect my location' in the modal...")
                page.locator("text=Detect my location").first.click()
                
            time.sleep(5) # Wait for location to update
            page.screenshot(path="loc_3_updated.png")
            
            # Print updated resolved address text
            updated_text = page.locator("body").inner_text()
            print("\nUpdated page text (first 500 chars):")
            print(updated_text[:500].replace('\n', ' | '))
            
        except Exception as e:
            print("Error selecting location:", e)
            
        # Try loading PDP for 787571
        print("\nNavigating to product page 787571...")
        page.goto("https://blinkit.com/prn/x/prid/787571", wait_until="domcontentloaded")
        time.sleep(5)
        page.screenshot(path="loc_4_pdp.png")
        
        print("\n--- PDP Page Text ---")
        pdp_text = page.locator("body").inner_text()
        print(pdp_text[:1000])
        
        browser.close()

if __name__ == "__main__":
    test_location_resolution()

