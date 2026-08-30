from playwright.sync_api import sync_playwright
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

def inspect_pdp():
    lat, lon = 12.9716, 77.5946  # Bangalore
    url = "https://blinkit.com/prn/x/prid/804937"
    
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
        
        print("Navigating to homepage to resolve location...")
        page.goto("https://blinkit.com/", wait_until="domcontentloaded")
        time.sleep(4)
        
        print(f"Navigating to product page: {url}...")
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(5)
        
        # Save a screenshot to inspect visually (optional, we have log text)
        page.screenshot(path="debug_pdp.png")
        print("Saved debug_pdp.png")
        
        # Find all buttons on the page and print their texts and classes/tags
        print("\n--- Listing all buttons and clickable elements ---")
        elements_info = page.evaluate("""() => {
            const elements = [];
            
            // Look for buttons
            document.querySelectorAll('button').forEach(btn => {
                elements.push({
                    type: 'button',
                    text: btn.innerText || "",
                    className: btn.className,
                    html: btn.outerHTML.substring(0, 150)
                });
            });
            
            // Look for divs that have class containing 'btn' or 'button' or look like add button
            document.querySelectorAll('div').forEach(div => {
                const text = div.innerText || "";
                if (text === 'ADD' || text === 'Out of Stock' || text === 'Currently Unavailable') {
                    elements.push({
                        type: 'div_btn',
                        text: text,
                        className: div.className,
                        html: div.outerHTML.substring(0, 150)
                    });
                }
            });
            
            return elements;
        }""")
        
        for idx, el in enumerate(elements_info):
            print(f"Element {idx+1}: type={el['type']}, text={repr(el['text'])}, class={repr(el['className'])}")
            print(f"  HTML: {el['html']}")
            
        # Let's inspect the layout of the product page wrapper
        print("\n--- Inspecting elements containing the product title ---")
        titles_info = page.evaluate("""() => {
            const list = [];
            document.querySelectorAll('h1').forEach(h1 => {
                // Find sibling or parent container elements that deal with buying/add
                let parent = h1.parentElement;
                let siblingsText = "";
                if (parent) {
                    siblingsText = parent.innerText;
                }
                list.push({
                    text: h1.innerText,
                    parentText: siblingsText.substring(0, 500)
                });
            });
            return list;
        }""")
        
        for idx, t in enumerate(titles_info):
            print(f"H1 {idx+1}: {repr(t['text'])}")
            print(f"  Container Inner Text (first 500 chars):\n{t['parentText']}")
            
        browser.close()

if __name__ == "__main__":
    inspect_pdp();

