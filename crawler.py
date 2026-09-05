from curl_cffi import requests
import re

def crawl_stock(latitude, longitude, target_product_id):
    """
    Fetches product stock info using TLS-impersonated HTTP GET requests (Chrome 120 fingerprint).
    Bypasses Cloudflare 403 blocks on cloud hosting providers.
    
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
    
    print(f"Starting TLS-impersonated check for Product ID: {target_product_id} at ({latitude}, {longitude})")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "lat": str(latitude),
        "lon": str(longitude)
    }
    
    try:
        # impersonate="chrome120" mimics a real desktop browser TLS handshake
        response = requests.get(direct_url, headers=headers, impersonate="chrome120", timeout=12)
        
        if response.status_code == 200:
            html = response.text
            
            # 1. Parse Product Name
            name_match = re.search(r'"product_name":"([^"]+)"', html) or re.search(r'"display_name":"([^"]+)"', html)
            product_name = name_match.group(1) if name_match else None
            
            # 2. Parse Price
            price_match = re.search(r'"price":(\d+)', html)
            price = f"₹{price_match.group(1)}" if price_match else None
            
            # 3. Parse Stock Status
            status_match = re.search(r'"product_state":"([^"]+)"', html) or re.search(r'"state":"([^"]+)"', html)
            state_val = status_match.group(1) if status_match else "unknown"
            
            # Map state
            status = "in_stock" if state_val in ["available", "in_stock"] else "out_of_stock"
            
            result["success"] = True
            result["matched_title"] = product_name
            result["price"] = price
            result["status"] = status
            
            print(f"[+] TLS check succeeded: '{product_name}' | price='{price}' | status='{status}'")
            
        else:
            result["error"] = f"HTTP request failed with status code {response.status_code}"
            
    except Exception as e:
        result["error"] = f"HTTP request exception: {str(e)}"
        
    return result
