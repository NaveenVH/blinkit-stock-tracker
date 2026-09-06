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
    # Ignore messages sent by the bot itself
    if message.author == client.user:
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

        result = firebase_setup.parse_and_add_product(text_to_check)
        
        if result:
            embed = discord.Embed(
                title="✅ Product Added to Stock Tracker",
                description=f"**{result['product_name']}** has been registered in Firebase!",
                color=0x2ecc71
            )
            embed.add_field(name="Product ID", value=f"`{result['product_id']}`", inline=True)
            embed.add_field(name="Active Locations", value=str(result['locations_count']), inline=True)
            embed.add_field(name="Next Crawl Status", value="🟢 Active (Will check on next run)", inline=False)
            embed.set_footer(text="Blinkit Stock Tracker Auto-Ingestion")

            await message.reply(embed=embed)
            print(f"[+] Sent Discord confirmation reply for Product {result['product_id']}.")

def run_bot():
    client.run(BOT_TOKEN)

if __name__ == "__main__":
    run_bot()
