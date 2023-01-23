import faulthandler
import logging
import os
import random
import socket
import string
import threading
import time
import requests
import aria2p
import telegram.ext as tg
from dotenv import load_dotenv
from pyrogram import Client

import psycopg2
from psycopg2 import Error

faulthandler.enable()
import subprocess

from megasdkrestclient import MegaSdkRestClient
from megasdkrestclient import errors as mega_err

socket.setdefaulttimeout(600)

botStartTime = time.time()
if os.path.exists("log.txt"):
    with open("log.txt", "r+") as f:
        f.truncate(0)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    level=logging.INFO,
)
#Config And Heroku Support
CONFIG_FILE_URL = os.environ.get('CONFIG_FILE_URL')
if CONFIG_FILE_URL:
    if len(CONFIG_FILE_URL) == 0:
            CONFIG_FILE_URL = None
    if CONFIG_FILE_URL is not None:
        logging.error("Downloading config.env From Provided URL")
        if os.path.isfile("config.env"):
            logging.error("Updating config.env")
            os.remove("config.env")
        res = requests.get(CONFIG_FILE_URL)
        if res.status_code == 200:
            with open('config.env', 'wb+') as f:
                f.write(res.content)
                f.close()
        else:
            logging.error(f"Failed to download config.env {res.status_code}")
load_dotenv("config.env")

Interval = []
def mktable():
    try:
        conn = psycopg2.connect(DB_URI)
        cur = conn.cursor()
        sql = "CREATE TABLE users (uid bigint, sudo boolean DEFAULT FALSE);"
        cur.execute(sql)
        conn.commit()
        logging.info("Table Created!")
    except Error as e:
        logging.error(e)
        exit(1)

def getConfig(name: str):
    return os.environ[name]


LOGGER = logging.getLogger(__name__)

try:
    if bool(getConfig("_____REMOVE_THIS_LINE_____")):
        logging.error("The README.md file there to be read! Exiting now!")
        exit()
except KeyError:
    pass

subprocess.run(["./aria.sh"], shell=True)

#RECURSIVE SEARCH
DRIVE_NAME = []
DRIVE_ID = []
UNI_INDEX_URL = []

if os.path.exists('drive_folder'):
    with open('drive_folder', 'r+') as f:
        lines = f.readlines()
        for line in lines:
            temp = line.strip().split()
            DRIVE_NAME.append(temp[0].replace("_", " "))
            DRIVE_ID.append(temp[1])
            try:
                UNI_INDEX_URL.append(temp[2])
            except IndexError as e:
                UNI_INDEX_URL.append(None)
try:
    RECURSIVE_SEARCH = getConfig("RECURSIVE_SEARCH")
    if RECURSIVE_SEARCH.lower() == "true":
        RECURSIVE_SEARCH = True
    else:
        RECURSIVE_SEARCH = False
except KeyError:
    RECURSIVE_SEARCH = False
                

if RECURSIVE_SEARCH:
    if DRIVE_ID:
        pass
    else :
        LOGGER.error("Fill Drive_Folder File For Multi Drive Search!")
        exit(1)    
        

aria2 = aria2p.API(
    aria2p.Client(
        host="http://localhost",
        port=6800,
        secret="",
    )
)

def aria2c_init():
    try:
        if not os.path.isfile(".restartmsg"):
            logging.info("Initializing Aria2c")
            link = "https://releases.ubuntu.com/21.10/ubuntu-21.10-desktop-amd64.iso.torrent"
            path = "/usr/src/app/"
            aria2.add_uris([link], {'dir': path})
            time.sleep(3)
            downloads = aria2.get_downloads()
            time.sleep(30)
            for download in downloads:
                aria2.remove([download], force=True, files=True)
    except Exception as e:
        logging.error(f"Aria2c initializing error: {e}")
        pass

threading.Thread(target=aria2c_init).start()
time.sleep(0.5)

DOWNLOAD_DIR = None
BOT_TOKEN = None

