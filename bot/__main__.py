import os
import shutil, psutil
import signal

from sys import executable
import time

from telegram.ext import CommandHandler
from bot import bot, dispatcher, updater, botStartTime, AUTHORIZED_CHATS
from bot.helper.ext_utils import fs_utils
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.message_utils import LOGGER, editMessage, sendLogFile, sendMessage
from .helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time
from .helper.telegram_helper.filters import CustomFilters
from .modules import authorize, list, cancel_mirror, mirror_status, mirror, clone, watch, delete, leech_settings, speedtest, usage # noqa

from pyrogram import idle
from bot import app


def stats(update, context):
    currentTime = get_readable_time(time.time() - botStartTime)
    total, used, free = shutil.disk_usage('.')
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(psutil.net_io_counters().bytes_sent)
    recv = get_readable_file_size(psutil.net_io_counters().bytes_recv)
    cpuUsage = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage('/').percent
    stats = f'<b>╭────【 🌟 BOT STATISTICS 🌟 】</b>\n' \
            f'<b>│</b>\n' \
            f'<b>├  ⏰ Bot Uptime : {currentTime}</b>\n' \
            f'<b>├  🗄 Total Disk Space : {total}</b>\n' \
            f'<b>├  🗂 Total Used Space : {used}</b>\n' \
            f'<b>├  📂 Total Free Space : {free}</b>\n' \
            f'<b>├  📑 Data Usage 📑:</b>\n' \
            f'<b>├  📤 Total Upload : {sent}</b>\n' \
            f'<b>├  📥 Total Download : {recv}</b>\n' \
            f'<b>├  🖥️ CPU : {cpuUsage}%</b>\n' \
            f'<b>├  🚀 RAM : {memory}%</b>\n' \
            f'<b>└  🗄 DISK : {disk}%</b>'
    sendMessage(stats, context.bot, update)


def start(update, context):
    start_string = f'''
This bot is designed by @rahulkhatri137 to mirror your links to Google Drive!
Type /{BotCommands.HelpCommand} to get a list of available commands
'''
    sendMessage(start_string, context.bot, update)


def restart(update, context):
    restart_message = sendMessage("Restarting, Please wait!", context.bot, update)
    # Save restart message ID and chat ID in order to edit it after restarting
    with open(".restartmsg", "w") as f:
        f.truncate(0)
        f.write(f"{restart_message.chat.id}\n{restart_message.message_id}\n")
    fs_utils.clean_all()
    os.execl(executable, executable, "-m", "bot")


def ping(update, context):
    start_time = int(round(time.time() * 1000))
    reply = sendMessage("Starting Ping", context.bot, update)
    end_time = int(round(time.time() * 1000))
    editMessage(f'{end_time - start_time} ms', reply)


def log(update, context):
    sendLogFile(context.bot, update)


