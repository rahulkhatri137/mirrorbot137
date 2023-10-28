import os
import pathlib
import random
import re
import string
import subprocess
import threading
import urllib
import time
import shutil
import requests
from telegram import InlineKeyboardMarkup, ParseMode
from telegram.ext import CommandHandler

from bot import (
    BLOCK_MEGA_LINKS,
    BUTTON_FIVE_NAME,
    BUTTON_FIVE_URL,
    BUTTON_FOUR_NAME,
    BUTTON_FOUR_URL,
    BUTTON_THREE_NAME,
    BUTTON_THREE_URL,
    DOWNLOAD_DIR,
    DOWNLOAD_STATUS_UPDATE_INTERVAL,
    INDEX_URL,
    LOGGER,
    MEGA_KEY,
    SHORTENER,
    SHORTENER_API,
    Interval,
    dispatcher,
    download_dict,
    download_dict_lock,
    TG_SPLIT_SIZE,
    VIEW_LINK,
    BOT_PM,
    LOGS_CHATS,

)
from bot.helper.ext_utils import bot_utils, fs_utils
from bot.helper.ext_utils.bot_utils import setInterval
from bot.helper.ext_utils.exceptions import (
    DirectDownloadLinkException,
    NotSupportedExtractionArchive,
)
from bot.helper.mirror_utils.download_utils.aria2_download import AriaDownloadHelper
from bot.helper.mirror_utils.download_utils.direct_link_generator import (
    direct_link_generator,
)
from bot.helper.mirror_utils.download_utils.mega_download import MegaDownloader
from bot.helper.mirror_utils.download_utils.telegram_downloader import (
    TelegramDownloadHelper,
)
from bot.helper.mirror_utils.status_utils.tg_upload_status import TgUploadStatus
from bot.helper.mirror_utils.status_utils.split_status import SplitStatus
from bot.helper.mirror_utils.status_utils import listeners
from bot.helper.mirror_utils.status_utils.extract_status import ExtractStatus
from bot.helper.mirror_utils.status_utils.gdownload_status import DownloadStatus
from bot.helper.mirror_utils.status_utils.upload_status import UploadStatus
from bot.helper.mirror_utils.status_utils.tar_status import TarStatus
from bot.helper.mirror_utils.upload_utils import gdriveTools, pyrogramEngine
from bot.helper.telegram_helper import button_build
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import *

ariaDlManager = AriaDownloadHelper()
ariaDlManager.start_listener()


