import requests
import json

class BaseNotifier:
    def send(self, product_name, price, status, details_link=None):
        raise NotImplementedError("Subclasses must implement the send method.")

class DiscordNotifier(BaseNotifier):
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send(self, product_name, price, status, details_link=None):
        if not self.webhook_url or "YOUR_WEBHOOK_HERE" in self.webhook_url:
            print("WARNING: Discord Webhook URL is not configured. Notification skipped.")
            return False

        # Status styling
        if status.lower() == "in_stock":
            color = 3066993  # Green
            status_text = "🟢 IN STOCK"
            title = "🚨 Product Back In Stock!"
            description = f"**{product_name}** is now available on Blinkit!"
        else:
            color = 15158332  # Red
            status_text = "🔴 OUT OF STOCK"
            title = "📉 Product Out of Stock"
            description = f"**{product_name}** is no longer available on Blinkit."

        # Payload construction
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "fields": [
                {"name": "Product Name", "value": product_name, "inline": False},
                {"name": "Current Price", "value": price if price else "N/A", "inline": True},
                {"name": "Status", "value": status_text, "inline": True}
            ],
            "footer": {
                "text": "Blinkit Hyperlocal Stock Tracker"
            }
        }

        if details_link:
            embed["url"] = details_link
            embed["fields"].append({"name": "Link", "value": f"[View on Blinkit]({details_link})", "inline": False})

        payload = {
            "username": "Blinkit Stock Monitor",
            "avatar_url": "https://blinkit.com/images/favicon-96x96.png",  # Blinkit icon
            "embeds": [embed]
        }

        headers = {"Content-Type": "application/json"}
        
        try:
            response = requests.post(self.webhook_url, headers=headers, data=json.dumps(payload), timeout=10)
            if response.status_code in [200, 204]:
                print(f"Notification sent to Discord for '{product_name}' ({status}).")
                return True
            else:
                print(f"Failed to send Discord notification: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"Error sending Discord notification: {e}")
            return False

def get_notifier(webhook_url):
    """
    Factory function to return the correct notifier.
    Currently only supports Discord, but can be extended here.
    """
    return DiscordNotifier(webhook_url)

