import requests
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def test_direct_http(product_id):
    lat, lon = 13.012018, 77.705633
    url = f"https://blinkit.com/prn/x/prid/{product_id}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "lat": str(lat),
        "lon": str(lon)
    }
    
    print(f"\nChecking Product ID {product_id} via direct HTTP...")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            html = response.text
            
            # Find product name
            name_match = re.search(r'"product_name":"([^"]+)"', html) or re.search(r'"display_name":"([^"]+)"', html)
            product_name = name_match.group(1) if name_match else "Unknown Title"
            
            # Find price
            price_match = re.search(r'"price":(\d+)', html)
            price = f"₹{price_match.group(1)}" if price_match else "N/A"
            
            # Find status
            status_match = re.search(r'"product_state":"([^"]+)"', html) or re.search(r'"state":"([^"]+)"', html)
            state_val = status_match.group(1) if status_match else "unknown"
            
            status = "in_stock" if state_val in ["available", "in_stock"] else "out_of_stock"
            
            print(f"[+] Product Name: {product_name}")
            print(f"    Price:        {price}")
            print(f"    Raw State:    {state_val}")
            print(f"    Stock Status: {status}")
            
    except Exception as e:
        print("Error during direct HTTP check:", e)

if __name__ == "__main__":
    test_direct_http("804937")
    test_direct_http("787571")
    test_direct_http("1383384")

