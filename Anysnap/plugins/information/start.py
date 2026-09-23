# ==========================================================
# Copyright (c) 2026 Anysnap
# All Rights Reserved.
#
# Project      : Anysnap API Telegram Music Bot
# Powered By   : Anysnap
# Type         : API Based Telegram Music Bot
#
# Channel      : @ANYSNAP
# GitHub       : https://github.com/themagmalord333-oss
#
# Unauthorized copying, modification, or redistribution
# of this source code without permission is prohibited.
# ==========================================================

from pyrogram import enums, errors, filters, types

from Anysnap import app, config, db, lang
from Anysnap.helpers import buttons, utils


# ==========================================================
# HELP
# ==========================================================

@app.on_message(
    filters.command("help")
    & filters.private
    & ~app.bl_users
)
@lang.language()
async def _help(_, message: types.Message):
    """Show the help menu in private chat."""

    # Delete /help command
    try:
        await message.delete()
    except Exception:
        pass

    try:
        await message.reply_photo(
            photo=config.START_IMG,
            caption=message.lang["help_menu"],
            reply_markup=buttons.help_markup(message.lang),
            quote=True,
        )
    except Exception:
        # Fallback to text if photo cannot be sent
        try:
            await message.reply_text(
                text=message.lang["help_menu"],
                reply_markup=buttons.help_markup(message.lang),
                quote=True,
            )
        except Exception:
            pass


# ==========================================================
# START
# ==========================================================

@app.on_message(filters.command("start"))
@lang.language()
async def start(_, message: types.Message):
    """Handle the /start command."""

    # Ignore channel posts / anonymous messages
    if not message.from_user:
        return

    user_id = message.from_user.id
    private = message.chat.type == enums.ChatType.PRIVATE

    # Delete /start command in groups
    if not private:
        try:
            await message.delete()
        except Exception:
            pass

    # ======================================================
    # BLACKLIST CHECK
    # ======================================================

    if (
        user_id in app.bl_users
        and user_id not in db.notified
    ):
        return await message.reply_text(
            message.lang["bl_user_notify"]
        )

    # ======================================================
    # /start help
    # ======================================================

    if (
        private
        and len(message.command) > 1
        and message.command[1].lower() == "help"
    ):
        return await _help(_, message)

    # ======================================================
    # WELCOME MESSAGE
    # ======================================================

    if private:
        text = message.lang["start_pm"].format(
            message.from_user.first_name,
            config.BOT_NAME,
        )
    else:
        text = message.lang["start_gp"].format(
            config.BOT_NAME,
        )

    keyboard = buttons.start_key(
        message.lang,
        private,
    )

    # ======================================================
    # SEND WELCOME MESSAGE
    # ======================================================

    try:
        await message.reply_photo(
            photo=config.START_IMG,
            caption=text,
            reply_markup=keyboard,
            quote=not private,
        )

    except errors.ChatSendPhotosForbidden:
        # Photo sending is not allowed
        await message.reply_text(
            text=text,
            reply_markup=keyboard,
            quote=not private,
        )

    except Exception:
        # General fallback
        try:
            await message.reply_text(
                text=text,
                reply_markup=keyboard,
                quote=not private,
            )
        except Exception:
            pass

    # ======================================================
    # REGISTER PRIVATE USER
    # ======================================================

    if not private:
        return

    try:
        # User already exists
        if await db.is_user(user_id):
            return

        # Log new user
        await utils.send_log(message)

        # Add user to database
        await db.add_user(user_id)

    except Exception:
        # Database/logging failure should not crash the bot
        pass


# ==========================================================
# PLAYMODE / SETTINGS
# ==========================================================

@app.on_message(
    filters.command(["playmode", "settings"])
    & filters.group
    & ~app.bl_users
)
@lang.language()
async def settings(_, message: types.Message):
    """Show group play-mode settings."""

    # Delete command
    try:
        await message.delete()
    except Exception:
        pass

    # Get current play mode
    admin_only = await db.get_play_mode(
        message.chat.id
    )

    # Current/default language
    language = "en"

    await utils.safe_text(
        message,
        message.lang["start_settings"].format(
            message.chat.title
        ),
        reply_markup=buttons.settings_markup(
            message.lang,
            admin_only,
            language,
            message.chat.id,
        ),
        quote=True,
    )


# ==========================================================
# NEW CHAT MEMBER
# ==========================================================

@app.on_message(
    filters.new_chat_members,
    group=7,
)
@lang.language()
async def _new_member(_, message: types.Message):
    """Handle the bot being added to a group."""

    # Only allow supergroups
    if message.chat.type != enums.ChatType.SUPERGROUP:
        try:
            await message.chat.leave()
        except Exception:
            pass
        return

    # Check all newly added members
    for member in message.new_chat_members:

        # Ignore users; only process the bot itself
        if member.id != app.id:
            continue

        # Check if group already exists
        if await db.is_chat(message.chat.id):
            return

        # Add group to database
        await db.add_chat(message.chat.id)

        return