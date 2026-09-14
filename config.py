import os
import builtins
import datetime

# Configure timestamped print formatting for all logs (tracker.log and bot.log)
_original_print = builtins.print
def timestamped_print(*args, **kwargs):
    now_str = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    if args and isinstance(args[0], str) and args[0].startswith("\n"):
        _original_print(f"\n{now_str} " + args[0][1:], *args[1:], **kwargs)
    else:
        _original_print(now_str, *args, **kwargs)

builtins.print = timestamped_print

# Load local .env file explicitly using absolute directory path
from dotenv import load_dotenv
env_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(dotenv_path=env_file_path)
load_dotenv()



# Firebase Config
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "blinkit-stock-bot-2026")
# Can be the raw JSON string of the service account credential
FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
# Or a path to the service account JSON file for local dev
FIREBASE_SERVICE_ACCOUNT_FILE = os.getenv("FIREBASE_SERVICE_ACCOUNT_FILE", "serviceAccountKey.json")

# Fallback configurations if Firestore database is empty or not used
DEFAULT_DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
DEFAULT_PRODUCT_NAME = os.getenv("TARGET_PRODUCT", "Hot Wheels Batmobile Die Cast Car")
DEFAULT_PRODUCT_ID = os.getenv("TARGET_PRODUCT_ID", "804937")
DEFAULT_LATITUDE = float(os.getenv("LATITUDE", "12.9716"))  # Bangalore default
DEFAULT_LONGITUDE = float(os.getenv("LONGITUDE", "77.5946")) # Bangalore default


