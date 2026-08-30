from playwright.sync_api import sync_playwright
import time
import json
import sys

# Configure stdout to support UTF-8 characters (like the Rupee symbol ₹)
sys.stdout.reconfigure(encoding='utf-8')

def run():
    # Gurugram coordinates (latitude, longitude)
    lat, lon = 28.4595, 77.0266
    
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        
        # Create a browser context with mock geolocation
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            geolocation={"latitude": lat, "longitude": lon},
            permissions=["geolocation"]
        )
        
        page = context.new_page()
        
        print("Navigating to Blinkit...")
        page.goto("https://blinkit.com/", wait_until="networkidle")
        time.sleep(3)  # Wait for any geo-detection scripts to execute
        
        # Save a screenshot of the landing page
        page.screenshot(path="landing_page.png")
        print("Saved landing_page.png")
            
        print("Navigating to search results page for 'Amul Gold Milk'...")
        search_url = "https://blinkit.com/s/?q=Amul+Gold+Milk"
        page.goto(search_url, wait_until="networkidle")
        time.sleep(5)  # Wait for search results to load
        
        page.screenshot(path="search_results.png")
        print("Saved search_results.png")
        
        print("Parsing products...")
        
        # Run browser-side parsing to extract text elements
        products = page.evaluate("""() => {
            const cards = [];
            
            // Look for any links containing /prn/ (product details page)
            const productLinks = document.querySelectorAll('a[href*="/prn/"]');
            
            productLinks.forEach(link => {
                const text = link.innerText || "";
                if (!text.includes('₹')) return;
                
                const lines = text.split('\\n').map(l => l.trim()).filter(Boolean);
                cards.push({
                    href: link.href,
                    text: text,
                    lines: lines
                });
            });
            
            // Fallback: look for divs that might be product cards
            if (cards.length === 0) {
                const divs = document.querySelectorAll('div');
                divs.forEach(div => {
                    const txt = div.innerText || "";
                    // Product cards typically contain Rupee symbol and "ADD" or "Out of Stock"
                    if (txt.includes('₹') && (txt.includes('ADD') || txt.includes('Out of Stock') || txt.includes('ADD TO CART'))) {
                        const lines = txt.split('\\n').map(l => l.trim()).filter(Boolean);
                        // Prevent adding the same block multiple times by checking length
                        if (lines.length > 2 && lines.length < 8) {
                            cards.push({
                                text: txt,
                                lines: lines
                            });
                        }
                    }
                });
            }
            
            return cards;
        }""")
        
        print(f"Found {len(products)} potential product elements.")
        
        # Deduplicate results by their inner text content
        seen = set()
        dedup_products = []
        for p_item in products:
            p_text = " ".join(p_item.get("lines", []))
            if p_text not in seen:
                seen.add(p_text)
                dedup_products.append(p_item)
                
        print(f"Deduplicated to {len(dedup_products)} product elements.")
        
        for idx, p_item in enumerate(dedup_products[:10]):
            print(f"\nProduct {idx+1}:")
            print("  Lines:", p_item.get("lines"))
            if p_item.get("href"):
                print("  Link:", p_item.get("href"))
                
        browser.close()

if __name__ == "__main__":
    run()

