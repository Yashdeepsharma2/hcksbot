import base64
import struct

from pyrogram.storage.storage import Storage
from telethon import TelegramClient
from telethon.sessions import StringSession

from config import *

"""
async def _telethon(string):
    temp_client = TelegramClient(StringSession(string), api_id, api_hash)
    await temp_client.start()
    my_self = await temp_client.get_me()
    await temp_client.disconnect()
    return StringSession(string), my_self
"""


def _pyro(dc_id, auth_key, user_id=999999999, test_mode=False, is_bot=False):
    ssf = Storage.SESSION_STRING_FORMAT
    print(ssf, dc_id, auth_key, user_id, test_mode, is_bot)
    return (
        base64.urlsafe_b64encode(
            struct.pack(ssf, dc_id, test_mode, auth_key, user_id, is_bot)
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


"""
async def _convert(string):
    telethon_session, user_obj = await _telethon(string)
    pyro_session = _pyro(
        telethon_session.dc_id,
        telethon_session.auth_key.key,
        user_obj.id,
        False,
        user_obj.bot,
    )
    print(pyro_session)
    return pyro_session
"""
