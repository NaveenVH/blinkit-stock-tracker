import sys
import re

try:
    from curl_cffi import requests
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "curl_cffi"])
    from curl_cffi import requests

sys.stdout.reconfigure(encoding='utf-8')

def test_curl_cffi():
    product_id = "804937"
    lat, lon = 13.012018, 77.705633
    url = f"https://blinkit.com/prn/x/prid/{product_id}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "lat": str(lat),
        "lon": str(lon)
    }
    
    print(f"Sending impersonated Chrome TLS GET request to: {url}...")
    try:
        # impersonate="chrome120" matches real Chrome TLS handshake
        response = requests.get(url, headers=headers, impersonate="chrome120", timeout=12)
        print(f"HTTP Status Code: {response.status_code}")
        
        if response.status_code == 200:
            html = response.text
            name_match = re.search(r'"product_name":"([^"]+)"', html) or re.search(r'"display_name":"([^"]+)"', html)
            product_name = name_match.group(1) if name_match else "Unknown Title"
            
            price_match = re.search(r'"price":(\d+)', html)
            price = f"₹{price_match.group(1)}" if price_match else "N/A"
            
            status_match = re.search(r'"product_state":"([^"]+)"', html) or re.search(r'"state":"([^"]+)"', html)
            state_val = status_match.group(1) if status_match else "unknown"
            
            status = "in_stock" if state_val in ["available", "in_stock"] else "out_of_stock"
            
            print(f"[+] TLS IMPERSONATION EXTRACTION SUCCESSFUL!")
            print(f"    Product Name: {product_name}")
            print(f"    Price:        {price}")
            print(f"    Raw State:    {state_val}")
            print(f"    Stock Status: {status}")
        else:
            print(f"Request failed with status code: {response.status_code}")
            
    except Exception as e:
        print("Error during impersonated check:", e)

if __name__ == "__main__":
    test_curl_cffi()