download_dict_lock = threading.Lock()
status_reply_dict_lock = threading.Lock()
# Key: update.effective_chat.id
# Value: telegram.Message
status_reply_dict = {}
# Key: update.message.message_id
# Value: An object of Status
download_dict = {}
AS_DOC_USERS = set()
AS_MEDIA_USERS = set()
# Stores list of users and chats the bot is authorized to use in
AUTHORIZED_CHATS = set()
SUDO_USERS = set()
LOGS_CHATS = set()
if os.path.exists('sudo_users.txt'):
    with open('sudo_users.txt', 'r+') as f:
        lines = f.readlines()
        for line in lines:
            SUDO_USERS.add(int(line.split()[0]))
try:
    schats = getConfig('SUDO_USERS')
    schats = schats.split(" ")
    for chats in schats:
        SUDO_USERS.add(int(chats))
except:
    pass
if os.path.exists("authorized_chats.txt"):
    with open("authorized_chats.txt", "r+") as f:
        lines = f.readlines()
        for line in lines:
            #    LOGGER.info(line.split())
            AUTHORIZED_CHATS.add(int(line.split()[0]))
try:
    achats = getConfig("AUTHORIZED_CHATS")
    achats = achats.split(" ")
    for chats in achats:
        AUTHORIZED_CHATS.add(int(chats))
except:
    pass

if os.path.exists("logs_chat.txt"):
    with open("logs_chat.txt", "r+") as f:
        lines = f.readlines()
        for line in lines:
            #    LOGGER.info(line.split())
            LOGS_CHATS.add(int(line.split()[0]))
try:
    achats = getConfig("LOGS_CHATS")
    achats = achats.split(" ")
    for chats in achats:
        LOGS_CHATS.add(int(chats))
except:
    logging.warning('Logs Chat Details not provided!')
    pass
try:	
    BOT_PM = getConfig('BOT_PM')	
    BOT_PM = BOT_PM.lower() == 'true'	
except KeyError:	
    BOT_PM = False

try:
    CRYPT = getConfig('CRYPT')
    if len(CRYPT) == 0:
        raise KeyError
except KeyError:
    CRYPT = None

try:
    CUSTOM_FILENAME = getConfig('CUSTOM_FILENAME')
    if len(CUSTOM_FILENAME) == 0:
        raise KeyError
except:
    CUSTOM_FILENAME = None

try:
    BOT_TOKEN = getConfig("BOT_TOKEN")
    parent_id = getConfig("GDRIVE_FOLDER_ID")
    DOWNLOAD_DIR = getConfig("DOWNLOAD_DIR")
    if not DOWNLOAD_DIR.endswith("/"):
        DOWNLOAD_DIR = DOWNLOAD_DIR + "/"
    DOWNLOAD_STATUS_UPDATE_INTERVAL = int(getConfig("DOWNLOAD_STATUS_UPDATE_INTERVAL"))
    OWNER_ID = int(getConfig("OWNER_ID"))
    AUTO_DELETE_MESSAGE_DURATION = int(getConfig("AUTO_DELETE_MESSAGE_DURATION"))
    TELEGRAM_API = getConfig("TELEGRAM_API")
    TELEGRAM_HASH = getConfig("TELEGRAM_HASH")
except KeyError as missing:
    LOGGER.error("One or more env variables missing! Exiting now ")
    LOGGER.error(str(missing) + " Env Variable Is Missing.")
    exit(1)

try:
    DB_URI = getConfig('DATABASE_URL')
    if len(DB_URI) == 0:
        raise KeyError
except KeyError:
    DB_URI = None
if DB_URI is not None:
    try:
        conn = psycopg2.connect(DB_URI)
        cur = conn.cursor()
        sql = "SELECT * from users;"
        cur.execute(sql)
        rows = cur.fetchall()  #returns a list ==> (uid, sudo)
        for row in rows:
            AUTHORIZED_CHATS.add(row[0])
            if row[1]:
                SUDO_USERS.add(row[0])
    except Error as e:
        if 'relation "users" does not exist' in str(e):
            mktable()
        else:
            LOGGER.error(e)
            exit(1)
    finally:
        cur.close()
        conn.close()    

