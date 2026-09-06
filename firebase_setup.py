import os
import json
import re
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
import config

db = None

def init_firebase():
    """
    Initializes the Firebase Admin SDK and returns the Firestore client.
    Supports Service Account JSON from environment variables or a local file.
    """
    global db
    if db is not None:
        return db

    if not firebase_admin._apps:
        if config.FIREBASE_SERVICE_ACCOUNT_JSON:
            try:
                cred_dict = json.loads(config.FIREBASE_SERVICE_ACCOUNT_JSON)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                print("Initialized Firebase using raw Service Account JSON from environment.")
            except Exception as e:
                print(f"Error loading FIREBASE_SERVICE_ACCOUNT_JSON: {e}")
                raise e
        elif os.path.exists(config.FIREBASE_SERVICE_ACCOUNT_FILE):
            try:
                cred = credentials.Certificate(config.FIREBASE_SERVICE_ACCOUNT_FILE)
                firebase_admin.initialize_app(cred)
                print(f"Initialized Firebase using credential file: {config.FIREBASE_SERVICE_ACCOUNT_FILE}")
            except Exception as e:
                print(f"Error loading Firebase credential file: {e}")
                raise e
        else:
            try:
                firebase_admin.initialize_app(options={
                    'projectId': config.FIREBASE_PROJECT_ID
                })
                print("Initialized Firebase using default CLI credentials / project options.")
            except Exception as e:
                print(f"Could not initialize Firebase: {e}")
                print("WARNING: Firestore operations will be disabled. Running in local-only/mock database mode.")
                return None

    try:
        db = firestore.client()
        return db
    except Exception as e:
        print(f"Failed to create Firestore client: {e}")
        return None

def get_active_monitors():
    """
    Fetches active monitors from Firestore.
    A monitor is active ONLY IF monitor.isActive == True, product.isActive == True, AND location.isActive == True.
    """
    client = init_firebase()
    if not client:
        print("Firebase offline. Returning mock monitor from environment settings.")
        return [{
            "id": "mock_env_monitor",
            "product_id": config.DEFAULT_PRODUCT_ID,
            "product_name": config.DEFAULT_PRODUCT_NAME,
            "description": "",
            "latitude": config.DEFAULT_LATITUDE,
            "longitude": config.DEFAULT_LONGITUDE,
            "pincode": "Central Bengaluru",
            "discord_webhook": config.DEFAULT_DISCORD_WEBHOOK,
            "isActive": True,
            "last_stock_status": "unknown"
        }]

    monitors_ref = client.collection("monitors")
    products_ref = client.collection("products")
    locations_ref = client.collection("locations")

    # Fetch active monitors
    docs = list(monitors_ref.where(filter=FieldFilter("isActive", "==", True)).stream())
    if not docs:
        docs = list(monitors_ref.where(filter=FieldFilter("active", "==", True)).stream())

    if not docs:
        print("Firestore monitors collection is empty. Auto-initializing normalized schema...")
        prod_id = str(config.DEFAULT_PRODUCT_ID)
        prod_data = {
            "product_id": prod_id,
            "product_name": config.DEFAULT_PRODUCT_NAME,
            "description": "",
            "isActive": True,
            "created_at": firestore.SERVER_TIMESTAMP
        }
        products_ref.document(prod_id).set(prod_data)

        loc_ref = locations_ref.add({
            "pincode": "Central Bengaluru",
            "latitude": config.DEFAULT_LATITUDE,
            "longitude": config.DEFAULT_LONGITUDE,
            "isActive": True,
            "created_at": firestore.SERVER_TIMESTAMP
        })
        loc_id = loc_ref[1].id

        monitor_data = {
            "product_id": prod_id,
            "location_id": loc_id,
            "discord_webhook": config.DEFAULT_DISCORD_WEBHOOK or "https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE",
            "isActive": True,
            "last_stock_status": "unknown",
            "last_checked_at": firestore.SERVER_TIMESTAMP
        }
        new_mon_ref = monitors_ref.add(monitor_data)[1]

        return [{
            "id": new_mon_ref.id,
            "product_id": prod_id,
            "product_name": config.DEFAULT_PRODUCT_NAME,
            "description": "",
            "location_id": loc_id,
            "pincode": "Central Bengaluru",
            "latitude": config.DEFAULT_LATITUDE,
            "longitude": config.DEFAULT_LONGITUDE,
            "discord_webhook": monitor_data["discord_webhook"],
            "isActive": True,
            "last_stock_status": "unknown"
        }]

    active_monitors = []
    for doc in docs:
        mon_data = doc.to_dict()
        doc_id = doc.id
        
        prod_id = str(mon_data.get("product_id", "")).strip()
        loc_id = mon_data.get("location_id")
        
        # 1. Product details & active check
        product_name = mon_data.get("product_name")
        description = mon_data.get("description", "")
        prod_is_active = True
        if prod_id:
            prod_snap = products_ref.document(prod_id).get()
            if prod_snap.exists:
                prod_dict = prod_snap.to_dict()
                product_name = prod_dict.get("product_name") or product_name
                description = prod_dict.get("description") or description
                prod_is_active = prod_dict.get("isActive", prod_dict.get("active", True))

        if not prod_is_active:
            print(f"[-] Skipping monitor {doc_id}: Parent product {prod_id} is inactive (isActive=False).")
            continue

        # 2. Location details & active check
        lat = mon_data.get("latitude")
        lon = mon_data.get("longitude")
        pincode = mon_data.get("pincode") or mon_data.get("location_name")
        loc_is_active = True
        if loc_id:
            loc_snap = locations_ref.document(loc_id).get()
            if loc_snap.exists:
                loc_dict = loc_snap.to_dict()
                lat = loc_dict.get("latitude", lat)
                lon = loc_dict.get("longitude", lon)
                pincode = loc_dict.get("pincode", pincode)
                loc_is_active = loc_dict.get("isActive", loc_dict.get("active", True))

        if not loc_is_active:
            print(f"[-] Skipping monitor {doc_id}: Parent location {loc_id} is inactive (isActive=False).")
            continue

        combined = {
            "id": doc_id,
            "product_id": prod_id,
            "product_name": product_name or f"Product ID {prod_id}",
            "description": description,
            "location_id": loc_id,
            "latitude": lat,
            "longitude": lon,
            "pincode": pincode or f"({lat}, {lon})",
            "discord_webhook": mon_data.get("discord_webhook"),
            "isActive": True,
            "last_stock_status": mon_data.get("last_stock_status", "unknown")
        }
        active_monitors.append(combined)

    return active_monitors

