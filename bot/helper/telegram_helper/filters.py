from telegram.ext import MessageFilter
from telegram import Message
from bot import AUTHORIZED_CHATS, SUDO_USERS, OWNER_ID, download_dict, download_dict_lock

class CustomFilters:
    class _OwnerFilter(MessageFilter):
        def filter(self, message):
            return message.from_user.id == OWNER_ID

    owner = _OwnerFilter()

    class _AuthorizedFilter(MessageFilter):
        def filter(self, message):
            id = message.from_user.id
            return (
                message.chat.id in AUTHORIZED_CHATS
                or id in AUTHORIZED_CHATS
                or id in SUDO_USERS
                or id == OWNER_ID
            )

    authorized = _AuthorizedFilter()

    class _SudoUser(MessageFilter):
        def filter(self, message):
            return message.from_user.id in SUDO_USERS or message.from_user.id == OWNER_ID

    sudo = _SudoUser()

    class _MirrorOwner(MessageFilter):
        def filter(self, message: Message):
            user_id = message.from_user.id
            return user_id in SUDO_USERS or user_id == OWNER_ID
    mirror_owner = _MirrorOwner()
