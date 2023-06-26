from telegram.ext import MessageFilter
from telegram import Message
from bot import AUTHORIZED_CHATS, SUDO_USERS, OWNER_ID, download_dict, download_dict_lock

class CustomFilters:
    class _OwnerFilter(MessageFilter):
        def filter(self, message):
            return bool(message.from_user.id == OWNER_ID)

    owner = _OwnerFilter()

    class _AuthorizedFilter(MessageFilter):
        def filter(self, message):
            id = message.from_user.id
            return bool(message.chat.id in AUTHORIZED_CHATS or id in AUTHORIZED_CHATS or id in SUDO_USERS or id == OWNER_ID)

    authorized = _AuthorizedFilter()

    class _SudoUser(MessageFilter):
        def filter(self, message):
            return bool(message.from_user.id in SUDO_USERS or message.from_user.id == OWNER_ID)

    sudo = _SudoUser()

    class _MirrorOwner(MessageFilter):
        def filter(self, message: Message):
            user_id = message.from_user.id
            return bool(user_id in SUDO_USERS or user_id == OWNER_ID)
            args = str(message.text).split(' ')
            if len(args) > 1:
                # Cancelling by gid
                with download_dict_lock:
                    for message_id, status in download_dict.items():
                        if status.gid() == args[1] and status.message.from_user.id == user_id:
                            return True
                    else:
                        return False
            if not message.reply_to_message and len(args) == 1:
                return True
            # Cancelling by replying to original mirror message
            reply_user = message.reply_to_message.from_user.id
            return bool(reply_user == user_id)
    mirror_owner = _MirrorOwner()
