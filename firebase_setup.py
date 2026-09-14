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
            "source": "blinkit",
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
            "source": "blinkit",
            "last_stock_status": "unknown"
        }]

    active_monitors = []
    bigbasket_products_ref = client.collection("bigbasket_products")

    for doc in docs:
        mon_data = doc.to_dict()
        doc_id = doc.id
        
        prod_id = str(mon_data.get("product_id", "")).strip()
        loc_id = mon_data.get("location_id")
        mon_source = mon_data.get("source", "blinkit").lower()
        
        # 1. Product details & active check (from bigbasket_products or products)
        product_name = mon_data.get("product_name")
        description = mon_data.get("description", "")
        prod_is_active = True
        
        target_prod_ref = bigbasket_products_ref if mon_source == "bigbasket" else products_ref
        
        if prod_id:
            prod_snap = target_prod_ref.document(prod_id).get()
            if prod_snap.exists:
                prod_dict = prod_snap.to_dict()
                product_name = prod_dict.get("product_name") or product_name
                description = prod_dict.get("description") or description
                prod_is_active = prod_dict.get("isActive", prod_dict.get("active", True))

        if not prod_is_active:
            print(f"[-] Skipping monitor {doc_id}: Parent product {prod_id} ({mon_source}) is inactive (isActive=False).")
            continue

        # 2. Location details & active check (shared locations table)
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
            "source": mon_source,
            "last_stock_status": mon_data.get("last_stock_status", "unknown")
        }
        active_monitors.append(combined)

    return active_monitors

def is_generic_title(title):
    if not title:
        return True
    t = str(title).strip().lower()
    return t.startswith("product id") or t.startswith("bigbasket product") or t.startswith("blinkit product") or t == "none"

