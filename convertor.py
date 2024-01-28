import base64
import struct

from pyrogram import utils
from pyrogram.storage.storage import Storage
from telethon import TelegramClient
from telethon.sessions import StringSession

from config import *


async def _telethon(string):
    temp_client = TelegramClient(StringSession(string), api_id, api_hash)
    await temp_client.start()
    my_self = await temp_client.get_me()
    await temp_client.disconnect()
    return StringSession(string), my_self


def _pyro(dc_id, auth_key, user_id=999999999, test_mode=False, is_bot=False):
    ssf = (
        Storage.SESSION_STRING_FORMAT
        if user_id < utils.MAX_USER_ID_OLD
        else Storage.SESSION_STRING_FORMAT_64
    )
    print(dc_id, auth_key, user_id, test_mode, is_bot)
    return (
        base64.urlsafe_b64encode(
            struct.pack(ssf, dc_id, test_mode, auth_key, user_id, is_bot)
        )
        .decode()
        .rstrip("=")
    )


async def _convert(string):
    telethon_session, user_obj = await _telethon(string)
    # Assuming t.dc_id and t.auth_key.key are attributes of telethon_session
    pyro_session = _pyro(
        telethon_session.dc_id,
        telethon_session.auth_key.key,
        user_obj.id,
        False,
        user_obj.bot,
    )
    print(pyro_session)
    return pyro_session
