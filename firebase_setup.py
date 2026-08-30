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
        # 1. Check if raw JSON string is provided in env (for GitHub Actions)
        if config.FIREBASE_SERVICE_ACCOUNT_JSON:
            try:
                cred_dict = json.loads(config.FIREBASE_SERVICE_ACCOUNT_JSON)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                print("Initialized Firebase using raw Service Account JSON from environment.")
            except Exception as e:
                print(f"Error loading FIREBASE_SERVICE_ACCOUNT_JSON: {e}")
                raise e
        # 2. Check if local credential file exists (for local development)
        elif os.path.exists(config.FIREBASE_SERVICE_ACCOUNT_FILE):
            try:
                cred = credentials.Certificate(config.FIREBASE_SERVICE_ACCOUNT_FILE)
                firebase_admin.initialize_app(cred)
                print(f"Initialized Firebase using credential file: {config.FIREBASE_SERVICE_ACCOUNT_FILE}")
            except Exception as e:
                print(f"Error loading Firebase credential file: {e}")
                raise e
        # 3. Fallback to default options (local runner might have active login)
        else:
            try:
                # If no service account is provided, initialize using active CLI credentials if possible
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
    Fetches all active monitors from Firestore.
    If the database is empty, creates a default monitor using environment values.
    """
    client = init_firebase()
    if not client:
        # Return a mock monitor using env variables if Firebase is unavailable
        print("Firebase offline. Returning mock monitor from environment settings.")
        return [{
            "id": "mock_env_monitor",
            "product_name": config.DEFAULT_PRODUCT_NAME,
            "product_id": config.DEFAULT_PRODUCT_ID,
            "latitude": config.DEFAULT_LATITUDE,
            "longitude": config.DEFAULT_LONGITUDE,
            "discord_webhook": config.DEFAULT_DISCORD_WEBHOOK,
            "active": True,
            "last_stock_status": "unknown"
        }]

    monitors_ref = client.collection("monitors")
    # Fetch active monitors
    docs = list(monitors_ref.where(filter=FieldFilter("active", "==", True)).stream())
    
    if not docs:
        # Auto-initialize the database with a default monitor if completely empty
        print("Firestore 'monitors' collection is empty. Creating a default entry for Bangalore...")
        default_data = {
            "product_name": config.DEFAULT_PRODUCT_NAME,
            "product_id": config.DEFAULT_PRODUCT_ID,
            "latitude": config.DEFAULT_LATITUDE,
            "longitude": config.DEFAULT_LONGITUDE,
            "pincode": "560001",
            "discord_webhook": config.DEFAULT_DISCORD_WEBHOOK or "https://discord.com/api/webhooks/YOUR_WEBHOOK_HERE",
            "active": True,
            "last_stock_status": "unknown",
            "last_checked_at": firestore.SERVER_TIMESTAMP
        }
        # Add to Firestore
        new_doc_ref = monitors_ref.add(default_data)[1]
        default_data["id"] = new_doc_ref.id
        print(f"Created default monitor in Firestore with ID: {new_doc_ref.id}")
        return [default_data]

    active_monitors = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        active_monitors.append(data)
        
    return active_monitors

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

