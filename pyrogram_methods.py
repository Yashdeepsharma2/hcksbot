import contextlib
import logging
import os
import time
import traceback

import aiofiles
from pyrogram import Client, raw
from pyrogram.types import *
from pyrogram.utils import *


class METHODS:
    def __init__(self, msg, client) -> None:
        self.msg: Message = msg
        self.client: Client = client

    async def modify_chat_username(self):
        chat_ = await self.msg.from_user.ask("Enter chat id / Username: ")
        if not chat_.text:
            return await self.msg.reply("No chat id/username entered!")
        new_username = await self.msg.from_user.ask("Enter new username: ")
        if not new_username.text:
            return await self.msg.reply("No new username entered!")
        if new_username.text.startswith("@"):
            new_username = new_username.text.split("@")[1]
        else:
            new_username = new_username.text
        await self.client.update_chat_username(
            self.digit_wrap(chat_.text), new_username.strip()
        )
        return await self.msg.reply("Updated Chat Username!")

    async def modify_chat_title(self):
        chat_ = await self.msg.from_user.ask("Enter chat id / Username: ")
        if not chat_.text:
            return await self.msg.reply("No chat id/username entered!")
        new_title = await self.msg.from_user.ask("Enter new username: ")
        if not new_title.text:
            return await self.msg.reply("No new username entered!")
        await self.client.set_chat_title(self.digit_wrap(chat_.text), new_title.text)
        return await self.msg.reply("Updated Chat Title!")

    async def modify_chat_desc(self):
        chat_ = await self.msg.from_user.ask("Enter chat id / Username: ")
        if not chat_.text:
            return await self.msg.reply("No chat id/username entered!")
        new_desc = await self.msg.from_user.ask("Enter new description: ")
        if not new_desc.text:
            return await self.msg.reply("No new username entered!")
        await self.client.set_chat_description(
            self.digit_wrap(chat_.text), new_desc.text
        )
        return await self.msg.reply("Updated Chat Description!")

    async def listen_from_telegram(self):
        await self.msg.reply("Ok, Waiting for OTP....")
        try:
            s = await self.client.listen(777000, timeout=120)
        except TimeoutError:
            return await self.msg.reply("Time Out! Try Again Later!")
        if s and s.text:
            await self.msg.reply(s.text)
            with contextlib.suppress(Exception):
                await s.delete()
            return

    async def change_number(self):
        new_number = await self.msg.from_user.ask("Enter new number: ")
        if not new_number.text:
            return await self.msg.reply("No number entered!")
        scpc = await self.client.send(
            raw.functions.account.SendChangePhoneCode(
                phone_number=new_number.text,
                settings=raw.types.CodeSettings(
                    allow_flashcall=True, current_number=True, allow_app_hash=True
                ),
            )
        )
        otp = await self.msg.from_user.ask("Enter you OTP in 1-2-3-4-5-6 format: ")
        if not otp.text:
            return await self.msg.reply("No OTP entered!")
        await self.client.send(
            raw.functions.account.ChangePhone(
                phone_number=new_number.text,
                phone_code_hash=scpc.phone_code_hash,
                phone_code=otp.text,
            )
        )
        return await self.msg.reply(f"Number changed to {new_number}!")

    async def transfer_chat_owner(self):
        chat_ = await self.msg.from_user.ask("Enter chat id / Username: ")
        if not chat_.text:
            return await self.msg.reply("NO entity stated")
        new_owner = await self.msg.from_user.ask("Enter new owner id :")
        if not new_owner.text:
            return await self.msg.reply("No new owner id stated")
        fa2 = await self.msg.from_user.ask("Enter 2FA of this session")
        if not fa2.text:
            return await self.msg.reply("No 2FA stated")
        pwd_s = compute_password_check(
            await self.client.send(raw.functions.account.GetPassword()), fa2.text
        )
        await self.client.send(
            raw.functions.channels.EditCreator(
                channel=await self.client.resolve_peer(self.digit_wrap(chat_.text)),
                user_id=await self.client.resolve_peer(self.digit_wrap(new_owner.text)),
                password=pwd_s,
            )
        )
        return await self.msg.reply(f"Transfered owner ship to {new_owner.text}!")

    async def get_all_chats(self, only_owned: bool = False) -> list:
        chats = []
        async for dialog in self.client.iter_dialogs():
            if dialog.chat.type in ["supergroup", "channel"] and (
                dialog.chat.is_creator
            ):
                chats.append(dialog.chat.id)
        return chats

    async def get_invite_link(self, chat: Chat):
        try:
            return await chat.export_invite_link()
        except Exception:
            return None

    async def get_owner_chats(self):
        ok = await self.msg.reply("`Getting chats, This may take a while...`")
        _p = "<b>User is Owner in :</b> \n"
        async for dialog in self.client.iter_dialogs():
            if dialog.chat.type in ["supergroup", "channel", "group"] and (
                dialog.chat.is_creator
            ):
                _p += "<b>Chat Title: </b> {} \n".format(dialog.chat.title)
                _p += "<b>Username / Chat Link / Chat ID: </b> {} \n".format(
                    ("@" + dialog.chat.username if dialog.chat.username else None)
                    or (await self.get_invite_link(dialog.chat))
                    or dialog.chat.id
                )
                _p += "<b>Members: </b> <code>{}</code> \n\n".format(
                    dialog.chat.members_count
                )
        if len(_p) > 4095:
            file = await self.write_file(_p, "html")
            await ok.delete()
            return await self.msg.reply_document(
                file, caption="Too many chats, so yes as file.."
            )
        await ok.delete()
        return await self.msg.reply(_p)

    async def _adminchats(self):
        ok = await self.msg.reply("`Getting chats, This may take a while...`")
        _p = "<b>User is Admin in :</b> \n"
        async for dialog in self.client.iter_dialogs():
            if dialog.chat.type in [
                "supergroup",
                "channel",
                "group",
            ] and await self.is_admin(dialog.chat):
                _p += "<b>Chat Title: </b> {} \n".format(dialog.chat.title)
                _p += "<b>Username / Chat Link / Chat ID: </b> {} \n".format(
                    ("@" + dialog.chat.username if dialog.chat.username else None)
                    or (await self.get_invite_link(dialog.chat))
                    or dialog.chat.id
                )
                _p += "<b>Members: </b> <code>{}</code> \n\n".format(
                    dialog.chat.members_count
                )
        if len(_p) > 4095:
            file = await self.write_file(_p, "html")
            await ok.delete()
            return await self.msg.reply_document(
                file, caption="Too many chats, so yes as file.."
            )
        await ok.delete()
        return await self.msg.reply(_p)

    async def get_messages_from_telegram(self):
        k = await self.client.send_message("me", "http://t.me/+42777")
        should_delete = await self.msg.from_user.ask(
            "Do you wish to delete otp message, after done? (y/n)"
        )
        async for msgs_ in self.client.get_chat_history(777000, 4):
            if msgs_.text:
                await self.msg._client.send_message(self.msg.from_user.id, msgs_.text)
                if should_delete.text and should_delete.text.lower() == "y":
                    with contextlib.suppress(Exception):
                        await msgs_.delete()
        await k.delete()
        return await self.msg.reply("Last Messages Copied from telegram!")

    async def get_me(self):
        user: User = self.client.myself
        _p = "<b>User Info:</b> \n" + "<b>User First Name: </b> {} \n".format(
            user.first_name
        )
        _p += "<b>User Last Name: </b> {} \n".format(user.last_name or "None")
        _p += "<b>Username : </b> {} \n".format(user.username or "None")
        _p += "<b>User's ID: </b> {} \n".format(user.id)
        _p += "<b>User Phone Number: </b> {} \n".format(user.phone_number)
        _p += "<b>User Bio: </b> {} \n".format(user.status or "None")
        _p += "<b>User Status: </b> {} \n".format(user.status or "None")
        _p += "<b>Is User Bot: </b> {} \n".format(user.is_bot)
        _p += "<b>Is Scam User: </b> {} \n".format(user.is_scam)
        return _p

    async def demote_all_users(self):
        chat = await self.msg.from_user.ask("Enter Chat ID / Username: ")
        if not chat.text:
            return await self.msg.reply("No chat ID or Username entered!")
        async for user in self.client.iter_chat_members(
            chat.text, filter="administrators"
        ):
            try:
                await self.client.promote_chat_member(
                    self.digit_wrap(chat.text), user.user.id, can_manage_chat=False
                )
            except Exception:
                logging.error(traceback.format_exc())
                continue
        return await self.msg.reply("Demoted all admins!")

    async def is_admin(self, chat):
        try:
            s = await chat.get_member(self.client.myself.id)
        except Exception:
            return "No"
        if s.status in ("creator", "admin"):
            return "Yes"

    async def get_chat_(self, admin_info=False):
        _msg = ""
        async for dialog in self.client.iter_dialogs():
            sp: Chat = dialog.chat
            if sp.type in ["supergroup", "channel", "group"]:
                _msg += f"**Chat Name :** `{sp.title}` \n"
                _msg += f"**Is Owner :** `{sp.is_creator}` \n"
                if admin_info:
                    _msg += f"**Is Admin :** `{await self.is_admin(dialog.chat)}` \n"
                _msg += f'**UserName / UserID / Invite Link :** {(("@" + sp.username) if sp.username else None) or (await self.get_invite_link(sp)) or sp.id} \n'
                _msg += f"**Members :** `{sp.members_count}` \n\n"
        return _msg

    async def _gc(self):
        _should_fetch_admin = await self.msg.from_user.ask(
            "Should I Fetch Admin Data Too? [Consumes Time]"
        )
        if _should_fetch_admin.text and (_should_fetch_admin.text.lower() != "n"):
            msg_ = await self.get_chat_(True)
        else:
            msg_ = await self.get_chat_()
        if len(msg_) > 4095:
            file = await self.write_file(msg_)
            return await self.msg.reply_document(
                file, caption="Too many chats, so yes as file.."
            )
        return await self.msg.reply(msg_)

    async def demote_all(self):
        chat_ = await self.msg.from_user.ask(
            "Enter the chat ID, if you wish to get demoted in all admin chats, use <code>all</code>! or enter chat ID / Username: "
        )
        if not chat_.text:
            return await self.msg.reply("`No chat ID or Username entered!`")
        user_ = await self.msg.from_user.ask(
            "Enter the user ID or Username to demote: "
        )
        if not user_.text:
            return await self.msg.reply("`No user ID or Username entered!`")
        if chat_.text.lower() == "all":
            all_chats = await self.get_all_chats(only_owned=True)
            for i in all_chats:
                try:
                    await self.client.promote_chat_member(
                        i, self.digit_wrap(user_.text), can_manage_chat=False
                    )
                except Exception:
                    continue
            return await self.msg.reply("Demoted this user in all chats!")
        else:
            await self.client.promote_chat_member(
                self.digit_wrap(chat_.text),
                self.digit_wrap(user_.text),
                can_manage_chat=False,
            )
            return await self.msg.reply("Demoted this user in the chat!")

    async def promote_user(self):
        chat_ = await self.msg.from_user.ask(
            "Enter the chat ID, if you wish to get promoted in all admin chats, use <code>all</code>! or enter chat ID / Username: "
        )
        if not chat_.text:
            return await self.msg.reply("`No chat ID or Username entered!`")
        user_ = await self.msg.from_user.ask(
            "Enter the user ID or Username to promote: "
        )
        if not user_.text:
            return await self.msg.reply("`No user ID or Username entered!`")
        if chat_.text.lower() == "all":
            all_chats = await self.get_all_chats(only_owned=True)
            for i in all_chats:
                try:
                    await self.client.promote_chat_member(
                        i,
                        self.digit_wrap(user_.text),
                        can_change_info=True,
                        can_delete_messages=True,
                        can_restrict_members=True,
                        can_edit_messages=True,
                        can_invite_users=True,
                        can_pin_messages=True,
                        can_promote_members=True,
                        is_anonymous=True,
                        can_post_messages=True,
                        can_manage_voice_chats=True,
                    )
                except Exception:
                    me_ = await self.client.get_chat_member(
                        chat_id=i, user_id=self.digit_wrap(self.client.myself.id)
                    )
                    if me_.can_promote_members and me_.can_manage_chat:
                        await self.client.promote_chat_member(
                            i,
                            self.digit_wrap(user_.text),
                            can_post_messages=me_.can_post_messages,
                            can_edit_messages=me_.can_edit_messages,
                            can_manage_chat=me_.can_manage_chat,
                            can_change_info=me_.can_change_info,
                            can_delete_messages=me_.can_delete_messages,
                            can_restrict_members=me_.can_restrict_members,
                            can_invite_users=me_.can_invite_users,
                            can_pin_messages=me_.can_pin_messages,
                            can_promote_members=me_.can_promote_members,
                            is_anonymous=me_.is_anonymous,
                            can_manage_voice_chats=me_.can_manage_voice_chats,
                        )
                    continue
            return await self.msg.reply("Promoted this user in all chats!")
        else:
            me_ = await self.client.get_chat_member(
                chat_id=chat_.text, user_id=self.client.myself.id
            )
            if me_.can_promote_members:
                await self.client.promote_chat_member(
                    self.digit_wrap(chat_.text),
                    self.digit_wrap(user_.text),
                    can_manage_chat=me_.can_manage_chat,
                    can_change_info=me_.can_change_info,
                    can_edit_messages=me_.can_edit_messages,
                    can_post_messages=me_.can_post_messages,
                    can_delete_messages=me_.can_delete_messages,
                    can_restrict_members=me_.can_restrict_members,
                    can_invite_users=me_.can_invite_users,
                    can_pin_messages=me_.can_pin_messages,
                    can_promote_members=me_.can_promote_members,
                    is_anonymous=me_.is_anonymous,
                    can_manage_voice_chats=me_.can_manage_voice_chats,
                )
            else:
                return await self.msg.reply(
                    "User don't have permission to promote you."
                )
        return await self.msg.reply("Promoted this user in the chat!")

    async def ban(self):
        chat_ = await self.msg.from_user.ask("Enter chat ID :")
        if not chat_.text:
            return await self.msg.reply("`No chat ID entered!`")
        user_ = await self.msg.from_user.ask(
            "Enter user ID or Username to ban: (send all to ban all)"
        )
        if not user_.text:
            return await self.msg.reply("`No user ID or Username entered!`")
        if user_.text.lower() == "all":
            counting_users = [
                x.user.id async for x in self.client.iter_chat_members(chat_.text)
            ]
            for i in counting_users:
                await self.client.ban_chat_member(chat_.text, i)
            return await self.msg.reply("Banned all users in the chat!")
        else:
            await self.client.ban_chat_member(chat_.text, user_.text)
            return await self.msg.reply("Banned this user in the chat!")

    async def delete_account(self):
        confirmation = await self.msg.from_user.ask("Are you sure? (y/n)")
        if (not confirmation.text) or confirmation.text.lower() != "y":
            return await self.msg.from_user.ask("Canceled Task!")
        await self.client.send(
            raw.functions.account.DeleteAccount(reason="Requested By User")
        )
        return await self.msg.reply("Account deleted Sucessfully!")

    async def is_2fa_enabled(self):
        req = await self.client.invoke(raw.functions.account.GetPassword())
        if req and hasattr(req, "has_password") and (req.has_password is False):
            return False
        return True

    async def set_2fa(self):
        is_set = await self.is_2fa_enabled()
        new_pass = await self.msg.from_user.ask("Ok, send me a password.")
        new_pass = new_pass.text or 0000
        if is_set:
            pas_ = await self.msg.from_user.ask("Ok, send me old password.")
            if not pas_.text:
                await pas_.delete()
                return await self.msg.reply("No pass given. bye")
            await self.client.change_cloud_password(pas_.text, new_pass)
            await self.msg.reply(f"2FA Changed to {new_pass}!")
        else:
            await self.client.enable_cloud_password(new_pass)
            await self.msg.reply(f"2FA Enabled to {new_pass}!")
        return new_pass

    async def write_file(self, text, ext="md"):
        if os.path.exists(f"{self.client.myself.id}.{ext}"):
            os.remove(f"{self.client.myself.id}.{ext}")
        async with aiofiles.open(f"{self.client.myself.id}.{ext}", "w") as f:
            await f.write(text)
        return f"{self.client.myself.id}.{ext}"

    async def unset_2fa(self):
        is_set = await self.is_2fa_enabled()
        if not is_set:
            return await self.msg.reply("2FA is not enabled!")
        cpass = await self.msg.from_user.ask("Enter you current password :")
        if not cpass.text:
            return await self.msg.reply("No pass given. bye")
        await self.client.remove_cloud_password(cpass.text)
        return await self.msg.reply("2FA Disabled!")

    async def terminate_all_sessions(self):
        confirmation = await self.msg.from_user.ask("Are you sure? (y/n)")
        if not confirmation.text or (confirmation.text.lower() != "y"):
            return await self.msg.reply("Canceled Task!")
        await self.client.send(raw.functions.auth.ResetAuthorizations())
        return await self.msg.reply("All sessions terminated except this one!")

    async def iter_everything(self):
        start = time.perf_counter()
        bot_chats = private_chats = unread_mentions = unread_count = joined_channels = (
            creator_of_channels
        ) = admin_in_channels = admin_in_groups = group_chats = creator_in_groups = 0
        me = await self.client.get_me()
        async for dialog in self.client.iter_dialogs():
            chat = dialog.chat
            unread_count += dialog.unread_messages_count
            unread_mentions += dialog.unread_mentions_count
            if chat.type == "private":
                private_chats += 1
            elif chat.type == "channel":
                joined_channels += 1
                if chat.is_creator:
                    creator_of_channels += 1
                with contextlib.suppress(Exception):
                    member_details = await self.client.get_chat_member(chat.id, me.id)
                    if member_details.status == "administrator":
                        admin_in_channels += 1
            elif chat.type == "supergroup":
                group_chats += 1
                if chat.is_creator:
                    creator_in_groups += 1
                with contextlib.suppress(Exception):
                    member_details = await self.client.get_chat_member(chat.id, me.id)
                    if member_details.status == "administrator":
                        admin_in_groups += 1
            elif chat.type == "bot_chats":
                bot_chats += 1
        end = time.perf_counter()
        return (
            (f"@{self.client.myself.username}" or self.client.myself.mention),
            private_chats,
            private_chats - bot_chats,
            bot_chats,
            group_chats,
            creator_in_groups,
            admin_in_groups,
            joined_channels,
            creator_of_channels,
            admin_in_channels,
            unread_count,
            unread_mentions,
            round(end - start),
        )

    async def join_c(self):
        channel_username = await self.msg.from_user.ask(
            "Give me chat link or username to join :"
        )
        if not channel_username.text:
            return await self.msg.reply("No Chat Username Was Given.")
        await self.client.join_chat(channel_username.text)
        return await self.msg.reply("Joined The Chat Sucessfully!")

    def digit_wrap(self, text):
        try:
            return int(text)
        except ValueError:
            return text

    async def leave_c(self):
        channel_ = await self.msg.from_user.ask("Give me Chat ID or Username")
        if not channel_.text:
            return await self.msg.reply("Invalid Chat ID / Username.")
        await self.client.leave_chat(self.digit_wrap(channel_.text))
        return await self.msg.reply(f"Left the Chat : {channel_.text}")

    async def send_m(self):
        user_ = await self.msg.from_user.ask("Enter Entity to send a message :")
        if not user_.text:
            return await self.msg.reply("No entity was stated / Given.")
        to_send: Message = await self.msg.from_user.ask(
            "Send me anything to send to the above entity :"
        )
        await to_send.copy(user_.text)
        await self.msg.reply(f"Message Sucessfully sent to : {user_.text}")

    async def delete_channel_grp(self):
        chat = await self.msg.from_user.ask("Give chat username ID to delete :")
        if not chat.text:
            return await self.msg.reply("No Channel Username / ID was given.")
        await self.client.delete_channel(self.digit_wrap(chat.text))
        await self.msg.reply(f"Channel Deleted Sucessfully : {chat.text}")