class MirrorListener(listeners.MirrorListeners):
    def __init__(self, bot, update, isTar=False, isZip=False, extract=False, isLeech=False, pswd=None):
        super().__init__(bot, update)
        self.isZip = isZip
        self.isTar = isTar
        self.extract = extract
        self.pswd = pswd
        self.isLeech = isLeech

    def onDownloadStarted(self):
        pass

    def onDownloadProgress(self):
        # We are handling this on our own!
        pass

    def clean(self):
        try:
            Interval[0].cancel()
            del Interval[0]
            delete_all_messages()
        except IndexError:
            pass

    def onDownloadComplete(self):
        with download_dict_lock:
            LOGGER.info(f"Download completed: {download_dict[self.uid].name()}")
            download = download_dict[self.uid]
            name = download.name()
            gid = download.gid()
            size = download.size_raw()
            if name is None:  # when pyrogram's media.file_name is of NoneType
                name = os.listdir(f"{DOWNLOAD_DIR}{self.uid}")[0]
            m_path = f"{DOWNLOAD_DIR}{self.uid}/{name}"
        if self.isZip or self.isTar:
            try:
                with download_dict_lock:
                    download_dict[self.uid] = TarStatus(name, m_path, size)
                if self.isZip:
                    pswd = self.pswd
                    path = f"{m_path}.zip"
                    LOGGER.info(f'Zip: orig_path: {m_path}, zip_path: {path}')
                    if pswd is not None:
                        subprocess.run(["7z", "a", "-mx=0", f"-p{pswd}", path, m_path])
                    else:
                        subprocess.run(["7z", "a", "-mx=0", path, m_path])
                else:
                    path = fs_utils.tar(m_path)
            except FileNotFoundError:
                LOGGER.info('File to archive not found!')
                self.onUploadError('Internal error occurred!!')
                return
            try:
                shutil.rmtree(m_path)
            except:
                os.remove(m_path)
        elif self.extract:
            download.is_extracting = True
            try:
                path = fs_utils.get_base_name(m_path)
                LOGGER.info(f"Extracting : {name} ")
                with download_dict_lock:
                    download_dict[self.uid] = ExtractStatus(name, m_path, size)
                pswd = self.pswd
                archive_result = (
                    subprocess.run(["pextract", m_path, pswd])
                    if pswd is not None
                    else subprocess.run(["extract", m_path])
                )
                if archive_result.returncode == 0:
                    threading.Thread(target=os.remove, args=(m_path,)).start()
                    LOGGER.info(f"Deleting archive : {m_path}")
                else:
                    LOGGER.warning("Unable to extract archive! Uploading anyway")
                    path = f"{DOWNLOAD_DIR}{self.uid}/{name}"
                LOGGER.info(f"got path : {path}")

            except NotSupportedExtractionArchive:
                LOGGER.info("Not any valid archive, uploading file as it is.")
                path = f"{DOWNLOAD_DIR}{self.uid}/{name}"
        else:
            path = f"{DOWNLOAD_DIR}{self.uid}/{name}"
        up_name = pathlib.PurePath(path).name
        if up_name == "None":
            up_name = "".join(os.listdir(f"{DOWNLOAD_DIR}{self.uid}/"))
        up_path = f"{DOWNLOAD_DIR}{self.uid}/{up_name}"
        size = fs_utils.get_path_size(up_path)
        if self.isLeech:
            checked = False
            for dirpath, subdir, files in os.walk(f'{DOWNLOAD_DIR}{self.uid}', topdown=False):
                for file in files:
                    f_path = os.path.join(dirpath, file)
                    f_size = os.path.getsize(f_path)
                    if int(f_size) > TG_SPLIT_SIZE:
                        if not checked:
                            checked = True
                            with download_dict_lock:
                                download_dict[self.uid] = SplitStatus(up_name, up_path, size)
                            LOGGER.info(f"Splitting: {up_name}")
                        fs_utils.split(f_path, f_size, file, dirpath, TG_SPLIT_SIZE)
                        os.remove(f_path)
            LOGGER.info(f"Leech Name: {up_name}")
            tg = pyrogramEngine.TgUploader(up_name, self)
            tg_upload_status = TgUploadStatus(tg, size, gid, self)
            with download_dict_lock:
                download_dict[self.uid] = tg_upload_status
            update_all_messages()
            tg.upload()
        else:
            LOGGER.info(f"Upload Name: {up_name}")
            drive = gdriveTools.GoogleDriveHelper(up_name, self)
            upload_status = UploadStatus(drive, size, gid, self)
            with download_dict_lock:
                download_dict[self.uid] = upload_status
            update_all_messages()
            drive.upload(up_name)

    def onDownloadError(self, error):
        error = error.replace("<", " ")
        error = error.replace(">", " ")
        LOGGER.info(self.update.effective_chat.id)
        with download_dict_lock:
            try:
                download = download_dict[self.uid]
                del download_dict[self.uid]
                LOGGER.info(f"Deleting folder: {download.path()}")
                fs_utils.clean_download(download.path())
                LOGGER.info(str(download_dict))
            except Exception as e:
                LOGGER.error(str(e))
            count = len(download_dict)
        if self.message.from_user.username:
            uname = f"@{self.message.from_user.username}"
        else:
            uname = f'<a href="tg://user?id={self.message.from_user.id}">{self.message.from_user.first_name}</a>'
        msg = f"{uname} your download has been stopped due to: {error}"
        sendMessage(msg, self.bot, self.update)
        if count == 0:
            self.clean()
        else:
            update_all_messages()

    def onUploadStarted(self):
        pass

    def onUploadProgress(self):
        pass
    
    def onUploadComplete(self, link: str, size, files, folders, typ):
        if self.isLeech:
            if self.message.from_user.username:
                uname = f"@{self.message.from_user.username}"
            else:
                uname = f'<a href="tg://user?id={self.message.from_user.id}">{self.message.from_user.first_name}</a>'
            count = len(files)
            if self.message.chat.type == 'private':
                msg = f'<b>Name:</b> <code>{link}</code>\n'
                msg += f'<b>Total Files:</b> {count}'
                if typ != 0:
                    msg += f'\n<b>Corrupted Files: </b>{typ}'
                sendMessage(msg, self.bot, self.update)
            else:
                chat_id = str(self.message.chat.id)[4:]
                msg = f"<b>Name:</b> <a href='https://t.me/c/{chat_id}/{self.uid}'>{link}</a>\n"
                msg += f'<b>Total Files:</b> {count}\n'
                msg += f'cc: {uname}\n\n'
                if typ != 0:
                    msg += f'\n<b>Corrupted Files: </b>{typ}'
                fmsg = ''
                for index, item in enumerate(list(files), start=1):
                    msg_id = files[item]
                    link = f"https://t.me/c/{chat_id}/{msg_id}"
                    fmsg += f"{index}. <a href='{link}'>{item}</a>\n"
                    if len(fmsg) > 3900:
                        sendMessage(msg + fmsg, self.bot, self.update)
                        fmsg = ''
                if fmsg != '':
                    sendMessage(msg + fmsg, self.bot, self.update)
            if LOGS_CHATS:
                try:
                    for i in LOGS_CHATS:
                        msg1 = f"<b>Files Leeched</b>\n"
                        msg1 += f"<b>By:</b> {uname}\n"
                        msg1 += f'<b>Total Files:</b> {count}\n'
                        bot.sendMessage(chat_id=i, text=msg1, parse_mode=ParseMode.HTML)
                except Exception as e:
                    LOGGER.warning(e)
            if self.message.chat.type != 'private' and BOT_PM:
                try:
                    msg1 = f"<b>Files Leeched</b>\n"
                    msg1 += f"<b>By:</b> {uname}\n"
                    msg1 += f'<b>Total Files:</b> {count}\n'
                    bot.sendMessage(chat_id=self.self.message.from_user.id, text=msg1, parse_mode=ParseMode.HTML)
                except Exception as e:
                    LOGGER.warning(e)
            with download_dict_lock:
                try:
                    fs_utils.clean_download(download_dict[self.uid].path())
                except FileNotFoundError:
                    pass
                del download_dict[self.uid]
                count = len(download_dict)
            if count == 0:
                self.clean()
            else:
                update_all_messages()
            return
        with download_dict_lock:
            msg = f"<b>Filename : </b><code>{download_dict[self.uid].name()}</code>\n<b>Size : </b><code>{size}</code>"
            buttons = button_build.ButtonMaker()
            if SHORTENER is not None and SHORTENER_API is not None:
                surl = requests.get(
                    f"https://{SHORTENER}/api?api={SHORTENER_API}&url={link}&format=text"
                ).text
                buttons.buildbutton("☁️ Drive Link", surl)
            else:
                buttons.buildbutton("☁️ Drive Link", link)
            LOGGER.info(f'Done Uploading {download_dict[self.uid].name()}')
            if INDEX_URL is not None:
                url_path = requests.utils.quote(f'{download_dict[self.uid].name()}')
                share_url = f'{INDEX_URL}/{url_path}'
                if os.path.isdir(f'{DOWNLOAD_DIR}/{self.uid}/{download_dict[self.uid].name()}'):
                    share_url += '/'
                    if SHORTENER is not None and SHORTENER_API is not None:
                        siurl = requests.get(f'https://{SHORTENER}/api?api={SHORTENER_API}&url={share_url}&format=text').text
                        buttons.buildbutton("⚡ Index Link", siurl)
                    else:
                        buttons.buildbutton("⚡ Index Link", share_url)
                else:
                    share_urls = f'{INDEX_URL}/{url_path}?a=view'
                    if SHORTENER is not None and SHORTENER_API is not None:
                        siurl = requests.get(f'https://{SHORTENER}/api?api={SHORTENER_API}&url={share_url}&format=text').text
                        siurls = requests.get(f'https://{SHORTENER}/api?api={SHORTENER_API}&url={share_urls}&format=text').text
                        buttons.buildbutton("⚡ Index Link", siurl)
                        if VIEW_LINK:
                            buttons.buildbutton("🌐 View Link", siurls)
                    else:
                        buttons.buildbutton("⚡ Index Link", share_url)
                        if VIEW_LINK:
                            buttons.buildbutton("🌐 View Link", share_urls)
            if BUTTON_THREE_NAME is not None and BUTTON_THREE_URL is not None:
                buttons.buildbutton(f"{BUTTON_THREE_NAME}", f"{BUTTON_THREE_URL}")
            if BUTTON_FOUR_NAME is not None and BUTTON_FOUR_URL is not None:
                buttons.buildbutton(f"{BUTTON_FOUR_NAME}", f"{BUTTON_FOUR_URL}")
            if BUTTON_FIVE_NAME is not None and BUTTON_FIVE_URL is not None:
                buttons.buildbutton(f"{BUTTON_FIVE_NAME}", f"{BUTTON_FIVE_URL}")
            if self.message.from_user.username:
                uname = f"@{self.message.from_user.username}"
            else:
                uname = f'<a href="tg://user?id={self.message.from_user.id}">{self.message.from_user.first_name}</a>'
            if uname is not None:
                msg += f"\n\ncc : {uname}"
                if LOGS_CHATS:
                    try:
                        for i in LOGS_CHATS:
                            msg1 = f'<b>File Uploaded: </b> <code>{download_dict[self.uid].name()}</code>\n'
                            msg1 += f'<b>Size: </b>{size}\n'
                            msg1 += f'<b>By: </b>{uname}\n'
                            bot.sendMessage(chat_id=i, text=msg1, reply_markup=InlineKeyboardMarkup(buttons.build_menu(2)), parse_mode=ParseMode.HTML)
                    except Exception as e:
                        LOGGER.warning(e)
                if self.message.chat.type != 'private' and BOT_PM:
                    try:
                        msg1 = f'<b>File Uploaded: </b> <code>{download_dict[self.uid].name()}</code>\n'
                        msg1 += f'<b>Size: </b>{size}\n'
                        msg1 += f'<b>By: </b>{uname}\n'
                        bot.sendMessage(chat_id=self.self.message.from_user.id, text=msg1, reply_markup=InlineKeyboardMarkup(buttons.build_menu(2)), parse_mode=ParseMode.HTML)
                    except Exception as e:
                        LOGGER.warning(e)
            try:
                fs_utils.clean_download(download_dict[self.uid].path())
            except FileNotFoundError:
                pass
            del download_dict[self.uid]
            count = len(download_dict)
        sendMarkup(
            msg, self.bot, self.update, InlineKeyboardMarkup(buttons.build_menu(2))
        )
        if count == 0:
            self.clean()
        else:
            update_all_messages()

    def onUploadError(self, error):
        e_str = error.replace("<", "").replace(">", "")
        with download_dict_lock:
            try:
                fs_utils.clean_download(download_dict[self.uid].path())
            except FileNotFoundError:
                pass
            del download_dict[self.message.message_id]
            count = len(download_dict)
        if self.message.from_user.username:
            uname = f"@{self.message.from_user.username}"
        else:
            uname = f'<a href="tg://user?id={self.message.from_user.id}">{self.message.from_user.first_name}</a>'
        if uname is not None:
            men = f'{uname} '
        sendMessage(men + e_str, self.bot, self.update)
        if count == 0:
            self.clean()
        else:
            update_all_messages()