def update_product_details(product_id, description=None, product_name=None, isActive=True):
    """
    Saves or updates product description, name, and isActive in the separate 'products' collection.
    """
    client = init_firebase()
    if not client or not product_id:
        return
        
    try:
        prod_ref = client.collection("products").document(str(product_id).strip())
        prod_snap = prod_ref.get()
        
        updates = {}
        if description is not None:
            updates["description"] = description
        if product_name is not None and not product_name.startswith("Product ID"):
            updates["product_name"] = product_name
        if isActive is not None:
            updates["isActive"] = bool(isActive)
            
        if prod_snap.exists:
            if updates:
                prod_ref.update(updates)
                print(f"[*] Updated product details in 'products' table for ID {product_id}")
        else:
            doc_data = {
                "product_id": str(product_id).strip(),
                "product_name": product_name or f"Product ID {product_id}",
                "description": description or "",
                "isActive": bool(isActive),
                "created_at": firestore.SERVER_TIMESTAMP
            }
            prod_ref.set(doc_data)
            print(f"[+] Created entry in 'products' table for ID {product_id}")
    except Exception as e:
        print(f"Error updating product details in Firestore: {e}")

def update_monitor_status(doc_id, status):
    """
    Updates the stock status and timestamp of a monitor in Firestore.
    """
    client = init_firebase()
    if not client or doc_id == "mock_env_monitor":
        return
        
    try:
        doc_ref = client.collection("monitors").document(doc_id)
        doc_ref.update({
            "last_stock_status": status,
            "last_checked_at": firestore.SERVER_TIMESTAMP
        })
        print(f"Updated Firestore monitor {doc_id} stock status to: {status}")
    except Exception as e:
        print(f"Error updating Firestore document {doc_id}: {e}")

