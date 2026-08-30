from playwright.sync_api import sync_playwright
import time

def crawl_stock(latitude, longitude, target_product_id):
    """
    Launches a Playwright browser, mocks the geolocation coordinates,
    goes directly to the Product Detail Page (PDP), and extracts stock/price info.
    
    Returns:
        dict: {
            "success": bool,
            "matched_title": str or None,
            "price": str or None,
            "status": "in_stock" | "out_of_stock" | "unknown",
            "link": str or None,
            "error": str or None
        }
    """
    direct_url = f"https://blinkit.com/prn/x/prid/{target_product_id}"
    
    result = {
        "success": False,
        "matched_title": None,
        "price": None,
        "status": "unknown",
        "link": direct_url,
        "error": None
    }
    
    print(f"Starting crawl for Product ID: {target_product_id} at coordinates: ({latitude}, {longitude})")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                geolocation={"latitude": float(latitude), "longitude": float(longitude)},
                permissions=["geolocation"]
            )
            
            page = context.new_page()
            
            # 1. Navigate to Homepage and Force Location Resolution
            print("Navigating to homepage to set location...")
            page.goto("https://blinkit.com/", wait_until="domcontentloaded", timeout=30000)
            
            try:
                # Wait for the main "Detect my location" button to render (up to 8s)
                detect_btn = page.locator("button:has-text('Detect my location'), [class*='Location']:has-text('Detect')").first
                
                try:
                    # Wait for it to become visible
                    detect_btn.wait_for(state="visible", timeout=8000)
                    print("Clicking visible 'Detect my location' button...")
                    detect_btn.click()
                except Exception:
                    # If direct detect button is not visible, try opening the location sidebar
                    print("Direct detect button not visible. Trying location header selector...")
                    location_header = page.locator("div:has-text('Delivering to'), div:has-text('Delivery in'), div:has-text('Select Location'), div:has-text('Gurugram')").first
                    location_header.wait_for(state="visible", timeout=8000)
                    location_header.click()
                    time.sleep(2)
                    
                    # Click "Detect my location" inside the modal/sidebar
                    modal_detect_btn = page.locator("text=Detect my location").first
                    modal_detect_btn.wait_for(state="visible", timeout=5000)
                    modal_detect_btn.click()
                
                # Wait for location coordinates to apply
                time.sleep(6)
                
                # Print resolved address info
                body_text = page.locator("body").inner_text()
                first_line = body_text.split('\n')[0] if body_text else ""
                second_line = body_text.split('\n')[1] if body_text and len(body_text.split('\n')) > 1 else ""
                print(f"Location resolved: {first_line} | {second_line}")
                
            except Exception as le:
                print(f"Warning: Could not force location resolution: {le}")
            
            # 2. Check stock on direct Product Detail Page (PDP)
            print(f"Navigating to direct Product Page: {direct_url}...")
            page.goto(direct_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(5)  # Wait for price and stock fields to hydrate
            
            # Extract text and button info from product detail page
            pdp_data = page.evaluate(r"""() => {
                let titleEl = Array.from(document.querySelectorAll('div.tw-font-extrabold')).find(el => el.innerText !== 'Product Details');
                if (!titleEl) {
                    titleEl = document.querySelector('[class*="BreadcrumbProductName"]') || 
                              document.querySelector('h1');
                }
                                
                if (!titleEl) return null;
                
                let container = titleEl;
                let hasAdd = false;
                let hasOos = false;
                let found = false;
                
                while (container && container.tagName !== 'BODY') {
                    const txt = container.innerText || "";
                    hasAdd = txt.includes('ADD') || txt.includes('ADD TO CART');
                    const txtLower = txt.toLowerCase();
                    hasOos = txtLower.includes('out of stock') || 
                             txtLower.includes('currently unavailable') || 
                             txtLower.includes('coming soon');
                    
                    if (hasAdd || hasOos) {
                        found = true;
                        break;
                    }
                    container = container.parentElement;
                }
                
                if (!found) {
                    const bodyText = document.body.innerText || "";
                    hasAdd = bodyText.includes('ADD') || bodyText.includes('ADD TO CART');
                    const bodyLower = bodyText.toLowerCase();
                    hasOos = bodyLower.includes('out of stock') || 
                             bodyLower.includes('currently unavailable') || 
                             bodyLower.includes('coming soon');
                    found = true;
                    container = document.body;
                }
                
                const lines = (container.innerText || "").split('\n').map(l => l.trim()).filter(Boolean);
                
                return {
                    success: found,
                    title: titleEl.innerText,
                    lines: lines,
                    hasAdd: hasAdd,
                    hasOos: hasOos
                };
            }""")
            
            browser.close()
            
            if pdp_data and pdp_data.get("success"):
                pdp_lines = pdp_data.get("lines", [])
                matched_title = pdp_data.get("title")
                
                # Find price: look for element containing ₹ on the page
                price_text = None
                for line in pdp_lines[:50]:
                    if "₹" in line and len(line) < 15:
                        price_text = line
                        break
                
                # Exact status logic: Out of stock/Coming soon dominates if present
                status = "out_of_stock" if pdp_data.get("hasOos") else ("in_stock" if pdp_data.get("hasAdd") else "out_of_stock")
                
                result["success"] = True
                result["matched_title"] = matched_title
                result["price"] = price_text
                result["status"] = status
            else:
                result["error"] = "Could not parse product page details."
                
    except Exception as e:
        result["error"] = f"Exception occurred during crawling: {str(e)}"
        
    return result
