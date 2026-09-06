import os
import sys
import time
import requests
import json
import firebase_setup
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

# Discord Webhook URL for posting confirmations back to Discord
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/1507429640279425065/IRy10lKzooBzKFjr6cNIsHpkVBV29zo2TLpj2GZXMRGxHrhlOZqA_QuC7fuAyua9xOyO")
# Optional Bot Token or User Auth Token for reading messages from channel
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN") or os.getenv("DISCORD_USER_TOKEN")
# Target Channel ID (if reading via Discord API)
CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")

processed_message_ids = set()

def send_discord_confirmation(product_id, product_name, locations_count):
    """
    Sends a confirmation message back to the Discord channel via Webhook.
    """
    if not DISCORD_WEBHOOK_URL:
        return

    embed = {
        "title": "✅ Product Added to Stock Tracker",
        "description": f"**{product_name}** has been registered in Firebase!",
        "color": 3066993,  # Green
        "fields": [
            {"name": "Product ID", "value": f"`{product_id}`", "inline": True},
            {"name": "Active Locations", "value": str(locations_count), "inline": True},
            {"name": "Status", "value": "🟢 Active (Will be checked on next run)", "inline": False}
        ],
        "footer": {
            "text": "Blinkit Stock Tracker Ingestion Bot"
        }
    }

    payload = {
        "username": "Blinkit Stock Ingestor",
        "avatar_url": "https://blinkit.com/images/favicon-96x96.png",
        "embeds": [embed]
    }

    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        print(f"[+] Sent confirmation embed back to Discord for Product {product_id}.")
    except Exception as e:
        print(f"Error sending Discord confirmation: {e}")

def process_text_message(text):
    """
    Parses message text, registers product in Firebase, and posts confirmation back to Discord.
    """
    result = firebase_setup.parse_and_add_product(text)
    if result:
        send_discord_confirmation(
            product_id=result['product_id'],
            product_name=result['product_name'],
            locations_count=result['locations_count']
        )
        return result
    return None

def poll_channel_messages():
    """
    Polls the Discord Channel REST API for new Blinkit product links.
    Requires DISCORD_BOT_TOKEN or DISCORD_USER_TOKEN.
    """
    if not DISCORD_TOKEN or not CHANNEL_ID:
        print("[!] Note: To poll Discord Channel messages automatically, set DISCORD_BOT_TOKEN and DISCORD_CHANNEL_ID in your .env file.")
        return

    headers = {
        "Authorization": f"Bot {DISCORD_TOKEN}" if not DISCORD_TOKEN.startswith("Bearer") else DISCORD_TOKEN
    }

    url = f"https://discord.com/api/v9/channels/{CHANNEL_ID}/messages?limit=10"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            messages = response.json()
            for msg in messages:
                msg_id = msg.get("id")
                content = msg.get("content", "")
                
                # Ignore already processed messages or bot's own webhook messages
                if msg_id in processed_message_ids or msg.get("webhook_id"):
                    continue

                processed_message_ids.add(msg_id)
                
                if "blinkit.com/prn/x/prid/" in content or "prid/" in content:
                    print(f"\n[!] Detected new Blinkit product link in Discord Channel:")
                    print(f"    Message: {content}")
                    process_text_message(content)
        else:
            print(f"Warning: Discord API returned status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Error polling Discord messages: {e}")

if __name__ == "__main__":
    print(f"[+] Discord Channel Listener Starting...")
    print(f"    Webhook URL: {DISCORD_WEBHOOK_URL[:50]}...")
    
    if DISCORD_TOKEN and CHANNEL_ID:
        print(f"    Polling Channel ID: {CHANNEL_ID}")
        while True:
            poll_channel_messages()
            time.sleep(10)
    else:
        print("\nReady to process incoming text messages manually or via Webhook.")

