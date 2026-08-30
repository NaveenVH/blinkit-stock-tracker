import json

def inspect_all():
    with open("preloaded_state.json", "r", encoding="utf-8") as f:
        state = json.load(f)
        
    data = state.get("data", {})
    print("--- Non-empty fields in data ---")
    for k, v in data.items():
        if v:
            print(f"Key: {k}, type: {type(v)}")
            v_str = str(v)
            if isinstance(v, dict):
                print(f"  Keys: {list(v.keys())}")
            elif isinstance(v, list):
                print(f"  Length: {len(v)}")
            print(f"  Snippet: {v_str[:300]}")

if __name__ == "__main__":
    inspect_all()

