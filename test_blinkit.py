from curl_cffi import requests
from bs4 import BeautifulSoup
import json

def test_fetch():
    url = "https://blinkit.com/s/?q=milk"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://blinkit.com/",
    }
    
    try:
        response = requests.get(url, headers=headers, impersonate="chrome", timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        target_script = None
        for s in soup.find_all('script'):
            if s.string and "window.grofers.PRELOADED_STATE" in s.string:
                target_script = s.string
                break
                
        if target_script:
            start_marker = "window.grofers.PRELOADED_STATE ="
            start_pos = target_script.find(start_marker)
            if start_pos != -1:
                json_start = target_script.find("{", start_pos)
                # Slice from json_start to the end of the script content
                remaining_content = target_script[json_start:]
                
                try:
                    # Parse the JSON starting from the beginning of remaining_content
                    decoder = json.JSONDecoder()
                    data, end_pos = decoder.raw_decode(remaining_content)
                    print("Successfully parsed PRELOADED_STATE JSON using raw_decode!")
                    print("Parsed JSON length:", end_pos)
                    
                    with open("preloaded_state.json", "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    print("Saved preloaded_state.json")
                    
                    print("Top-level keys in state:", list(data.keys()))
                    if 'data' in data:
                        print("Keys in 'data':", list(data['data'].keys()))
                        
                except Exception as je:
                    print("raw_decode error:", je)
            else:
                print("Could not find start marker")
        else:
            print("Did not find script containing PRELOADED_STATE")
            
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_fetch()

