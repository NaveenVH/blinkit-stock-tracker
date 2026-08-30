from playwright.sync_api import sync_playwright
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

def find_title_tag():
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
        
        page.goto("https://blinkit.com/", wait_until="domcontentloaded")
        time.sleep(4)
        
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(5)
        
        # Find elements containing "Pontiac Firebird"
        elements = page.evaluate("""() => {
            const results = [];
            // Find all elements containing the text
            const allElements = document.querySelectorAll('*');
            allElements.forEach(el => {
                const text = el.innerText || "";
                if (text.includes('Pontiac Firebird') && el.children.length === 0) {
                    results.push({
                        tag: el.tagName,
                        className: el.className,
                        text: text,
                        parentTag: el.parentElement ? el.parentElement.tagName : "",
                        parentClass: el.parentElement ? el.parentElement.className : ""
                    });
                }
            });
            return results;
        }""")
        
        print("--- Elements containing 'Pontiac Firebird' ---")
        for el in elements:
            print(f"Tag: {el['tag']}, Class: {repr(el['className'])}, Text: {repr(el['text'])}")
            print(f"  Parent Tag: {el['parentTag']}, Parent Class: {repr(el['parentClass'])}")
            
        browser.close()

if __name__ == "__main__":
    find_title_tag()

