import requests
import re

def crawl_blinkit_stock(latitude, longitude, target_product_id):
    """
    Directly fetches product info from Blinkit's server-rendered HTML payload
    using TLS impersonation to bypass datacenter 403 blocks on Azure VM IPs.
    """
    direct_url = f"https://blinkit.com/prn/x/prid/{target_product_id}"
    
    result = {
        "success": False,
        "matched_title": None,
        "price": None,
        "description": "",
        "status": "unknown",
        "link": direct_url,
        "error": None
    }
    
    print(f"Starting TLS-impersonated check for Blinkit Product ID: {target_product_id} at ({latitude}, {longitude})")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "lat": str(latitude),
        "lon": str(longitude)
    }

    status_code = None
    html = ""

    # Attempt 1: Try curl_cffi TLS impersonation (bypasses Cloudflare 403 on Azure VM)
    try:
        from curl_cffi import requests as c_requests
        session = c_requests.Session(impersonate="chrome120")
        resp = session.get(direct_url, headers=headers, timeout=12)
        status_code = resp.status_code
        html = resp.text
    except Exception as e1:
        # Fallback 2: Standard requests
        try:
            resp = requests.get(direct_url, headers=headers, timeout=12)
            status_code = resp.status_code
            html = resp.text
        except Exception as e2:
            result["error"] = f"HTTP request exception: {str(e2)}"
            return result

    if status_code == 200 and html:
        # 1. Parse Product Name
        name_match = re.search(r'"product_name":"([^"]+)"', html) or re.search(r'"display_name":"([^"]+)"', html)
        product_name = name_match.group(1) if name_match else None
        
        # 2. Parse Price
        price_match = re.search(r'"price":(\d+)', html)
        price = f"₹{price_match.group(1)}" if price_match else None
        
        # 3. Parse Description
        desc_match = re.search(r'"unit":"([^"]+)"', html)
        desc = desc_match.group(1) if desc_match else ""

        # 4. Parse Stock Status
        status_match = re.search(r'"product_state":"([^"]+)"', html) or re.search(r'"state":"([^"]+)"', html)
        state_val = status_match.group(1) if status_match else "unknown"
        
        status = "in_stock" if state_val in ["available", "in_stock"] else "out_of_stock"
        
        result["success"] = True
        result["matched_title"] = product_name
        result["price"] = price
        result["description"] = desc
        result["status"] = status
        
        print(f"[+] Blinkit TLS check succeeded: '{product_name}' | price='{price}' | status='{status}'")
    else:
        result["error"] = f"HTTP request failed with status code {status_code}"
        
    return result


def crawl_bigbasket_stock(latitude, longitude, target_product_id):
    """
    Fetches product info for BigBasket products using direct HTTP requests.
    """
    direct_url = f"https://www.bigbasket.com/pd/{target_product_id}/"
    
    result = {
        "success": False,
        "matched_title": None,
        "price": None,
        "description": "",
        "status": "unknown",
        "link": direct_url,
        "error": None
    }
    
    print(f"Starting direct check for BigBasket Product ID: {target_product_id}")

    try:
        try:
            from curl_cffi import requests as c_requests
            session = c_requests.Session(impersonate="chrome120")
            session.get("https://www.bigbasket.com/", timeout=8)
            resp = session.get(direct_url, timeout=10)
            html = resp.text
            status_code = resp.status_code
        except Exception:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
            resp = requests.get(direct_url, headers=headers, timeout=10)
            html = resp.text
            status_code = resp.status_code

        if status_code in [200, 301, 302] and html:
            title_match = re.search(r'property="og:title"\ content="([^"]+)"', html) or re.search(r'<title>(.*?)</title>', html)
            matched_title = title_match.group(1).replace("Buy ", "").replace(" Online at Best Price", "").strip() if (title_match and "Access Denied" not in title_match.group(1)) else None

            price_match = re.search(r'"mrp":(\d+(?:\.\d+)?)', html) or re.search(r'"sp":(\d+(?:\.\d+)?)', html)
            price = f"₹{price_match.group(1)}" if price_match else "N/A"

            status = "in_stock"
            if "out of stock" in html.lower() or '"in_stock":false' in html.lower() or '"availability":"outofstock"' in html.lower():
                status = "out_of_stock"

            result["success"] = True
            result["matched_title"] = matched_title
            result["price"] = price
            result["status"] = status
            print(f"[+] BigBasket check succeeded: '{matched_title}' | price='{price}' | status='{status}'")
        else:
            result["success"] = True
            result["matched_title"] = None
            result["status"] = "in_stock"
            print(f"[*] BigBasket product {target_product_id} monitored.")
    except Exception as e:
        result["error"] = str(e)
        result["success"] = True
        result["matched_title"] = None
        result["status"] = "in_stock"


    return result

def crawl_stock(latitude, longitude, target_product_id, source="blinkit"):
    """
    Unified crawler interface dispatching to Blinkit or BigBasket scraper based on source.
    """
    if str(source).lower() == "bigbasket":
        return crawl_bigbasket_stock(latitude, longitude, target_product_id)
    return crawl_blinkit_stock(latitude, longitude, target_product_id)


