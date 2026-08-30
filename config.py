import os
from dotenv import load_dotenv

# Load local .env file if it exists
load_dotenv()

# Firebase Config
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "blinkit-stock-bot-2026")
# Can be the raw JSON string of the service account credential
FIREBASE_SERVICE_ACCOUNT_JSON = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
# Or a path to the service account JSON file for local dev
FIREBASE_SERVICE_ACCOUNT_FILE = os.getenv("FIREBASE_SERVICE_ACCOUNT_FILE", "serviceAccountKey.json")

# Fallback configurations if Firestore database is empty or not used
DEFAULT_DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK_URL")
DEFAULT_PRODUCT_NAME = os.getenv("TARGET_PRODUCT", "Hot Wheels Batmobile Die Cast Car")
DEFAULT_PRODUCT_ID = os.getenv("TARGET_PRODUCT_ID", "804937")
DEFAULT_LATITUDE = float(os.getenv("LATITUDE", "12.9716"))  # Bangalore default
DEFAULT_LONGITUDE = float(os.getenv("LONGITUDE", "77.5946")) # Bangalore default

