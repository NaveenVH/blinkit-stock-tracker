import firebase_setup
import sys

sys.stdout.reconfigure(encoding='utf-8')

def list_records():
    db = firebase_setup.init_firebase()
    if not db:
        print("Could not initialize Firebase.")
        return
        
    print("==================================================")
    print("               FIREBASE FIRESTORE DATA            ")
    print("==================================================")

    # 1. Products Table
    print("\n--- PRODUCTS TABLE ('products') ---")
    products = list(db.collection("products").stream())
    print(f"Total Products: {len(products)}")
    for prod in products:
        p = prod.to_dict()
        is_act = p.get('isActive', p.get('active', True))
        print(f"  [{p.get('product_id')}] {p.get('product_name')} (isActive={is_act})")
        desc = p.get('description', '')
        if desc:
            print(f"      Desc: {desc[:80]}...")
        else:
            print(f"      Desc: (Not fetched yet)")

    # 2. Locations Table
    print("\n--- LOCATIONS TABLE ('locations') ---")
    locations = list(db.collection("locations").stream())
    print(f"Total Locations: {len(locations)}")
    for loc in locations:
        l = loc.to_dict()
        is_act = l.get('isActive', l.get('active', True))
        print(f"  [{loc.id}] {l.get('pincode')} ({l.get('latitude')}, {l.get('longitude')}) (isActive={is_act})")

    # 3. Monitors Table
    print("\n--- MONITORS TABLE ('monitors') ---")
    monitors = list(db.collection("monitors").stream())
    print(f"Total Monitors: {len(monitors)}")
    for mon in monitors:
        m = mon.to_dict()
        is_act = m.get('isActive', m.get('active', True))
        print(f"  Doc ID: {mon.id}")
        print(f"    Product ID:  {m.get('product_id')}")
        print(f"    Location ID: {m.get('location_id')}")
        print(f"    isActive:    {is_act}")
        print(f"    Status:      {m.get('last_stock_status')}")
        print("  " + "-" * 40)

if __name__ == "__main__":
    list_records()
