import requests
import json

class BaseNotifier:
    def send(self, product_name, price, status, details_link=None):
        raise NotImplementedError("Subclasses must implement the send method.")

class DiscordNotifier(BaseNotifier):
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send(self, product_name, price, status, details_link=None, location_name=None, source="blinkit"):
        if not self.webhook_url or "YOUR_WEBHOOK_HERE" in self.webhook_url:
            print("WARNING: Discord Webhook URL is not configured. Notification skipped.")
            return False

        is_bb = (str(source).lower() == "bigbasket")
        badge = "[🔴 BigBasket]" if is_bb else "[🟡 Blinkit]"
        platform_name = "BigBasket" if is_bb else "Blinkit"
        bot_username = "BigBasket Stock Monitor" if is_bb else "Blinkit Stock Monitor"
        bot_avatar = "https://www.bigbasket.com/favicon.ico" if is_bb else "https://blinkit.com/images/favicon-96x96.png"

        # Status styling
        if status.lower() == "in_stock":
            color = 3066993  # Green
            status_text = "🟢 IN STOCK"
            title = f"{badge} 🚨 Product Back In Stock!"
            description = f"**{product_name}** is now available on **{platform_name}**!"
        else:
            color = 15158332  # Red
            status_text = "🔴 OUT OF STOCK"
            title = f"{badge} 📉 Product Out of Stock"
            description = f"**{product_name}** is no longer available on **{platform_name}**."

        # Payload construction
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "fields": [
                {"name": "Platform", "value": badge, "inline": True},
                {"name": "Product Name", "value": product_name, "inline": False},
                {"name": "Current Price", "value": price if price else "N/A", "inline": True},
                {"name": "Status", "value": status_text, "inline": True}
            ],
            "footer": {
                "text": f"{platform_name} Hyperlocal Stock Tracker"
            }
        }

        if location_name:
            embed["fields"].append({"name": "Target Location", "value": location_name, "inline": False})

        if details_link:
            embed["url"] = details_link
            embed["fields"].append({"name": "Link", "value": f"[View on {platform_name}]({details_link})", "inline": False})

        payload = {
            "username": bot_username,
            "avatar_url": bot_avatar,
            "embeds": [embed]
        }

        headers = {"Content-Type": "application/json"}
        sent_success = False

        if self.webhook_url and "YOUR_WEBHOOK" not in self.webhook_url:
            try:
                response = requests.post(self.webhook_url, headers=headers, data=json.dumps(payload), timeout=10)
                if response.status_code in [200, 204]:
                    print(f"[+] Webhook notification sent for [{platform_name}] '{product_name}' ({status}).")
                    sent_success = True
                else:
                    print(f"[-] Webhook failed ({response.status_code}). Attempting Bot API fallback...")
            except Exception as e:
                print(f"[-] Webhook exception ({e}). Attempting Bot API fallback...")

        # Fallback to Discord Bot REST API if Webhook failed or was unavailable
        if not sent_success:
            import config
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
                        print(f"[+] Discord Bot API notification delivered for [{platform_name}] '{product_name}' ({status}).")
                        return True
                    else:
                        print(f"[-] Discord Bot API returned status {bot_resp.status_code}: {bot_resp.text}")
                except Exception as e:
                    print(f"[-] Discord Bot API exception: {e}")

        return sent_success

def get_notifier(webhook_url):
    """
    Factory function to return the correct notifier.
    Currently only supports Discord, but can be extended here.
    """
    return DiscordNotifier(webhook_url)



