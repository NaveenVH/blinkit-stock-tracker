import os
import json
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

        # Skip monitor if parent product is inactive
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

        # Skip monitor if parent location is inactive
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
