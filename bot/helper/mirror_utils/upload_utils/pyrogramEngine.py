import os
import logging
import time

from pyrogram.errors import FloodWait, RPCError
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

from bot import app, DOWNLOAD_DIR, AS_DOCUMENT, AS_DOC_USERS, AS_MEDIA_USERS, BOT_PM, LOGS_CHATS, CUSTOM_FILENAME
from bot.helper.ext_utils.fs_utils import take_ss 

LOGGER = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

VIDEO_SUFFIXES = ("MKV", "MP4", "MOV", "WMV", "3GP", "MPG", "WEBM", "AVI", "FLV", "M4V")
AUDIO_SUFFIXES = ("MP3", "M4A", "M4B", "FLAC", "WAV", "AIF", "OGG", "AAC", "DTS", "MID", "AMR", "MKA")
IMAGE_SUFFIXES = ("JPG", "JPX", "PNG", "GIF", "WEBP", "CR2", "TIF", "BMP", "JXR", "PSD", "ICO", "HEIC")


class TgUploader:

    def __init__(self, name=None, listener=None):
        self.__listener = listener
        self.name = name
        self.__app = app
        self.total_bytes = 0
        self.uploaded_bytes = 0
        self.last_uploaded = 0
        self.start_time = time.time()
        self.is_cancelled = False
        self.chat_id = listener.message.chat.id
        self.message_id = listener.uid
        self.user_id = listener.message.from_user.id
        self.as_doc = AS_DOCUMENT
        self.thumb = f"Thumbnails/{self.user_id}.jpg"
        self.sent_msg = self.__app.get_messages(self.chat_id, self.message_id)
        self.corrupted = 0
        self.isPrivate = listener.message.chat.type in ['private', 'group']

    def upload(self):
        msgs_dict = {}
        path = f"{DOWNLOAD_DIR}{self.message_id}"
        self.user_settings()
        for dirpath, subdir, files in sorted(os.walk(path)):
            for file in sorted(files):
                if self.is_cancelled:
                    return
                up_path = os.path.join(dirpath, file)
                fsize = os.path.getsize(up_path)
                if fsize == 0:
                    LOGGER.error(f"{up_path} size is zero, telegram don't upload zero size files")
                    self.corrupted += 1
                    continue
                self.upload_file(up_path, file, dirpath)
                if self.is_cancelled:
                    return
                msgs_dict[file] = self.sent_msg.id
                self.last_uploaded = 0
        if len(msgs_dict) <= self.corrupted:
            return self.__listener.onUploadError('Files Corrupted. Check logs')
        LOGGER.info(f"Leech Done: {self.name}")
        self.__listener.onUploadComplete(self.name, None, msgs_dict, None, self.corrupted)

    def upload_file(self, up_path, file, dirpath):
        if CUSTOM_FILENAME is not None:
            cap_mono = f"{CUSTOM_FILENAME} <i>{file}</i>"
            file = f"{CUSTOM_FILENAME} {file}"
            new_path = os.path.join(dirpath, file)
            os.rename(up_path, new_path)
            up_path = new_path
        else:
            cap_mono = f"<i>{file}</i>"

        notMedia = False
        thumb = self.thumb
        try:
            if not self.as_doc:
                duration = 0
                if file.upper().endswith(VIDEO_SUFFIXES):
                    metadata = extractMetadata(createParser(up_path))
                    if metadata.has("duration"):
                        duration = metadata.get("duration").seconds
                    if thumb is None:
                        thumb = take_ss(up_path)
                    if self.is_cancelled:
                        return
                    if not file.upper().endswith(("MKV", "MP4")):
                        file = f'{os.path.splitext(file)[0]}.mp4'
                        new_path = os.path.join(dirpath, file)
                        os.rename(up_path, new_path)
                        up_path = new_path
                    self.sent_msg = self.sent_msg.reply_video(video=up_path,
                                                              quote=True,
                                                              caption=cap_mono,
                                                              duration=duration,
                                                              width=480,
                                                              height=320,
                                                              thumb=thumb,
                                                              supports_streaming=True,
                                                              disable_notification=True,
                                                              progress=self.upload_progress)
                    if not self.isPrivate and BOT_PM:
                        try:
                            app.send_video(self.user_id, video=self.sent_msg.video.file_id, caption=cap_mono)
                        except Exception as err:
                            LOGGER.error(f"Failed To Send Video in PM:\n{err}")
                    try:
                        for i in LOGS_CHATS:
                            app.send_video(i, video=self.sent_msg.video.file_id, caption=cap_mono)
                    except Exception as err:
                        LOGGER.error(f"Failed to forward file to log channel:\n{err}")
                    if self.thumb is None and thumb is not None and os.path.lexists(thumb):
                        os.remove(thumb)
                elif file.upper().endswith(AUDIO_SUFFIXES):
                    metadata = extractMetadata(createParser(up_path))
                    if metadata.has("duration"):
                        duration = metadata.get('duration').seconds
                    title = metadata.get("title") if metadata.has("title") else None
                    artist = metadata.get("artist") if metadata.has("artist") else None
                    self.sent_msg = self.sent_msg.reply_audio(audio=up_path,
                                                              quote=True,
                                                              caption=cap_mono,
                                                              duration=duration,
                                                              performer=artist,
                                                              title=title,
                                                              thumb=thumb,
                                                              disable_notification=True,
                                                              progress=self.upload_progress)
                    if not self.isPrivate and BOT_PM:
                        try:
                            app.send_audio(self.user_id, audio=self.sent_msg.audio.file_id, caption=cap_mono)
                        except Exception as err:
                            LOGGER.error(f"Failed To Send Audio in PM:\n{err}")
                    try:
                        for i in LOGS_CHATS:
                            app.send_audio(i, audio=self.sent_msg.audio.file_id, caption=cap_mono)
                    except Exception as err:
                        LOGGER.error(f"Failed to forward file to log channel:\n{err}")
                elif file.upper().endswith(IMAGE_SUFFIXES):
                    self.sent_msg = self.sent_msg.reply_photo(photo=up_path,
                                                              quote=True,
                                                              caption=cap_mono,
                                                              disable_notification=True,
                                                              progress=self.upload_progress)
                    if not self.isPrivate and BOT_PM:
                        try:
                            app.send_photo(self.user_id, photo=self.sent_msg.photo.file_id, caption=cap_mono)
                        except Exception as err:
                            LOGGER.error(f"Failed To Send Photo in PM:\n{err}")
                    try:
                        for i in LOGS_CHATS:
                            app.send_photo(i, photo=self.sent_msg.photo.file_id, caption=cap_mono)
                    except Exception as err:
                        LOGGER.error(f"Failed to forward file to log channel:\n{err}")
                else:
                    notMedia = True
            if self.as_doc or notMedia:
                if file.upper().endswith(VIDEO_SUFFIXES) and thumb is None:
                    thumb = take_ss(up_path)
                if self.is_cancelled:
                    return
                self.sent_msg = self.sent_msg.reply_document(document=up_path,
                                                             quote=True,
                                                             thumb=thumb,
                                                             caption=cap_mono,
                                                             disable_notification=True,
                                                             progress=self.upload_progress)
                if not self.isPrivate and BOT_PM:
                    try:
                        app.send_document(self.user_id, document=self.sent_msg.document.file_id, caption=cap_mono)
                    except Exception as err:
                        LOGGER.error(f"Failed To Send file in PM:\n{err}")
                try:
                    for i in LOGS_CHATS:
                        app.send_document(i, document=self.sent_msg.document.file_id, caption=cap_mono)
                except Exception as err:
                    LOGGER.error(f"Failed to forward file to log channel:\n{err}")
                if self.thumb is None and thumb is not None and os.path.lexists(thumb):
                    os.remove(thumb)
            if not self.is_cancelled:
                os.remove(up_path)
        except FloodWait as f:
            LOGGER.info(f)
            time.sleep(f.x)
        except RPCError as e:
            LOGGER.error(f"RPCError: {e} File: {up_path}")
            self.corrupted += 1
        except Exception as err:
            LOGGER.error(f"{err} File: {up_path}")
            self.corrupted += 1
    def upload_progress(self, current, total):
        if self.is_cancelled:
            self.__app.stop_transmission()
            return
        chunk_size = current - self.last_uploaded
        self.last_uploaded = current
        self.uploaded_bytes += chunk_size

    def user_settings(self):
        if self.user_id in AS_DOC_USERS:
            self.as_doc = True
        elif self.user_id in AS_MEDIA_USERS:
            self.as_doc = False
        if not os.path.lexists(self.thumb):
            self.thumb = None

    def speed(self):
        try:
            return self.uploaded_bytes / (time.time() - self.start_time)
        except ZeroDivisionError:
            return 0

    def cancel_download(self):
        self.is_cancelled = True
        LOGGER.info(f"Cancelling Upload: {self.name}")
        self.__listener.onUploadError('your upload has been stopped!')
