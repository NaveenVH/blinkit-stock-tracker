import os
import sys
import discord
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

token = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"\n[TEST BOT READY] Logged in as: {client.user}")
    print("Listing accessible channels:")
    for guild in client.guilds:
        print(f" Guild: {guild.name} (ID: {guild.id})")
        for channel in guild.text_channels:
            print(f"   - Channel: #{channel.name} (ID: {channel.id})")
    print("\n>>> Waiting for ANY message in Discord... (Type anything in #stockalertsnvh)")

@client.event
async def on_message(message):
    print(f"\n[RECEIVED MSG] Author: {message.author} | Channel: #{message.channel.name} | Content: '{message.content}'")

if __name__ == "__main__":
    client.run(token)

