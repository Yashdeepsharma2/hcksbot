import base64
import struct

from pyrogram.storage.storage import Storage
from telethon import TelegramClient
from telethon.sessions import StringSession

from config import *


def _pyro(dc_id, auth_key, user_id=999999999, test_mode=False, is_bot=False):
    ssf = Storage.SESSION_STRING_FORMAT
    return (
        base64.urlsafe_b64encode(
            struct.pack(ssf, dc_id, api_id, test_mode, auth_key, user_id, is_bot)
        )
        .decode()
        .rstrip("=")
    )

async def _convert(string):
    temp_client = TelegramClient(StringSession(string), api_id, api_hash)
    await temp_client.start()
    my_self = await temp_client.get_me()
    await temp_client.disconnect()
    pyro_session = _pyro(
        temp_client.session.dc_id,
        temp_client.session.auth_key.key,
        my_self.id,
        False,
        my_self.bot,
    )
    return pyro_session
