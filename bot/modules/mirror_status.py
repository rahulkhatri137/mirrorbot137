import threading

from telegram.ext import CommandHandler

from bot import dispatcher, status_reply_dict, status_reply_dict_lock
from bot.helper.ext_utils.bot_utils import get_readable_message
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import (
    auto_delete_message,
    bot,
    deleteMessage,
    sendMessage,
    sendStatusMessage,
)


def mirror_status(update, context):
    message = get_readable_message()
    if len(message) == 0:
        message = "No active downloads"
        reply_message = sendMessage(message, context.bot, update)
        threading.Thread(
            target=auto_delete_message, args=(bot, update.message, reply_message)
        ).start()
        return
    index = update.effective_chat.id
    with status_reply_dict_lock:
        if index in status_reply_dict.keys():
            deleteMessage(bot, status_reply_dict[index])
            del status_reply_dict[index]
    sendStatusMessage(update, context.bot)
    deleteMessage(context.bot, update.message)


mirror_status_handler = CommandHandler(
    BotCommands.StatusCommand,
    mirror_status,
    filters=CustomFilters.authorized,
    run_async=True,
)
dispatcher.add_handler(mirror_status_handler)