LOGGER.info("Generating USER_SESSION_STRING")
try:
    PREMIUM_USER = False
    SESSION_STRING = getConfig('SESSION_STRING')
    if len(SESSION_STRING) == 0:
        raise KeyError
    app = Client(
    ":memory:", api_id=int(TELEGRAM_API), api_hash=TELEGRAM_HASH, session_string=SESSION_STRING
)
    with app:
        PREMIUM_USER = app.get_me().is_premium
except:
    app = Client(
    ":memory:", api_id=int(TELEGRAM_API), api_hash=TELEGRAM_HASH, bot_token=BOT_TOKEN
)

try:
    MEGA_KEY = getConfig("MEGA_KEY")

except KeyError:
    MEGA_KEY = None
    LOGGER.info("MEGA API KEY NOT AVAILABLE")
if MEGA_KEY is not None:
    # Start megasdkrest binary
    subprocess.Popen(["megasdkrest", "--apikey", MEGA_KEY])
    time.sleep(3)  # Wait for the mega server to start listening
    mega_client = MegaSdkRestClient("http://localhost:6090")
    try:
        MEGA_USERNAME = getConfig("MEGA_USERNAME")
        MEGA_PASSWORD = getConfig("MEGA_PASSWORD")
        if len(MEGA_USERNAME) > 0 and len(MEGA_PASSWORD) > 0:
            try:
                mega_client.login(MEGA_USERNAME, MEGA_PASSWORD)
            except mega_err.MegaSdkRestClientException as e:
                logging.error(e.message["message"])
                exit(0)
        else:
            LOGGER.info(
                "Mega API KEY provided but credentials not provided. Starting mega in anonymous mode!"
            )
            MEGA_USERNAME = None
            MEGA_PASSWORD = None
    except KeyError:
        LOGGER.info(
            "Mega API KEY provided but credentials not provided. Starting mega in anonymous mode!"
        )
        MEGA_USERNAME = None
        MEGA_PASSWORD = None
else:
    MEGA_USERNAME = None
    MEGA_PASSWORD = None
try:
    INDEX_URL = getConfig("INDEX_URL")
    if len(INDEX_URL) == 0:
        INDEX_URL = None
except KeyError:
    INDEX_URL = None
try:
    BUTTON_THREE_NAME = getConfig("BUTTON_THREE_NAME")
    BUTTON_THREE_URL = getConfig("BUTTON_THREE_URL")
    if len(BUTTON_THREE_NAME) == 0 or len(BUTTON_THREE_URL) == 0:
        raise KeyError
except KeyError:
    BUTTON_THREE_NAME = None
    BUTTON_THREE_URL = None
try:
    BUTTON_FOUR_NAME = getConfig("BUTTON_FOUR_NAME")
    BUTTON_FOUR_URL = getConfig("BUTTON_FOUR_URL")
    if len(BUTTON_FOUR_NAME) == 0 or len(BUTTON_FOUR_URL) == 0:
        raise KeyError
except KeyError:
    BUTTON_FOUR_NAME = None
    BUTTON_FOUR_URL = None
try:
    BUTTON_FIVE_NAME = getConfig("BUTTON_FIVE_NAME")
    BUTTON_FIVE_URL = getConfig("BUTTON_FIVE_URL")
    if len(BUTTON_FIVE_NAME) == 0 or len(BUTTON_FIVE_URL) == 0:
        raise KeyError
except KeyError:
    BUTTON_FIVE_NAME = None
    BUTTON_FIVE_URL = None
try:
    IS_TEAM_DRIVE = getConfig("IS_TEAM_DRIVE")
    IS_TEAM_DRIVE = IS_TEAM_DRIVE.lower() == "true"
except KeyError:
    IS_TEAM_DRIVE = False

try:
    USE_SERVICE_ACCOUNTS = getConfig("USE_SERVICE_ACCOUNTS")
    if USE_SERVICE_ACCOUNTS.lower() == "true":
        USE_SERVICE_ACCOUNTS = True
    else:
        USE_SERVICE_ACCOUNTS = False
except KeyError:
    USE_SERVICE_ACCOUNTS = False

try:
    BLOCK_MEGA_LINKS = getConfig("BLOCK_MEGA_LINKS")
    BLOCK_MEGA_LINKS = BLOCK_MEGA_LINKS.lower() == "true"
