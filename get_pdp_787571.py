from playwright.sync_api import sync_playwright
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

def get_pdp_787571_text():
    lat, lon = 12.9716, 77.5946  # Bangalore
    url = "https://blinkit.com/prn/x/prid/787571"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            geolocation={"latitude": lat, "longitude": lon},
            permissions=["geolocation"]
        )
        page = context.new_page()
        
        # Resolve location first
        page.goto("https://blinkit.com/", wait_until="domcontentloaded")
        time.sleep(4)
        
        # Load PDP
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(5)
        
        # Save a screenshot to visually verify what is on the screen
        page.screenshot(path="debug_787571.png")
        print("Saved debug_787571.png")
        
        print("--- Inner text of PDP 787571 ---")
        text = page.locator("body").inner_text()
        print(text[:2000]) # First 2000 chars of body text
        
        # Find all divs and buttons in the main details block
        print("\n--- Main Title Selector and Parent Traverse ---")
        pdp_data = page.evaluate("""() => {
            let titleEl = Array.from(document.querySelectorAll('div.tw-font-extrabold')).find(el => el.innerText !== 'Product Details');
            if (!titleEl) {
                titleEl = document.querySelector('[class*="BreadcrumbProductName"]') || document.querySelector('h1');
            }
            if (!titleEl) return "No Title Element Found";
            
            let container = titleEl;
            let foundText = "";
            let depth = 0;
            
            while (container && container.tagName !== 'BODY' && depth < 6) {
                foundText += `[Level ${depth}] Tag: ${container.tagName}, Text Snippet: ${container.innerText.substring(0, 150).replace(/\\n/g, ' ')}\\n`;
                container = container.parentElement;
                depth++;
            }
            return foundText;
        }""")
        print(pdp_data)
        
        browser.close()

if __name__ == "__main__":
    get_pdp_787571_text()

