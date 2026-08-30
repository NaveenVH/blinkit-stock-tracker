from playwright.sync_api import sync_playwright
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

def debug_crawl():
    lat, lon = 12.9716, 77.5946  # Bangalore
    url = "https://blinkit.com/s/?q=Amul+Gold+Full+Cream+Milk"
    
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
        
        # Monitor console messages
        page.on("console", lambda msg: print(f"Browser Console: {msg.text}"))
        
        print(f"Navigating to {url}...")
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        
        # Save screenshot immediately after DOMContentLoaded
        page.screenshot(path="debug_domcontentloaded.png")
        print("Saved debug_domcontentloaded.png")
        
        print("Waiting 5 seconds for page load and hydration...")
        time.sleep(5)
        
        page.screenshot(path="debug_hydrated.png")
        print("Saved debug_hydrated.png")
        
        # Print some HTML snippets to see what elements are present
        print("\n--- Inner text of the body ---")
        body_text = page.locator("body").inner_text()
        print(body_text[:1000])
        
        # Check if there are links containing '/prn/'
        prn_links = page.locator('a[href*="/prn/"]').count()
        print(f"\nNumber of '/prn/' links: {prn_links}")
        
        # Check if there is a location selection dialog
        print("\nChecking for dialogs/modals...")
        modals = page.locator("div:has-text('Select Location')").count()
        print(f"Elements containing 'Select Location': {modals}")
        
        browser.close()

if __name__ == "__main__":
    debug_crawl()

