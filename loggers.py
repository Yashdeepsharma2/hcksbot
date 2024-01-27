import logging

logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("telethon").setLevel(logging.WARNING)
logging.basicConfig(
            level=logging.INFO,
            datefmt="[%d/%m/%Y %H:%M:%S]",
            format="%(asctime)s - [BOT] >> %(levelname)s << %(message)s",
            handlers=[logging.FileHandler("aman.log"), logging.StreamHandler()],
    )