def _mirror(bot, update,isTar=False, isZip=False, extract=False, isLeech=False, pswd=None, multi=0):
    if not update.message.chat.type == 'private' and BOT_PM:
        try:
            msg1 = f"New Link Task"
            send = bot.sendMessage(
                chat_id=update.message.from_user.id,
                text=msg1,
            )
            send.delete()
        except Exception as e:
            LOGGER.warning(e)
            if update.message.from_user.username:
                uname = f"@{update.message.from_user.username}"
            else:
                uname = f'<a href="tg://user?id={update.message.from_user.id}">{update.message.from_user.first_name}</a>'
            buttons = button_build.ButtonMaker()
            buttons.buildbutton("Start Bot", f"https://t.me/{bot.get_me().username}?start=start")
            help_msg = f"{uname}, Start the bot in PM first."
            reply_message = sendMarkup(
                help_msg, bot, update, InlineKeyboardMarkup(buttons.build_menu(2))
            )
            threading.Thread(target=auto_delete_message, args=(bot, update, reply_message)).start()
            return reply_message
    mesg = update.message.text.split("\n")
    message_args = mesg[0].split(" ")
    name_args = mesg[0].split("|")
    try:
        link = message_args[1]
        print(link)
        if link.startswith("|") or link.startswith("pswd: "):
            link = ""
        elif link.isdigit():
            multi = int(link)
            raise IndexError
    except IndexError:
        link = ""
    try:
        name = name_args[1]
        name = name.strip()
        if name.startswith("pswd: "):
            name = ""
    except IndexError:
        name = ""
    try:
        ussr = urllib.parse.quote(mesg[1], safe="")
        pssw = urllib.parse.quote(mesg[2], safe="")
    except:
        ussr = ""
        pssw = ""
    if ussr != "" and pssw != "":
        link = link.split("://", maxsplit=1)
        link = f"{link[0]}://{ussr}:{pssw}@{link[1]}"
    pswd = re.search("(?<=pswd: )(.*)", update.message.text)
    if pswd is not None:
        pswd = pswd.groups()
        pswd = " ".join(pswd)
    LOGGER.info(link)
    link = link.strip()
    reply_to = update.message.reply_to_message
    if reply_to is not None:
        file = None
        media_array = [reply_to.document, reply_to.video, reply_to.audio]
        for i in media_array:
            if i is not None:
                file = i
                break

        if (
            not bot_utils.is_url(link)
            and not bot_utils.is_magnet(link)
            or len(link) == 0
        ) and file is not None:
            if file.mime_type != "application/x-bittorrent":
                listener = MirrorListener(bot, update, isTar, isZip, extract, isLeech=isLeech, pswd=pswd)
                tg_downloader = TelegramDownloadHelper(listener)
                ms = update.message
                tg_downloader.add_download(ms, f'{DOWNLOAD_DIR}{listener.uid}/', name)
                sendStatusMessage(update, bot)
                if len(Interval) == 0:
                    Interval.append(
                        setInterval(
                            DOWNLOAD_STATUS_UPDATE_INTERVAL, update_all_messages
                        )
                    )

                if multi > 1:
                    time.sleep(3)
                    update.message.message_id = update.message.reply_to_message.message_id + 1 
                    update.message = sendMessage(message_args[0], bot, update)
                    multi -= 1
                    time.sleep(3)
                    threading.Thread(target=_mirror, args=(bot, update, isTar, isZip, extract, isLeech, pswd, multi)).start()
                return
            else:
                link = file.get_file().file_path
        elif (
              not bot_utils.is_url(link)
              and not bot_utils.is_magnet(link)
              or len(link) == 0
        ) and file is None:
            reply_text = reply_to.text
            reply_text = re.split('\n ', reply_text)[0]
            if bot_utils.is_url(reply_text) or bot_utils.is_magnet(reply_text):
                link = reply_text

            if not bot_utils.is_url(link) and not bot_utils.is_magnet(link) and not os.path.exists(link) :
                resp = requests.get(link)
                if resp.status_code == 200:
                    file_name = str(time.time()).replace(".", "") + ".torrent"
                    open(file_name, "wb").write(resp.content)
                    link = f"{file_name}"
                else:
                    sendMessage("ERROR: link got HTTP response:" + resp.status_code, bot, update)
                    return
    elif not bot_utils.is_url(link) and not bot_utils.is_magnet(link):
        sendMessage("No download source provided", bot, update)
        return
    try:
        gdtot_link = bot_utils.is_gdtot_link(link)
        link = direct_link_generator(link)
    except DirectDownloadLinkException as e:
        LOGGER.info(e)
        if "ERROR:" in str(e):
                sendMessage(f"{e}", bot, update)
                return
        if "Youtube" in str(e):
                sendMessage(f"{e}", bot, update)
                return    
    listener = MirrorListener(bot, update, isTar, isZip, extract, isLeech, pswd)
    if bot_utils.is_gdrive_link(link):
        if not isZip and not isTar and not extract and not isLeech:
            sendMessage(
                f"Use /{BotCommands.CloneCommand} To Copy File/Folder", bot, update
            )
            return
        res, size, name, files = gdriveTools.GoogleDriveHelper().clonehelper(link)
        if res != "":
            sendMessage(res, bot, update)
            return
        try:
            name = name_args[1]
            name = name.strip()
        except IndexError:
            name = name
        LOGGER.info(f"Download Name : {name}")
        drive = gdriveTools.GoogleDriveHelper(name, listener)
        gid = "".join(
            random.SystemRandom().choices(string.ascii_letters + string.digits, k=12)
        )
        download_status = DownloadStatus(drive, size, listener, gid)
        with download_dict_lock:
            download_dict[listener.uid] = download_status
        if len(Interval) == 0:
            Interval.append(
                setInterval(DOWNLOAD_STATUS_UPDATE_INTERVAL, update_all_messages)
            )
        sendStatusMessage(update, bot)
        drive.download(link)
        if gdtot_link:
            drive.deletefile(link)

    elif bot_utils.is_mega_link(link) and MEGA_KEY is not None and not BLOCK_MEGA_LINKS:
        mega_dl = MegaDownloader(listener)
        mega_dl.add_download(link, f"{DOWNLOAD_DIR}{listener.uid}/")
        sendStatusMessage(update, bot)
    elif bot_utils.is_mega_link(link) and BLOCK_MEGA_LINKS:
        sendMessage(
            "Mega links are blocked. Dont try to mirror mega links.", bot, update
        )
    else:
        ariaDlManager.add_download(
            link, f"{DOWNLOAD_DIR}{listener.uid}/", listener, name
        )
        sendStatusMessage(update, bot)
    if len(Interval) == 0:
        Interval.append(
            setInterval(DOWNLOAD_STATUS_UPDATE_INTERVAL, update_all_messages)
        )

    if multi > 1:
        time.sleep(3)
        update.message.message_id = update.message.reply_to_message.message_id + 1 
        update.message = sendMessage(message_args[0], bot, update)
        multi -= 1
        time.sleep(3)
        threading.Thread(target=_mirror, args=(bot, update, isTar, isZip, extract, isLeech, pswd, multi)).start()
    return

