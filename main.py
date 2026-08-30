import firebase_setup
import crawler
import notifier
import config
import sys
import concurrent.futures

# Configure stdout to support UTF-8 characters (like the Rupee symbol ₹)
sys.stdout.reconfigure(encoding='utf-8')

def process_monitor(monitor):
    """
    Processes a single product-location monitor rule:
    Crawls stock status, checks for state changes, updates Firestore, and alerts Discord.
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
        
    last_status = monitor.get("last_stock_status", "unknown")
    
    if not product_id:
        print(f"[-] Skipping monitor doc {doc_id} because product_id is missing.")
        return

    print(f"\n[+] Starting Monitor: Product ID {product_id} at ({lat}, {lon})")
    
    # Execute PDP crawl (isolated thread-safe browser context)
    crawl_result = crawler.crawl_stock(lat, lon, product_id)
    
    if crawl_result["success"]:
        current_status = crawl_result["status"]
        matched_title = crawl_result["matched_title"] or product_name
        price = crawl_result["price"]
        link = crawl_result["link"]
        
        print(f"[Result] Product ID {product_id}: '{matched_title}' | price='{price}' | status='{current_status}'")
        
        # Auto-update product_name in Firestore if it was default/empty
        if matched_title and (not monitor.get("product_name") or monitor.get("product_name") == f"Product ID {product_id}"):
            client = firebase_setup.init_firebase()
            if client and doc_id != "mock_env_monitor":
                try:
                    client.collection("monitors").document(doc_id).update({
                        "product_name": matched_title
                    })
                    print(f"[*] Auto-updated product name in Firestore for doc {doc_id} to: {matched_title}")
                except Exception as ue:
                    print(f"Warning: Failed to auto-update name in Firestore: {ue}")
        
        # Check if stock status changed
        if current_status != last_status:
            print(f"[!] Stock transition detected for {matched_title}: {last_status} -> {current_status}")
            
            # Send Discord Notification
            discord_notifier = notifier.get_notifier(webhook_url)
            discord_notifier.send(
                product_name=matched_title,
                price=price,
                status=current_status,
                details_link=link,
                location_name=location_name
            )
            
            # Update Firestore with new status
            firebase_setup.update_monitor_status(doc_id, current_status)
        else:
            print(f"[-] No stock change for {matched_title}. Remains: {current_status}")
            # Update last checked timestamp in Firestore
            firebase_setup.update_monitor_status(doc_id, current_status)
            
    else:
        print(f"[Error] Crawl failed for Product ID {product_id}: {crawl_result['error']}")

def main():
    print("Fetching active monitors from database...")
    try:
        monitors = firebase_setup.get_active_monitors()
    except Exception as e:
        print(f"Error fetching monitors: {e}")
        sys.exit(1)
        
    print(f"Found {len(monitors)} active monitor rule(s) to process.")
    if len(monitors) == 0:
        print("No active monitors to process. Exiting.")
        return
        
    # Concurrently execute all checks in parallel
    # 3 workers is a safe balance for both local machines and limited free-tier CI CPUs
    max_workers = 3
    print(f"Executing checks in parallel using {max_workers} worker threads...\n")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all monitors to the thread pool
        executor.map(process_monitor, monitors)
        
    print("\nBatch crawl execution completed.")

if __name__ == "__main__":
    main()
