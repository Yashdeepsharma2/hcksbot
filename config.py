import os

import dotenv

dotenv.load_dotenv("local.env")

api_id = 11573285
api_hash = "f2cc3fdc32197c8fbaae9d0bf69d2033"
BOT_TOKEN = "6443237594:AAE1k8Ju2PGci7YgrnI0r8rlBWb9FbwM2DA"
FORCE_JOIN_CHAT_ID = int(os.environ.get("FORCE_JOIN_CHAT_ID", 1))
CHANNEL_LINK = os.environ.get("CHANNEL_LINK")
LOG_STRING_SESSION = int(os.environ.get("LOG_STRING_SESSION", 1))
