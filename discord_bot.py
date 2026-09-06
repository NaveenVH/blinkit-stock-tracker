import os
import sys
import re
import discord
from dotenv import load_dotenv
import firebase_setup

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if not BOT_TOKEN:
    print("WARNING: DISCORD_BOT_TOKEN environment variable is not set.")
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"\n[+] Discord Bot Listener online as {client.user} (ID: {client.user.id})")
    print("Listing accessible channels:")
    for guild in client.guilds:
        print(f" Guild: {guild.name} (ID: {guild.id})")
        for channel in guild.text_channels:
            print(f"   - Channel: #{channel.name} (ID: {channel.id})")
    print("Ready and listening for incoming Blinkit product links...")

@client.event
async def on_message(message):
    # Ignore messages sent by any bot (including webhooks) or by self
    if message.author.bot or message.webhook_id or message.author == client.user:
        return

    content = message.content.strip()
    print(f"\n[!] INCOMING DISCORD MSG from {message.author} in #{message.channel}: '{content}'")

    # Combine content with any embed text/url
    text_to_check = content
    if message.embeds:
        for emb in message.embeds:
            text_to_check += f" {emb.title or ''} {emb.description or ''} {emb.url or ''}"

    # Check if message contains a Blinkit link or product ID pattern or 'Check out'
    if "blinkit.com/prn/x/prid/" in text_to_check or "prid/" in text_to_check or "Check out" in text_to_check or re.search(r'\b7\d{5}\b', text_to_check):
        print(f"[+] Extracting Blinkit product from: {text_to_check}")

        # parse_and_add_product automatically dispatches a single formatted Webhook embed to Discord
        result = firebase_setup.parse_and_add_product(text_to_check)
        if result:
            print(f"[+] Processed product {result.get('product_id')} -> {result.get('status_label', 'Registered/Toggled')}")

def run_bot():
    client.run(BOT_TOKEN)

if __name__ == "__main__":
    run_bot()