except KeyError:
    BLOCK_MEGA_LINKS = False

try:
    SHORTENER = getConfig("SHORTENER")
    SHORTENER_API = getConfig("SHORTENER_API")
    if len(SHORTENER) == 0 or len(SHORTENER_API) == 0:
        raise KeyError
except KeyError:
    SHORTENER = None
    SHORTENER_API = None

IGNORE_PENDING_REQUESTS = False
try:
    if getConfig("IGNORE_PENDING_REQUESTS").lower() == "true":
        IGNORE_PENDING_REQUESTS = True
except KeyError:
    pass

try:
    TG_SPLIT_SIZE = getConfig('TG_SPLIT_SIZE')
    if len(TG_SPLIT_SIZE) == 0 or (not PREMIUM_USER and TG_SPLIT_SIZE > 2097152000) or TG_SPLIT_SIZE > 4194304000:
        raise KeyError
    else:
        TG_SPLIT_SIZE = int(TG_SPLIT_SIZE)
except:
    if PREMIUM_USER:
        TG_SPLIT_SIZE = 4194304000
    else:
        TG_SPLIT_SIZE = 2097152000
try:
    AS_DOCUMENT = getConfig('AS_DOCUMENT')
    AS_DOCUMENT = AS_DOCUMENT.lower() == 'true'
except KeyError:
    AS_DOCUMENT = False

#VIEW_LINK
try:
    VIEW_LINK = getConfig('VIEW_LINK')
    if VIEW_LINK.lower() == 'true':
        VIEW_LINK = True
    else:
        VIEW_LINK = False
except KeyError:
    VIEW_LINK = False
#CLONE
try:
    CLONE_LIMIT = getConfig('CLONE_LIMIT')
    if len(CLONE_LIMIT) == 0:
        CLONE_LIMIT = None
except KeyError:
    CLONE_LIMIT = None

try:
    STOP_DUPLICATE_CLONE = getConfig('STOP_DUPLICATE_CLONE')
    if STOP_DUPLICATE_CLONE.lower() == 'true':
        STOP_DUPLICATE_CLONE = True
    else:
        STOP_DUPLICATE_CLONE = False
except KeyError:
    STOP_DUPLICATE_CLONE = False
#HEROKUSUPPORT    
try:
    TOKEN_PICKLE_URL = getConfig('TOKEN_PICKLE_URL')
    if len(TOKEN_PICKLE_URL) == 0:
        TOKEN_PICKLE_URL = None
    else:
        res = requests.get(TOKEN_PICKLE_URL)
        if res.status_code == 200:
            with open('token.pickle', 'wb+') as f:
                f.write(res.content)
                f.close()
        else:
            logging.error(f"Failed to download token.pickle {res.status_code}")
            raise KeyError
except KeyError:
    pass

try:
    ACCOUNTS_ZIP_URL = getConfig('ACCOUNTS_ZIP_URL')
    if len(ACCOUNTS_ZIP_URL) == 0:
        ACCOUNTS_ZIP_URL = None
    else:
        res = requests.get(ACCOUNTS_ZIP_URL)
        if res.status_code == 200:
            with open('accounts.zip', 'wb+') as f:
                f.write(res.content)
                f.close()
        else:
            logging.error(f"Failed to download accounts.zip {res.status_code}")
            raise KeyError
        subprocess.run(["unzip", "-q", "-o", "accounts.zip"])
        os.remove("accounts.zip")
except KeyError:
    pass
#uptobox
try:
    UPTOBOX_TOKEN = getConfig('UPTOBOX_TOKEN')
    if len(UPTOBOX_TOKEN) == 0:
        raise KeyError
except KeyError:
    UPTOBOX_TOKEN = None
tgDefaults = tg.Defaults(parse_mode='HTML', disable_web_page_preview=True, allow_sending_without_reply=True)
updater = tg.Updater(token=BOT_TOKEN, defaults=tgDefaults, request_kwargs={'read_timeout': 20, 'connect_timeout': 15})
bot = updater.bot
dispatcher = updater.dispatcher