def bot_help(update, context):
    help_string = f'''
/{BotCommands.HelpCommand}: To get this message

/{BotCommands.MirrorCommand} [download_url][magnet_link]: Start mirroring the link to google drive

/{BotCommands.UnzipMirrorCommand} [download_url][magnet_link] : starts mirroring and if downloaded file is any archive , extracts it to google drive

/{BotCommands.ZipMirrorCommand} [download_url][magnet_link]: start mirroring and upload the archived (.zip) version of the download

/{BotCommands.LeechCommand} [download_url][magnet_link]: Start mirroring the link & upload to telegram

/{BotCommands.UnzipLeechCommand} [download_url][magnet_link] : starts mirroring and if downloaded file is any archive , extracts it and upload to telegram

/{BotCommands.ZipLeechCommand} [download_url][magnet_link]: start mirroring and upload the archived (.zip) version of the download

/{BotCommands.LeechSetCommand}: Leech Settings 

/{BotCommands.SetThumbCommand}: Reply photo to set it as Thumbnail

/{BotCommands.WatchCommand} [youtube-dl supported link]: Mirror through youtube-dl. Click /{BotCommands.WatchCommand} for more help.

/{BotCommands.ZipWatchCommand} [youtube-dl supported link]: Mirror through youtube-dl and zip before uploading

/{BotCommands.CancelMirror} : Reply to the message by which the download was initiated and that download will be cancelled

/{BotCommands.StatusCommand}: Shows a status of all the downloads

/{BotCommands.ListCommand} [search term]: Searches the search term in the Google drive, if found replies with the link

/{BotCommands.StatsCommand}: Show Stats of the machine the bot is hosted on

/{BotCommands.AuthorizeCommand}: Authorize a chat or a user to use the bot (Can only be invoked by owner of the bot)

/{BotCommands.UnAuthorizeCommand}: UnAuthorize a chat or a user to use the bot (Can only be invoked by owner of the bot)

/{BotCommands.LogCommand}: Get a log file of the bot. Handy for getting crash reports

/{BotCommands.SpeedCommand}: Check Internet Speed of the Host
/{BotCommands.UsageCommand}: To see Heroku Dyno Stats (Owner only)
'''
    sendMessage(help_string, context.bot, update)

botcmds = [
    (f"{BotCommands.HelpCommand}", "Get detailed help"),
    (f"{BotCommands.MirrorCommand}", "Start mirroring"),
    (f"{BotCommands.ZipMirrorCommand}", "Start mirroring and upload as .zip"),
    (f"{BotCommands.UnzipMirrorCommand}", "Extract files"),
    (f"{BotCommands.CloneCommand}", "Copy file/folder from GDrive"),
    (f"{BotCommands.deleteCommand}", "Delete file from GDrive [owner only]"),
    (f"{BotCommands.WatchCommand}", "Mirror Youtube-dl support link"),
    (f"{BotCommands.ZipWatchCommand}", "Mirror Youtube playlist link as .zip"),
    (f"{BotCommands.CancelMirror}", "Cancel a task"),
    (f"{BotCommands.CancelAllCommand}", "Cancel all tasks [owner only]"),
    (f"{BotCommands.StatusCommand}", "Get mirror status"),
    (f"{BotCommands.StatsCommand}", "Bot usage stats"),
    (f"{BotCommands.PingCommand}", "Ping the bot"),
    (f"{BotCommands.RestartCommand}", "Restart the bot [owner only]"),
    (f"{BotCommands.LogCommand}", "Get the bot log [owner only]"),
    (f"{BotCommands.LeechCommand}", "Start leeching"),
    (f"{BotCommands.LeechSetCommand}", "Leech Settings"),
    (f"{BotCommands.ZipLeechCommand}", "Start leeching and upload as .Zip"),
    (f"{BotCommands.UnzipLeechCommand}", "Extract the archive and leech to telegram"),
]

def main():
    fs_utils.start_cleanup()
    # Check if the bot is restarting
    if os.path.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
        bot.edit_message_text("Restarted successfully!", chat_id, msg_id)
        os.remove(".restartmsg")
    bot.set_my_commands(botcmds)
    start_handler = CommandHandler(BotCommands.StartCommand, start,
                                   filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    ping_handler = CommandHandler(BotCommands.PingCommand, ping,
                                  filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    restart_handler = CommandHandler(BotCommands.RestartCommand, restart,
                                     filters=CustomFilters.owner_filter, run_async=True)
    help_handler = CommandHandler(BotCommands.HelpCommand,
                                  bot_help, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    stats_handler = CommandHandler(BotCommands.StatsCommand,
                                   stats, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    log_handler = CommandHandler(BotCommands.LogCommand, log, filters=CustomFilters.owner_filter, run_async=True)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(ping_handler)
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(stats_handler)
    dispatcher.add_handler(log_handler)
    updater.start_polling()
    LOGGER.info("Bot Started!")
    signal.signal(signal.SIGINT, fs_utils.exit_clean_up)

app.start()
main()
idle()
