import argparse
import firebase_setup
from firebase_admin import firestore
import config
import sys

sys.stdout.reconfigure(encoding='utf-8')

def add_monitor_entry(product_id, latitude, longitude, pincode=None):
    db = firebase_setup.init_firebase()
    if not db:
        print("Error: Could not initialize Firebase.")
        return
        
    products_ref = db.collection("products")
    locations_ref = db.collection("locations")
    monitors_ref = db.collection("monitors")
    
    prod_id = str(product_id).strip()
    lat = float(latitude)
    lon = float(longitude)
    pincode_label = pincode if pincode else f"({lat}, {lon})"
    webhook = config.DEFAULT_DISCORD_WEBHOOK or "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL_HERE"
    
    # 1. Ensure Product exists in 'products' table with isActive=True
    prod_doc_ref = products_ref.document(prod_id)
    prod_snap = prod_doc_ref.get()
    if not prod_snap.exists:
        prod_doc_ref.set({
            "product_id": prod_id,
            "product_name": f"Product ID {prod_id}",
            "description": "",
            "isActive": True,
            "created_at": firestore.SERVER_TIMESTAMP
        })
        print(f"[+] Created Product in 'products' table (isActive=True): {prod_id}")
    else:
        prod_doc_ref.update({"isActive": True})

    # 2. Ensure Location exists in 'locations' table with isActive=True
    loc_query = list(locations_ref.where("latitude", "==", lat).where("longitude", "==", lon).limit(1).stream())
    if loc_query:
        loc_id = loc_query[0].id
        locations_ref.document(loc_id).update({"isActive": True})
    else:
        new_loc_ref = locations_ref.add({
            "pincode": pincode_label,
            "latitude": lat,
            "longitude": lon,
            "isActive": True,
            "created_at": firestore.SERVER_TIMESTAMP
        })
        loc_id = new_loc_ref[1].id
        print(f"[+] Created Location in 'locations' table (isActive=True): {loc_id} ({pincode_label})")

    # 3. Add or update Monitor with isActive=True
    mon_query = list(monitors_ref.where("product_id", "==", prod_id).where("location_id", "==", loc_id).limit(1).stream())
    if mon_query:
        existing_id = mon_query[0].id
        monitors_ref.document(existing_id).update({"isActive": True})
        print(f"[-] Monitor rule already exists for Product ID {prod_id} at {pincode_label}. Ensured isActive=True.")
        return
        
    doc_data = {
        "product_id": prod_id,
        "location_id": loc_id,
        "discord_webhook": webhook,
        "isActive": True,
        "last_stock_status": "unknown",
        "last_checked_at": firestore.SERVER_TIMESTAMP
    }
    
    new_doc_ref = monitors_ref.add(doc_data)
    print(f"[+] Successfully added new monitor rule to Firebase!")
    print(f"    Document ID: {new_doc_ref[1].id}")
    print(f"    Product ID:  {prod_id} (isActive=True)")
    print(f"    Location ID: {loc_id} ({pincode_label}, isActive=True)")
    print(f"    isActive:    True")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add a new product/location monitor rule to Firebase.")
    parser.add_argument("--id", required=True, help="Blinkit Product ID (e.g. 787961)")
    parser.add_argument("--lat", required=True, type=float, help="Latitude (e.g. 13.012018)")
    parser.add_argument("--lon", required=True, type=float, help="Longitude (e.g. 77.705633)")
    parser.add_argument("--pincode", required=False, help="Location name label (e.g. 'KR Puram, Bengaluru')")
    
    args = parser.parse_args()
    add_monitor_entry(args.id, args.lat, args.lon, args.pincode)
