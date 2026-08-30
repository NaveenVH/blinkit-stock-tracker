import json

def inspect_json():
    with open("preloaded_state.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Check location data
    print("--- Location Data ---")
    location = data.get("data", {}).get("location", {})
    print(json.dumps(location, indent=2))
    
    # Check search data
    print("\n--- Search Data Keys ---")
    search = data.get("data", {}).get("search", {})
    print(list(search.keys()))
    
    # If there are products or results
    for key in ['results', 'products', 'items', 'suggestions']:
        if key in search:
            print(f"Key '{key}' exists in search. Type: {type(search[key])}")
            if isinstance(search[key], list):
                print(f"  Length: {len(search[key])}")
                if len(search[key]) > 0:
                    print("  First item preview:", json.dumps(search[key][0], indent=2)[:300])
            elif isinstance(search[key], dict):
                print(f"  Keys: {list(search[key].keys())}")
                
    # Inspect other parts of search
    if 'pages' in search:
        print("Pages key exists in search. Keys:", list(search['pages'].keys()))
        for pk in list(search['pages'].keys())[:2]:
            print(f"  Page {pk} keys:", list(search['pages'][pk].keys()))
            if 'products' in search['pages'][pk]:
                products = search['pages'][pk]['products']
                print(f"    Products: type={type(products)}, len={len(products)}")
                if len(products) > 0:
                    print("    First product:", json.dumps(products[0], indent=2)[:500])

if __name__ == "__main__":
    inspect_json()

