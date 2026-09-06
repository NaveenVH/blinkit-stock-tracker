import os
import sys
import discord
from dotenv import load_dotenv
import firebase_setup

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if not BOT_TOKEN:
    print("WARNING: DISCORD_BOT_TOKEN environment variable is not set.")
    print("To run the Discord listener bot, set DISCORD_BOT_TOKEN in your .env or environment secrets.")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"[+] Discord Bot Listener online as {client.user} (ID: {client.user.id})")
    print("Listening for incoming Blinkit product links...")

@client.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == client.user:
        return

    content = message.content.strip()
    
    # Check if message contains a Blinkit link or product ID pattern
    if "blinkit.com/prn/x/prid/" in content or "prid/" in content:
        print(f"\n[!] Detected Blinkit product link from {message.author}:")
        print(f"    Message: {content}")

        result = firebase_setup.parse_and_add_product(content)
        
        if result:
            embed = discord.Embed(
                title="✅ Product Added to Stock Tracker",
                description=f"**{result['product_name']}** has been registered in Firebase!",
                color=0x2ecc71
            )
            embed.add_field(name="Product ID", value=f"`{result['product_id']}`", inline=True)
            embed.add_field(name="Active Locations", value=str(result['locations_count']), inline=True)
            embed.add_field(name="Status", value="🟢 Active (Will check on next run)", inline=False)
            embed.set_footer(text="Blinkit Stock Tracker Auto-Ingestion")

            await message.reply(embed=embed)
            print(f"[+] Sent Discord confirmation reply for Product {result['product_id']}.")
        else:
            await message.reply("⚠️ Could not extract product ID from the link. Please check the URL format.")

def run_bot():
    if not BOT_TOKEN:
        print("Error: Cannot start Discord bot without DISCORD_BOT_TOKEN.")
        sys.exit(1)
    client.run(BOT_TOKEN)

if __name__ == "__main__":
    run_bot()
