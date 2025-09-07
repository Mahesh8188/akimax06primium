import sys
import glob
import importlib
from pathlib import Path
from pyrogram import idle
import logging
import logging.config

# Get logging configurations
logging.config.fileConfig("logging.conf")
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("imdbpy").setLevel(logging.ERROR)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.getLogger("aiohttp").setLevel(logging.ERROR)
logging.getLogger("aiohttp.web").setLevel(logging.ERROR)


from pyrogram import __version__
from pyrogram.raw.all import layer
from database.ia_filterdb import Media
from database.users_chats_db import db
from info import *
from utils import temp
from Script import script
from datetime import date, datetime
import pytz
from aiohttp import web
from plugins import web_server, check_expired_premium
import pyrogram.utils
import asyncio
from Jisshu.bot import JisshuBot
from Jisshu.util.keepalive import ping_server
from Jisshu.bot.clients import initialize_clients

ppath = "plugins/*.py"
files = glob.glob(ppath)
JisshuBot.start()
loop = asyncio.get_event_loop()

pyrogram.utils.MIN_CHANNEL_ID = -1009147483647


from pyrogram import filters, Client
from pyrogram.types import ChatMemberUpdated

# =========================
# Allowed groups load/save
# =========================
def load_allowed_groups():
    try:
        with open("allowed_groups.txt", "r") as f:
            return [x.strip() for x in f.readlines()]  # string return karo
    except FileNotFoundError:
        return []

def save_allowed_groups(groups):
    with open("allowed_groups.txt", "w") as f:
        for g in groups:
            f.write(f"{g}\n")

# =========================
# /allow command (owner only)
# =========================
OWNER_ID = 6859451629  # apna telegram id

@JisshuBot.on_message(filters.command("allow") & filters.user(OWNER_ID))
async def allow_group(client, message):
    groups = load_allowed_groups()
    chat_id = str(message.chat.id)  # string me convert karo
    if chat_id not in groups:
        groups.append(chat_id)
        save_allowed_groups(groups)
        await message.reply("✅ This group is now allowed for the bot.")
    else:
        await message.reply("⚠️ Ye group already allowed hai.")

# =========================
# Event 1: on_chat_member_updated
# =========================
@JisshuBot.on_chat_member_updated()
async def on_bot_added(client, chat_member_update: ChatMemberUpdated):
    try:
        if chat_member_update.new_chat_member and chat_member_update.new_chat_member.user.id == client.me.id:
            chat_id = str(chat_member_update.chat.id)  # string me convert
            adder_id = chat_member_update.from_user.id if chat_member_update.from_user else None
            groups = load_allowed_groups()

            # agar owner ne add kiya hai → force allow
            if adder_id == OWNER_ID:
                if chat_id not in groups:
                    groups.append(chat_id)
                    save_allowed_groups(groups)
                await client.send_message(chat_id, "✅ Owner ne mujhe add kiya hai. Main yaha rahunga!")
                return

            # normal user add kare to allow check
            if chat_id not in groups:
                await client.send_message(chat_id, "𝗦𝘂𝗻𝗼 𝗚𝗿𝗼𝘂𝗽 𝗸𝗲 𝗟𝗼𝗴𝗼 𝗜𝘀 𝗚𝗿𝗼𝘂𝗽 𝗞𝗮 𝗢𝘄𝗻𝗲𝗿 𝗕𝗵𝗲𝗻 𝗸𝗮 𝗟𝗼𝗱𝗮 𝗵𝗮𝗶... 𝗔𝘀𝗹𝗶 𝗔𝗞 𝗜𝗠𝗔𝗫 𝗝𝗼𝗶𝗻 𝗸𝗿𝗼 @akimax06")
                await client.leave_chat(chat_id)
            else:
                await client.send_message(chat_id, "✅ Bot is ready in this allowed group!")
    except Exception as e:
        print(f"Error in on_chat_member_updated: {e}")

# =========================
# Event 2: new_chat_members (Fallback)
# =========================
@JisshuBot.on_message(filters.new_chat_members)
async def when_added(client, message):
    try:
        for user in message.new_chat_members:
            if user.id == client.me.id:  # bot khud add hua hai
                chat_id = str(message.chat.id)  # string me convert
                adder_id = message.from_user.id if message.from_user else None
                groups = load_allowed_groups()

                # owner add kare → force allow
                if adder_id == OWNER_ID:
                    if chat_id not in groups:
                        groups.append(chat_id)
                        save_allowed_groups(groups)
                    await message.reply("✅ Owner ne add kiya hai. Main yaha rahunga!")
                    return

                # normal user add kare
                if chat_id not in groups:
                    await message.reply("𝗦𝘂𝗻𝗼 𝗚𝗿𝗼𝘂𝗽 𝗸𝗲 𝗟𝗼𝗴𝗼 𝗜𝘀 𝗚𝗿𝗼𝘂𝗽 𝗞𝗮 𝗢𝘄𝗻𝗲𝗿 𝗕𝗵𝗲𝗻 𝗸𝗮 𝗟𝗼𝗱𝗮 𝗵𝗮𝗶... 𝗔𝘀𝗹𝗶 𝗔𝗞 𝗜𝗠𝗔𝗫 𝗝𝗼𝗶𝗻 𝗸𝗿𝗼 @akimax06")
                    await client.leave_chat(chat_id)
                else:
                    await message.reply("✅ Bot is ready in this allowed group!")
    except Exception as e:
        print(f"Error in when_added: {e}")



async def Jisshu_start():
    print("\n")
    print("Credit - Telegram @JISSHU_BOTS")
    bot_info = await JisshuBot.get_me()
    JisshuBot.username = bot_info.username
    await initialize_clients()
    for name in files:
        with open(name) as a:
            patt = Path(a.name)
            plugin_name = patt.stem.replace(".py", "")
            plugins_dir = Path(f"plugins/{plugin_name}.py")
            import_path = "plugins.{}".format(plugin_name)
            spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
            load = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(load)
            sys.modules["plugins." + plugin_name] = load
            print("JisshuBot Imported => " + plugin_name)
    if ON_HEROKU:
        asyncio.create_task(ping_server())
    b_users, b_chats = await db.get_banned()
    temp.BANNED_USERS = b_users
    temp.BANNED_CHATS = b_chats
    await Media.ensure_indexes()
    me = await JisshuBot.get_me()
    temp.ME = me.id
    temp.U_NAME = me.username
    temp.B_NAME = me.first_name
    temp.B_LINK = me.mention
    JisshuBot.username = "@" + me.username
    JisshuBot.loop.create_task(check_expired_premium(JisshuBot))
    logging.info(
        f"{me.first_name} with for Pyrogram v{__version__} (Layer {layer}) started on {me.username}."
    )
    logging.info(script.LOGO)
    tz = pytz.timezone("Asia/Kolkata")
    today = date.today()
    now = datetime.now(tz)
    time = now.strftime("%H:%M:%S %p")
    await JisshuBot.send_message(
        chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(me.mention, today, time)
    )
    await JisshuBot.send_message(
        chat_id=SUPPORT_GROUP, text=f"<b>{me.mention} ʀᴇsᴛᴀʀᴛᴇᴅ 🤖</b>"
    )
    app = web.AppRunner(await web_server())
    await app.setup()
    bind_address = "0.0.0.0"
    await web.TCPSite(app, bind_address, PORT).start()
    await idle()


if __name__ == "__main__":
    try:
        loop.run_until_complete(Jisshu_start())
    except KeyboardInterrupt:
        logging.info("Service Stopped Bye 👋")
