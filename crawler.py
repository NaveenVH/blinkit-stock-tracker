from curl_cffi import requests
import re
import time
import random

def crawl_stock(latitude, longitude, target_product_id):
    """
    Fetches product stock info using TLS-impersonated HTTP GET requests.
    Includes rate-limit delays and retry backoff logic to handle Cloudflare 403 bursts.
    
    Returns:
        dict: {
            "success": bool,
            "matched_title": str or None,
            "description": str or None,
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
        "description": None,
        "price": None,
        "status": "unknown",
        "link": direct_url,
        "error": None
    }
    
    print(f"Starting TLS-impersonated check for Product ID: {target_product_id} at ({latitude}, {longitude})")
    
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
    ]
    
    impersonate_targets = ["chrome120", "chrome119", "chrome110"]
    
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        headers = {
            "User-Agent": random.choice(user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "lat": str(latitude),
            "lon": str(longitude)
        }
        
        # Small human-like pacing delay before request
        time.sleep(random.uniform(1.2, 2.5))
        
        try:
            target_profile = impersonate_targets[(attempt - 1) % len(impersonate_targets)]
            response = requests.get(direct_url, headers=headers, impersonate=target_profile, timeout=12)
            
            if response.status_code == 200:
                html = response.text
                
                # 1. Parse Product Name
                name_match = re.search(r'"product_name":"([^"]+)"', html) or re.search(r'"display_name":"([^"]+)"', html) or re.search(r'<title>([^<]+)</title>', html)
                product_name = name_match.group(1) if name_match else None
                if product_name and "Blinkit" in product_name and "Buy" in product_name:
                    product_name = product_name.split("Online at")[0].replace("Buy", "").strip()

                # 2. Parse Description
                desc_match = (
                    re.search(r'"description":"([^"]+)"', html) or
                    re.search(r'<meta\s+(?:name|property)=["\'](?:description|og:description)["\']\s+content=["\']([^"\']+)["\']', html, re.IGNORECASE) or
                    re.search(r'<meta\s+content=["\']([^"\']+)["\']\s+(?:name|property)=["\'](?:description|og:description)["\']', html, re.IGNORECASE)
                )
                description = desc_match.group(1).replace("\\n", " ").replace('\\"', '"').strip() if desc_match else None
                
                # 3. Parse Price
                price_match = re.search(r'"price":(\d+)', html)
                price = f"₹{price_match.group(1)}" if price_match else None
                
                # 4. Parse Stock Status
                status_match = re.search(r'"product_state":"([^"]+)"', html) or re.search(r'"state":"([^"]+)"', html)
                state_val = status_match.group(1) if status_match else "unknown"
                
                # Map state
                status = "in_stock" if state_val in ["available", "in_stock"] else "out_of_stock"
                
                result["success"] = True
                result["matched_title"] = product_name
                result["description"] = description
                result["price"] = price
                result["status"] = status
                
                print(f"[+] TLS check succeeded (Attempt {attempt}): '{product_name}' | price='{price}' | status='{status}'")
                break
                
            elif response.status_code == 403 and attempt < max_retries:
                backoff_sec = attempt * 3.0
                print(f"[-] Received HTTP 403 (Rate-limit burst). Retrying in {backoff_sec} seconds (Attempt {attempt}/{max_retries})...")
                time.sleep(backoff_sec)
            else:
                result["error"] = f"HTTP request failed with status code {response.status_code}"
                
        except Exception as e:
            if attempt < max_retries:
                time.sleep(attempt * 2)
            else:
                result["error"] = f"HTTP request exception: {str(e)}"
                
    return result
