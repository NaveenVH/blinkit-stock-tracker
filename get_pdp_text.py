from playwright.sync_api import sync_playwright
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

def get_pdp_text():
    lat, lon = 12.9716, 77.5946  # Bangalore
    url = "https://blinkit.com/prn/x/prid/804937"
    
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
        
        print("--- Inner text of PDP ---")
        text = page.locator("body").inner_text()
        print(text)
        
        # Let's inspect the main container where the purchase card is
        # We can find all elements that contain the string "804937" or are near the title
        # E.g. find all headings or bold texts or elements with price symbol
        print("\n--- Listing elements with price or stock text ---")
        info = page.evaluate("""() => {
            const results = [];
            // Find divs containing '₹179' or similar
            document.querySelectorAll('div, h1, h2, h3, h4, span, button').forEach(el => {
                const txt = el.innerText || "";
                if (txt.includes('₹') && txt.length < 50 && el.children.length === 0) {
                    results.push({
                        tag: el.tagName,
                        class: el.className,
                        text: txt,
                        parent_text: el.parentElement ? el.parentElement.innerText.substring(0, 200).replace(/\\n/g, ' ') : ""
                    });
                }
            });
            return results;
        }""")
        
        for item in info[:20]:
            print(f"Tag: {item['tag']}, Class: {repr(item['class'])}, Text: {repr(item['text'])}")
            print(f"  Parent: {repr(item['parent_text'])}")
            
        browser.close()

if __name__ == "__main__":
    get_pdp_text()

