import firebase_setup
import crawler
import notifier
import config
import sys

# Configure stdout to support UTF-8 characters (like the Rupee symbol ₹)
sys.stdout.reconfigure(encoding='utf-8')

def process_monitor(monitor):
    """
    Processes a single product-location monitor rule:
    Crawls stock status, updates product details (name & description) in Firestore 'products' table,
    updates monitor stock status, and dispatches Discord notifications.
    """
    doc_id = monitor.get("id")
    product_id = monitor.get("product_id")
    product_name = monitor.get("product_name", f"Product ID {product_id}")
    lat = monitor.get("latitude")
    lon = monitor.get("longitude")
    location_name = monitor.get("pincode") or monitor.get("location_name") or f"Coordinates ({lat}, {lon})"
    webhook_url = monitor.get("discord_webhook")
    
    # Fall back to environment variable (GitHub secret) if document has placeholder or is empty
    if not webhook_url or "YOUR_WEBHOOK" in webhook_url:
        webhook_url = config.DEFAULT_DISCORD_WEBHOOK
    
    if not product_id:
        print(f"[-] Skipping monitor doc {doc_id} because product_id is missing.")
        return

    print(f"\n[+] Starting Monitor: Product ID {product_id} at ({lat}, {lon})")
    
    # Execute PDP crawl
    crawl_result = crawler.crawl_stock(lat, lon, product_id)
    
    if crawl_result["success"]:
        current_status = crawl_result["status"]
        matched_title = crawl_result["matched_title"] or product_name
        description = crawl_result["description"]
        price = crawl_result["price"]
        link = crawl_result["link"]
        
        print(f"[Result] Product ID {product_id}: '{matched_title}' | price='{price}' | status='{current_status}'")
        
        # Save / Auto-update product details (including description) in separate 'products' table in Firestore
        firebase_setup.update_product_details(
            product_id=product_id,
            description=description,
            product_name=matched_title
        )
        
        # Send Discord notification
        print(f"[!] Sending notification for {matched_title} ({current_status}) at {location_name}")
        discord_notifier = notifier.get_notifier(webhook_url)
        discord_notifier.send(
            product_name=matched_title,
            price=price,
            status=current_status,
            details_link=link,
            location_name=location_name
        )
        
        # Update last checked status/timestamp in Firestore
        firebase_setup.update_monitor_status(doc_id, current_status)
            
    else:
        print(f"[Error] Crawl failed for Product ID {product_id}: {crawl_result['error']}")

def main():
    print("Fetching active monitors (isActive == True) from database...")
    try:
        monitors = firebase_setup.get_active_monitors()
    except Exception as e:
        print(f"Error fetching monitors: {e}")
        sys.exit(1)
        
    print(f"Found {len(monitors)} active monitor rule(s) to process.")
    if len(monitors) == 0:
        print("No active monitors to process. Exiting.")
        return
        
    # Process sequentially on main thread
    for monitor in monitors:
        process_monitor(monitor)
        
    print("\nBatch crawl execution completed.")

if __name__ == "__main__":
    main()
