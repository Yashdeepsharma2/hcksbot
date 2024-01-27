import dotenv
import os

dotenv.load_dotenv("local.env")

api_id = int(os.environ.get("API_ID") or 6)
api_hash = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
FORCE_JOIN_CHAT_ID = int(os.environ.get('FORCE_JOIN_CHAT_ID', 1))
CHANNEL_LINK = os.environ.get('CHANNEL_LINK')
LOG_STRING_SESSION = int(os.environ.get('LOG_STRING_SESSION', 1))