def mirror(update, context):
    _mirror(context.bot, update)

def tar_mirror(update, context):
    _mirror(context.bot, update, isTar=True)

def zip_mirror(update, context):
    _mirror(context.bot, update, True, isZip=True)    

def unzip_mirror(update, context):
    _mirror(context.bot, update, extract=True)

def leech(update, context):
    _mirror(context.bot, update, isLeech=True)

def tar_leech(update, context):
    _mirror(context.bot, update, isTar=True, isLeech=True)

def unzip_leech(update, context):
    _mirror(context.bot, update, extract=True, isLeech=True)

def zip_leech(update, context):
    _mirror(context.bot, update, True, True, isLeech=True)


mirror_handler = CommandHandler(
    BotCommands.MirrorCommand,
    mirror,
    filters=CustomFilters.authorized,
    run_async=True,
)
zip_mirror_handler = CommandHandler(
    BotCommands.ZipMirrorCommand,
    zip_mirror,
    filters=CustomFilters.authorized,
    run_async=True,
)
tar_mirror_handler = CommandHandler(
    BotCommands.TarMirrorCommand,
    tar_mirror,
    filters=CustomFilters.authorized,
    run_async=True,
)
unzip_mirror_handler = CommandHandler(
    BotCommands.UnzipMirrorCommand,
    unzip_mirror,
    filters=CustomFilters.authorized,
    run_async=True,
)
leech_handler = CommandHandler(BotCommands.LeechCommand, leech,
                                filters=CustomFilters.authorized, run_async=True)
tar_leech_handler = CommandHandler(BotCommands.TarLeechCommand, tar_leech,
                                filters=CustomFilters.authorized, run_async=True)
unzip_leech_handler = CommandHandler(BotCommands.UnzipLeechCommand, unzip_leech,
                                filters=CustomFilters.authorized, run_async=True)
zip_leech_handler = CommandHandler(BotCommands.ZipLeechCommand, zip_leech,
                                filters=CustomFilters.authorized, run_async=True)
dispatcher.add_handler(mirror_handler)
dispatcher.add_handler(zip_mirror_handler)
dispatcher.add_handler(unzip_mirror_handler)
dispatcher.add_handler(leech_handler)
dispatcher.add_handler(tar_leech_handler)
dispatcher.add_handler(unzip_leech_handler)
dispatcher.add_handler(zip_leech_handler)
dispatcher.add_handler(tar_mirror_handler)
