import firebase_setup
from firebase_admin import firestore
import config

def seed():
    # Initialize Firebase
    db = firebase_setup.init_firebase()
    if not db:
        print("Firebase database could not be initialized. Please configure credentials first.")
        return
        
    monitors_ref = db.collection("monitors")
    
    # Configure your locations
    locations = [
        {"name": "KR Puram, Bengaluru", "lat": 13.012018, "lon": 77.705633},
        {"name": "Central Bengaluru", "lat": 12.9716, "lon": 77.5946}
    ]
    
    # Configure your product IDs
    products = [
        {"id": "787571", "name": "Hot Wheels Batmobile Die Cast Car"},
        {"id": "804937", "name": "Hot Wheels 1970 Pontiac Firebird"},
        {"id": "1383384", "name": "Matchbox 1973 Volkswagen T2B Bus"}
    ]
    
    # Webhook URL (reads from config/env or falls back)
    webhook = config.DEFAULT_DISCORD_WEBHOOK or "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL_HERE"
    
    print(f"Seeding monitors into Firestore project '{config.FIREBASE_PROJECT_ID}'...")
    
    count = 0
    for loc in locations:
        for prod in products:
            # Check if this exact product-location combination already exists
            query = (monitors_ref
                     .where("product_id", "==", prod["id"])
                     .where("latitude", "==", loc["lat"])
                     .where("longitude", "==", loc["lon"])
                     .limit(1)
                     .stream())
            
            if len(list(query)) > 0:
                print(f"[-] Already exists: {prod['name']} at {loc['name']}. Skipping.")
                continue
                
            doc_data = {
                "product_id": prod["id"],
                "product_name": prod["name"],
                "latitude": loc["lat"],
                "longitude": loc["lon"],
                "pincode": loc["name"],
                "discord_webhook": webhook,
                "active": True,
                "last_stock_status": "unknown",
                "last_checked_at": firestore.SERVER_TIMESTAMP
            }
            
            monitors_ref.add(doc_data)
            print(f"[+] Seeded: {prod['name']} at {loc['name']}")
            count += 1
            
    print(f"\nSeeding complete! Added {count} new monitor rule(s) to Firestore.")

if __name__ == "__main__":
    seed()

