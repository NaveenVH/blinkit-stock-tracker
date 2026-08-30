import json

def inspect_config():
    with open("preloaded_state.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        
    mainConfig = data.get("data", {}).get("mainConfig", {})
    print("--- mainConfig Keys ---")
    print(list(mainConfig.keys()))
    
    # Let's search the entire config for urls, APIs, domains, etc.
    print("\n--- URL/API configuration entries in mainConfig ---")
    for k, v in mainConfig.items():
        v_str = str(v)
        if "http" in v_str or "api" in v_str or "grofers" in v_str or "blinkit" in v_str or "/" in v_str:
            print(f"  {k}: {repr(v)[:200]}")
            
    # Let's inspect the keys inside other data structures
    print("\n--- categories list size ---")
    categories = data.get("data", {}).get("categories", {})
    print(f"categories type: {type(categories)}, keys/size: {len(categories)}")

if __name__ == "__main__":
    inspect_config()

