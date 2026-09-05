import firebase_setup
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
import config
import sys

sys.stdout.reconfigure(encoding='utf-8')

def seed():
    db = firebase_setup.init_firebase()
    if not db:
        print("Firebase database could not be initialized. Please configure credentials first.")
        return
        
    products_ref = db.collection("products")
    locations_ref = db.collection("locations")
    monitors_ref = db.collection("monitors")
    
    locations = [
        {"name": "KR Puram, Bengaluru", "lat": 13.012018, "lon": 77.705633},
        {"name": "Central Bengaluru", "lat": 12.9716, "lon": 77.5946}
    ]
    
    products = [
        {"id": "787571", "name": "Hot Wheels Batmobile Die Cast Car", "desc": "Authentic 1:64 scale Batmobile die-cast vehicle."},
        {"id": "804937", "name": "Hot Wheels 1970 Pontiac Firebird", "desc": "Classic muscle car 1:64 scale replica."},
        {"id": "1383384", "name": "Matchbox 1973 Volkswagen T2B Bus", "desc": "Detailed vintage Volkswagen T2B Bus model."},
        {"id": "787961", "name": "Hot Wheels '70 Dodge Charger Die Cast Car", "desc": "High-speed Dodge Charger 1:64 die-cast car."}
    ]
    
    webhook = config.DEFAULT_DISCORD_WEBHOOK or "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL_HERE"
    
    print(f"Seeding normalized tables with isActive in Firestore project '{config.FIREBASE_PROJECT_ID}'...")

    # 1. Seed Products (with isActive: True)
    for prod in products:
        prod_ref = products_ref.document(prod["id"])
        prod_snap = prod_ref.get()
        if not prod_snap.exists:
            prod_ref.set({
                "product_id": prod["id"],
                "product_name": prod["name"],
                "description": prod["desc"],
                "isActive": True,
                "created_at": firestore.SERVER_TIMESTAMP
            })
            print(f"[+] Seeded Product (isActive=True): {prod['id']} - {prod['name']}")
        else:
            prod_ref.update({"isActive": True})

    # 2. Seed Locations (with isActive: True)
    loc_id_map = {}
    for loc in locations:
        query = list(locations_ref.where(filter=FieldFilter("latitude", "==", loc["lat"])).where(filter=FieldFilter("longitude", "==", loc["lon"])).limit(1).stream())
        if query:
            loc_doc = query[0]
            loc_id_map[loc["name"]] = loc_doc.id
            locations_ref.document(loc_doc.id).update({"isActive": True})
        else:
            new_loc_ref = locations_ref.add({
                "pincode": loc["name"],
                "latitude": loc["lat"],
                "longitude": loc["lon"],
                "isActive": True,
                "created_at": firestore.SERVER_TIMESTAMP
            })
            loc_id_map[loc["name"]] = new_loc_ref[1].id
            print(f"[+] Seeded Location (isActive=True): {loc['name']}")

    # 3. Seed Monitors (with isActive: True)
    monitors_added = 0
    for loc in locations:
        loc_id = loc_id_map[loc["name"]]
        for prod in products:
            prod_id = prod["id"]
            
            query = list(monitors_ref.where(filter=FieldFilter("product_id", "==", prod_id)).where(filter=FieldFilter("location_id", "==", loc_id)).limit(1).stream())
            if query:
                existing_doc = query[0]
                monitors_ref.document(existing_doc.id).update({"isActive": True})
                print(f"[-] Already exists: Product {prod_id} at {loc['name']}. Ensured isActive=True.")
                continue

            monitor_doc = {
                "product_id": prod_id,
                "location_id": loc_id,
                "discord_webhook": webhook,
                "isActive": True,
                "last_stock_status": "unknown",
                "last_checked_at": firestore.SERVER_TIMESTAMP
            }
            monitors_ref.add(monitor_doc)
            print(f"[+] Seeded Monitor: Product {prod_id} at {loc['name']} (isActive=True)")
            monitors_added += 1

    print(f"\nSeeding complete! Added {monitors_added} new monitor rule(s).")

if __name__ == "__main__":
    seed()