def parse_and_add_product(text_or_url):
    """
    Parses a Blinkit link or text message (e.g. "Check out this product on Blinkit - Hot Wheels Chop N Bloc Die Cast Car\nhttps://blinkit.com/prn/x/prid/787541"),
    extracts the product ID and title, saves the product in 'products' table (isActive=True),
    and creates monitor entries in 'monitors' table for ALL active locations.
    """
    client = init_firebase()
    if not client:
        print("Error: Firebase client unavailable.")
        return None

    # 1. Extract Product ID
    id_match = re.search(r'prid/(\d+)', text_or_url) or re.search(r'\b(\d{6,7})\b', text_or_url)
    if not id_match:
        print("Error: Could not extract product ID from input text.")
        return None
        
    product_id = id_match.group(1).strip()
    
    # 2. Extract Product Name if present in text
    title_match = re.search(r'Check out this product on Blinkit\s*-\s*([^\n\r]+)', text_or_url, re.IGNORECASE)
    if title_match:
        product_name = title_match.group(1).strip()
    else:
        lines = [line.strip() for line in text_or_url.splitlines() if line.strip() and not line.startswith("http")]
        product_name = lines[0] if lines else f"Product ID {product_id}"

    # Strip any trailing URL from product_name
    if "http" in product_name:
        product_name = re.sub(r'https?://\S+', '', product_name).strip()

    print(f"[+] Parsed Input -> Product ID: {product_id} | Name: '{product_name}'")

    # 3. Save/Upsert in 'products' table
    products_ref = client.collection("products")
    prod_doc_ref = products_ref.document(product_id)
    prod_snap = prod_doc_ref.get()
    
    if prod_snap.exists:
        existing_data = prod_snap.to_dict()
        updates = {"isActive": True}
        if not product_name.startswith("Product ID") and (not existing_data.get("product_name") or existing_data.get("product_name").startswith("Product ID")):
            updates["product_name"] = product_name
        prod_doc_ref.update(updates)
        print(f"[*] Updated existing product {product_id} to isActive=True in 'products' table.")
    else:
        prod_doc_ref.set({
            "product_id": product_id,
            "product_name": product_name,
            "description": "",
            "isActive": True,
            "created_at": firestore.SERVER_TIMESTAMP
        })
        print(f"[+] Created new product {product_id} in 'products' table.")

    # 4. Fetch all active locations
    locations_ref = client.collection("locations")
    active_locations = list(locations_ref.where(filter=FieldFilter("isActive", "==", True)).stream())
    
    if not active_locations:
        print("Warning: No active locations found in 'locations' table. Creating default location...")
        default_loc_ref = locations_ref.add({
            "pincode": "Central Bengaluru",
            "latitude": config.DEFAULT_LATITUDE,
            "longitude": config.DEFAULT_LONGITUDE,
            "isActive": True,
            "created_at": firestore.SERVER_TIMESTAMP
        })
        active_locations = [default_loc_ref[1].get()]

    # 5. Create monitor entries for each active location
    monitors_ref = client.collection("monitors")
    webhook = config.DEFAULT_DISCORD_WEBHOOK or "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL_HERE"
    
    monitors_created = 0
    for loc_doc in active_locations:
        loc_id = loc_doc.id
        loc_data = loc_doc.to_dict()
        pincode = loc_data.get("pincode", loc_id)
        
        mon_query = list(monitors_ref.where(filter=FieldFilter("product_id", "==", product_id)).where(filter=FieldFilter("location_id", "==", loc_id)).limit(1).stream())
        if mon_query:
            existing_id = mon_query[0].id
            monitors_ref.document(existing_id).update({"isActive": True})
            print(f"  [*] Monitor rule for Product {product_id} at location '{pincode}' already exists. Ensured isActive=True.")
        else:
            monitors_ref.add({
                "product_id": product_id,
                "location_id": loc_id,
                "discord_webhook": webhook,
                "isActive": True,
                "last_stock_status": "unknown",
                "last_checked_at": firestore.SERVER_TIMESTAMP
            })
            monitors_created += 1
            print(f"  [+] Created new monitor rule for Product {product_id} at location '{pincode}'.")

    # Send Discord Acknowledgement back to channel
    send_discord_acknowledgement(product_id, product_name, len(active_locations))

    return {
        "product_id": product_id,
        "product_name": product_name,
        "locations_count": len(active_locations),
        "monitors_created": monitors_created
    }

def send_discord_acknowledgement(product_id, product_name, locations_count):
    """
    Sends an instant confirmation embed message back to the Discord channel when a product is ingested.
    """
    webhook_url = config.DEFAULT_DISCORD_WEBHOOK
    if not webhook_url or "YOUR_WEBHOOK" in webhook_url:
        return

    embed = {
        "title": "✅ Product Ingested & Added to Tracker",
        "description": f"**{product_name}** has been registered in Firebase!",
        "color": 3066993,  # Green
        "fields": [
            {"name": "Product ID", "value": f"`{product_id}`", "inline": True},
            {"name": "Active Locations", "value": str(locations_count), "inline": True},
            {"name": "Next Crawl Status", "value": "🟢 Active (Will check on next scheduled run)", "inline": False}
        ],
        "footer": {
            "text": "Blinkit Stock Tracker Auto-Ingestion"
        }
    }

    payload = {
        "username": "Blinkit Ingestion Bot",
        "avatar_url": "https://blinkit.com/images/favicon-96x96.png",
        "embeds": [embed]
    }

    try:
        import requests
        requests.post(webhook_url, json=payload, timeout=10)
        print(f"[!] Dispatched Discord acknowledgement embed for Product {product_id}.")
    except Exception as e:
        print(f"Warning: Failed to send Discord acknowledgement: {e}")

