import firebase_setup
from firebase_admin import firestore
import sys

sys.stdout.reconfigure(encoding='utf-8')

def migrate():
    db = firebase_setup.init_firebase()
    if not db:
        print("Error: Could not initialize Firebase database.")
        return

    print("--- Starting Schema Migration (Adding isActive to products and locations) ---")
    monitors_ref = db.collection("monitors")
    products_ref = db.collection("products")
    locations_ref = db.collection("locations")

    # 1. Update Products
    prods = list(products_ref.stream())
    print(f"Updating {len(prods)} products in 'products' collection...")
    for prod in prods:
        pdata = prod.to_dict()
        is_act = pdata.get("isActive")
        if is_act is None:
            is_act = pdata.get("active", True)
        products_ref.document(prod.id).update({
            "isActive": bool(is_act)
        })
        print(f"  [+] Set isActive={is_act} for Product: {prod.id}")

    # 2. Update Locations
    locs = list(locations_ref.stream())
    print(f"Updating {len(locs)} locations in 'locations' collection...")
    for loc in locs:
        ldata = loc.to_dict()
        is_act = ldata.get("isActive")
        if is_act is None:
            is_act = ldata.get("active", True)
        locations_ref.document(loc.id).update({
            "isActive": bool(is_act)
        })
        print(f"  [+] Set isActive={is_act} for Location: {loc.id}")

    # 3. Ensure Monitors
    mons = list(monitors_ref.stream())
    print(f"Updating {len(mons)} monitors in 'monitors' collection...")
    for mon in mons:
        mdata = mon.to_dict()
        is_act = mdata.get("isActive")
        if is_act is None:
            is_act = mdata.get("active", True)
        monitors_ref.document(mon.id).update({
            "isActive": bool(is_act)
        })

    print("\n--- Migration Complete ---")

if __name__ == "__main__":
    migrate()