def update_product_details(product_id, description=None, product_name=None, isActive=True, source="blinkit"):
    """
    Saves or updates product description, name, and isActive in the platform-specific collection
    ('bigbasket_products' for BigBasket or 'products' for Blinkit).
    """
    client = init_firebase()
    if not client or not product_id:
        return
        
    collection_name = "bigbasket_products" if str(source).lower() == "bigbasket" else "products"
    
    try:
        prod_ref = client.collection(collection_name).document(str(product_id).strip())
        prod_snap = prod_ref.get()
        
        updates = {}
        if description is not None:
            updates["description"] = description
        if product_name is not None and not is_generic_title(product_name):
            updates["product_name"] = product_name
        if isActive is not None:
            updates["isActive"] = bool(isActive)
            
        if prod_snap.exists:
            existing = prod_snap.to_dict()
            if is_generic_title(existing.get("product_name")) and not is_generic_title(product_name):
                updates["product_name"] = product_name
            if updates:
                prod_ref.update(updates)
                print(f"[*] Updated product details in '{collection_name}' table for ID {product_id}")
        else:
            doc_data = {
                "product_id": str(product_id).strip(),
                "product_name": product_name or f"Product ID {product_id}",
                "description": description or "",
                "isActive": bool(isActive),
                "source": source.lower(),
                "created_at": firestore.SERVER_TIMESTAMP
            }
            prod_ref.set(doc_data)
            print(f"[+] Created entry in '{collection_name}' table for ID {product_id}")
    except Exception as e:
        print(f"Error updating product details in Firestore ({collection_name}): {e}")

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
    Parses a Blinkit or BigBasket product link/text message.
    Extracts the product ID, platform source ('blinkit' vs 'bigbasket'), and product title.
    Saves BigBasket products to 'bigbasket_products' table and Blinkit products to 'products' table.
    Creates monitor entries in the shared 'monitors' table (with shared locations).
    """
    client = init_firebase()
    if not client:
        print("Error: Firebase client unavailable.")
        return None

    # 1. Detect Source Platform and Extract Product ID & Title
    source = "blinkit"
    product_id = None
    product_name = None

    bb_match = re.search(r'bigbasket\.com/pd/(\d+)', text_or_url, re.IGNORECASE) or re.search(r'/pd/(\d+)', text_or_url, re.IGNORECASE)
    bk_match = re.search(r'blinkit\.com/prn/x/prid/(\d+)', text_or_url, re.IGNORECASE) or re.search(r'prid/(\d+)', text_or_url, re.IGNORECASE)

    if bb_match:
        source = "bigbasket"
        product_id = bb_match.group(1).strip()
        # Extract title slug from URL if available
        slug_match = re.search(r'/pd/\d+/([a-zA-Z0-9\-]+)', text_or_url)
        if slug_match and slug_match.group(1):
            raw_slug = slug_match.group(1).replace('-', ' ').strip()
            product_name = ' '.join(word.capitalize() for word in raw_slug.split())
    elif bk_match:
        source = "blinkit"
        product_id = bk_match.group(1).strip()
    else:
        # Fallback numeric ID
        gen_match = re.search(r'\b(\d{6,8})\b', text_or_url)
        if gen_match:
            product_id = gen_match.group(1).strip()
            source = "bigbasket" if "bigbasket" in text_or_url.lower() else "blinkit"

    if not product_id:
        print("Error: Could not extract product ID from input text.")
        return None

    # 2. Extract Product Name from preceding message text if available
    title_match = re.search(r'Check out this product on (?:Blinkit|BigBasket)\s*-\s*([^\n\r]+)', text_or_url, re.IGNORECASE)
    if title_match:
        product_name = title_match.group(1).strip()
    elif not product_name:
        lines = [line.strip() for line in text_or_url.splitlines() if line.strip() and not line.startswith("http")]
        product_name = lines[0] if lines else f"Product ID {product_id}"

    if "http" in product_name:
        product_name = re.sub(r'https?://\S+', '', product_name).strip()
    if not product_name:
        product_name = f"Product ID {product_id}"

    target_table = "bigbasket_products" if source == "bigbasket" else "products"
    print(f"[+] Parsed Input -> Source: {source.upper()} | Product ID: {product_id} | Name: '{product_name}' | Table: '{target_table}'")

    # 3. Check if Product exists in target table for Toggle logic
    products_ref = client.collection(target_table)
    monitors_ref = client.collection("monitors")
    prod_doc_ref = products_ref.document(product_id)
    prod_snap = prod_doc_ref.get()
    
    is_new_product = not prod_snap.exists

    if prod_snap.exists:
        existing_data = prod_snap.to_dict()
        current_active = existing_data.get("isActive", existing_data.get("active", True))
        new_active = not current_active
        
        updates = {"isActive": new_active}
        if not is_generic_title(product_name):
            updates["product_name"] = product_name
        prod_doc_ref.update(updates)
        
        # Toggle corresponding monitors
        mon_docs = list(monitors_ref.where(filter=FieldFilter("product_id", "==", product_id)).stream())
        for mdoc in mon_docs:
            monitors_ref.document(mdoc.id).update({"isActive": new_active})

        resolved_name = product_name if not is_generic_title(product_name) else (existing_data.get("product_name") or product_name)
        status_label = "PAUSED / INACTIVE 🔴" if not new_active else "ACTIVATED 🟢"
        print(f"[*] TOGGLED {source.upper()} product {product_id} ('{resolved_name}') to isActive={new_active} ({status_label}).")

        send_discord_acknowledgement(product_id, resolved_name, len(mon_docs) or 1, is_toggle=True, isActive=new_active, source=source)

        return {
            "product_id": product_id,
            "product_name": resolved_name,
            "source": source,
            "isActive": new_active,
            "toggled": True,
            "status_label": status_label
        }

    else:
        # NEW PRODUCT: Create entry in target table
        prod_doc_ref.set({
            "product_id": product_id,
            "product_name": product_name,
            "description": "",
            "source": source,
            "isActive": True,
            "created_at": firestore.SERVER_TIMESTAMP
        })
        print(f"[+] Created new product {product_id} in '{target_table}' table.")

    # 4. Fetch all active locations (shared locations table)
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

    # 5. Create monitor entries in shared 'monitors' table
    webhook = config.DEFAULT_DISCORD_WEBHOOK or "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL_HERE"
    monitors_created = 0

    for loc_doc in active_locations:
        loc_id = loc_doc.id
        loc_data = loc_doc.to_dict()
        pincode = loc_data.get("pincode", loc_id)
        
        mon_query = list(monitors_ref.where(filter=FieldFilter("product_id", "==", product_id)).where(filter=FieldFilter("location_id", "==", loc_id)).limit(1).stream())
        if mon_query:
            existing_id = mon_query[0].id
            monitors_ref.document(existing_id).update({"isActive": True, "source": source})
            print(f"  [*] Monitor rule for {source.upper()} Product {product_id} at location '{pincode}' already exists. Ensured isActive=True.")
        else:
            monitors_ref.add({
                "product_id": product_id,
                "location_id": loc_id,
                "discord_webhook": webhook,
                "source": source,
                "isActive": True,
                "last_stock_status": "unknown",
                "last_checked_at": firestore.SERVER_TIMESTAMP
            })
            monitors_created += 1
            print(f"  [+] Created new monitor rule for {source.upper()} Product {product_id} at location '{pincode}'.")

    send_discord_acknowledgement(product_id, product_name, len(active_locations), is_toggle=False, isActive=True, source=source)

    return {
        "product_id": product_id,
        "product_name": product_name,
        "source": source,
        "isActive": True,
        "locations_count": len(active_locations),
        "monitors_created": monitors_created
    }

def send_discord_acknowledgement(product_id, product_name, locations_count, is_toggle=False, isActive=True, source="blinkit"):
    """
    Sends an instant confirmation embed message back to Discord when a product is added or toggled,
    with explicit platform source badges ([🟡 Blinkit] / [🔴 BigBasket]).
    """
    webhook_url = config.DEFAULT_DISCORD_WEBHOOK
    if not webhook_url or "YOUR_WEBHOOK" in webhook_url:
        return

    is_bb = (str(source).lower() == "bigbasket")
    badge = "[🔴 BigBasket]" if is_bb else "[🟡 Blinkit]"
    platform_name = "BigBasket" if is_bb else "Blinkit"
    bot_username = "BigBasket Ingestion Bot" if is_bb else "Blinkit Ingestion Bot"
    bot_avatar = "https://www.bigbasket.com/favicon.ico" if is_bb else "https://blinkit.com/images/favicon-96x96.png"

    if is_toggle:
        if isActive:
            title = f"{badge} 🟢 Product Re-Activated"
            description = f"**{product_name}** ({platform_name}) has been set to **ACTIVE** and will be monitored!"
            color = 3066993  # Green
            status_val = "🟢 Active"
        else:
            title = f"{badge} 🔴 Product Paused / Deactivated"
            description = f"**{product_name}** ({platform_name}) has been set to **INACTIVE**."
            color = 15158332  # Red
            status_val = "🔴 Paused / Inactive"
    else:
        title = f"{badge} ✅ Product Ingested & Added to Tracker"
        description = f"**{product_name}** has been registered in Firebase `{platform_name.lower()}_products` table!"
        color = 15158332 if is_bb else 16766464
        status_val = "🟢 Active (Will check on next scheduled run)"

    embed = {
        "title": title,
        "description": description,
        "color": color,
        "fields": [
            {"name": "Source Platform", "value": badge, "inline": True},
            {"name": "Product ID", "value": f"`{product_id}`", "inline": True},
            {"name": "Locations Monitored", "value": str(locations_count), "inline": True},
            {"name": "Current Status", "value": status_val, "inline": False}
        ],
        "footer": {
            "text": f"{platform_name} Stock Tracker Auto-Ingestion"
        }
    }

    payload = {
        "username": bot_username,
        "avatar_url": bot_avatar,
        "embeds": [embed]
    }

    sent_success = False
    import requests

    if webhook_url and "YOUR_WEBHOOK" not in webhook_url:
        try:
            resp = requests.post(webhook_url, json=payload, timeout=10)
            if resp.status_code in [200, 204]:
                print(f"[!] Dispatched Webhook acknowledgement embed for {platform_name} Product {product_id}.")
                sent_success = True
            else:
                print(f"[-] Webhook failed ({resp.status_code}). Attempting Bot API fallback...")
        except Exception as e:
            print(f"[-] Webhook exception ({e}). Attempting Bot API fallback...")

    # Fallback to Discord Bot REST API if Webhook failed or was missing
    if not sent_success:
        bot_token = config.DISCORD_BOT_TOKEN
        channel_id = config.DISCORD_CHANNEL_ID
        if bot_token and channel_id:
            bot_url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
            bot_headers = {
                "Authorization": f"Bot {bot_token}",
                "Content-Type": "application/json"
            }
            bot_payload = {"embeds": [embed]}
            try:
                bot_resp = requests.post(bot_url, headers=bot_headers, json=bot_payload, timeout=10)
                if bot_resp.status_code in [200, 201]:
                    print(f"[!] Dispatched Bot API acknowledgement embed for {platform_name} Product {product_id}.")
                else:
                    print(f"[-] Bot API returned status {bot_resp.status_code}: {bot_resp.text}")
            except Exception as e:
                print(f"[-] Bot API exception: {e}")




