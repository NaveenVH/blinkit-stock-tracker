import os
from dotenv import load_dotenv
import requests
import firebase_setup

load_dotenv()

token = os.getenv("DISCORD_BOT_TOKEN")
channel_id = os.getenv("DISCORD_CHANNEL_ID")


print("Fetching recent channel messages from #stockalertsnvh...")
url = f"https://discord.com/api/v9/channels/{channel_id}/messages?limit=10"
headers = {"Authorization": f"Bot {token}"}

response = requests.get(url, headers=headers)
if response.status_code == 200:
    messages = response.json()
    print(f"Found {len(messages)} recent messages.")
    
    # Process in chronological order (oldest to newest)
    for msg in reversed(messages):
        content = msg.get("content", "")
        author = msg.get("author", {}).get("username", "")
        msg_id = msg.get("id")
        
        if "blinkit.com/prn/x/prid/" in content or "prid/" in content:
            print(f"\n[+] Ingesting message from {author} (ID {msg_id}):")
            print(f"    Content: {content[:80]}...")
            res = firebase_setup.parse_and_add_product(content)
            print(f"    Result: {res}")
else:
    print(f"Error fetching channel messages: {response.status_code} - {response.text}")

