from playwright.sync_api import sync_playwright
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

def find_all_batmobiles():
    lat, lon = 12.9716, 77.5946  # Bangalore
    url = "https://blinkit.com/s/?q=Hot+Wheels+Batmobile"
    
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
        
        print(f"Navigating to search page: {url}...")
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(5)
        
        raw_products = page.evaluate(r"""() => {
            const cards = [];
            const productLinks = document.querySelectorAll('a[href*="/prn/"]');
            
            productLinks.forEach(link => {
                const text = link.innerText || "";
                if (!text.includes('₹')) return;
                
                const lines = text.split('\n').map(l => l.trim()).filter(Boolean);
                cards.push({
                    href: link.href,
                    lines: lines
                });
            });
            
            if (cards.length === 0) {
                const divs = document.querySelectorAll('div');
                divs.forEach(div => {
                    const txt = div.innerText || "";
                    if (txt.includes('₹') && (txt.includes('ADD') || txt.includes('Out of Stock') || txt.includes('ADD TO CART'))) {
                        const lines = txt.split('\n').map(l => l.trim()).filter(Boolean);
                        if (lines.length > 2 && lines.length < 8) {
                            cards.push({
                                href: null,
                                lines: lines
                            });
                        }
                    }
                });
            }
            return cards;
        }""")
        
        browser.close()
        
        seen = set()
        dedup_products = []
        for p_item in raw_products:
            p_text = " ".join(p_item.get("lines", []))
            if p_text not in seen:
                seen.add(p_text)
                dedup_products.append(p_item)
                
        print(f"\n--- Found {len(dedup_products)} unique product cards ---")
        for idx, item in enumerate(dedup_products):
            lines = item.get("lines", [])
            href = item.get("href", "N/A")
            print(f"Card {idx+1}:")
            print(f"  URL: {href}")
            print(f"  Content: {lines}")

if __name__ == "__main__":
    find_all_batmobiles()

