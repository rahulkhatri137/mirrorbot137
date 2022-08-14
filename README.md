# MirrorBot137

**Important** - Read these points first
- Original repo is https://github.com/lzzy12/python-aria-mirror-bot
- I have collected some cool features from various repositories and merged them in one.
- So, credits goes to original repo holder, not to me. I have just collected them.
- This (or any custom) repo is not supported in official bot support group.

### What is this repo about?
This is a telegram bot writen in python for mirroring files on the internet to our beloved Google Drive.

## Inspiration
This project is heavily inspired from @out386 's telegram bot which is written in JS .

<details>
<summary>Features supported:</summary>


- Mirroring direct download links to google drive/Telegram
- Mirroring Mega.nz links to google drive/Telegram
- Mirror Telegram files to google drive
- Mirror all youtube-dl supported links
- Mirror Torrent Files and magnet links
- Mirror By Reply
- Mirror/Leech multiple Links or Files
- Custom filename support in direct link, telegram files, YT-DL links
- Extract these filetypes and uploads to google drive
  > ZIP, RAR, TAR, 7z, ISO, WIM, CAB, GZIP, BZIP2, APM, ARJ, CHM, CPIO, CramFS,
  > DEB, DMG, FAT, HFS, LZH, LZMA, LZMA2, MBR, MSI, MSLZ, NSIS, NTFS, RPM,
  > SquashFS, UDF, VHD, XAR, Z.
- Copy files from someone's drive to your drive (using Autorclone)
- Service account support in cloning and uploading
- Download/upload progress,speeds and ETAs
- Docker support
- Uploading To Team Drives.
- Index Link support
- Shortener support
- View Index Links To Steam Videos Or Music Online (Works With Bhadoo)
- Leech Files To Telegram with custom Thumbnail & Names.
- Multi Drive Search. 
- SpeedTest.
- Count Drive Files.
- Extract password protected files (It's not hack, you have to enter password)
- For extracting password protected files, using custom filename and download

## Multi Search IDs
To use list from multi TD/folder. Run driveid.py in your terminal and follow it. It will generate **drive_folder** file or u can simply create `drive_folder` file in working directory and fill it, check below format:
```
MyTdName tdID IndexLink(if available)
MyTdName2 tdID IndexLink(if available)
```
Turn On RECURSIVE_SEARCH In Config -RECURSIVE_SEARCH = "True"

</details>

<details>
<summary>How to deploy?</summary>


Deploying is pretty much straight forward and is divided into several steps as follows:
## Installing requirements

- Clone this repo:
```
git clone -b master https://github.com/rahulkhatri137/mirrorbot137
cd mirrorbot137
```

- Install requirements
For Debian based distros
```
sudo apt install python3
```
Install Docker by following the [official docker docs](https://docs.docker.com/engine/install/debian/)


- For Arch and it's derivatives:
```
sudo pacman -S docker python
```

- Install dependencies for running setup scripts:
```
pip3 install -r requirements-cli.txt
```

## Deploying

- Start docker daemon (skip if already running):
````

sudo dockerd

````

- Build Docker image:
```sudo docker build . -t mirror-bot
````

- Run the image:

```
sudo docker run mirror-bot
```

 </details>


<details>   
    <summary>Setting up config file</summary>

```
cp config_sample.env config.env
```

- Remove the first line saying:

```
_____REMOVE_THIS_LINE_____=True
```

Fill up rest of the fields. Meaning of each field is discussed below:

**1. Required Fields**

- `BOT_TOKEN`: The Telegram Bot Token that you got from [@BotFather](https://t.me/BotFather)
- `TELEGRAM_API`: This is to authenticate your Telegram account for downloading Telegram files. You can get this from https://my.telegram.org. `Int`
- `TELEGRAM_HASH`: This is to authenticate your Telegram account for downloading Telegram files. You can get this from https://my.telegram.org.
- `OWNER_ID`: The Telegram User ID (not username) of the Owner of the bot. `Int`
- `GDRIVE_FOLDER_ID`: This is the Folder/TeamDrive ID of the Google Drive Folder to which you want to upload all the mirrors.
- `DOWNLOAD_DIR`: The path to the local folder where the downloads should be downloaded to.
- `DOWNLOAD_STATUS_UPDATE_INTERVAL`: Time in seconds after which the progress/status message will be updated. Recommended `10` seconds at least. `Int`
- `AUTO_DELETE_MESSAGE_DURATION`: Interval of time (in seconds), after which the bot deletes it's message and command message which is expected to be viewed instantly. **NOTE**: Set to `-1` to disable auto message deletion. `Int`

**2. Optional Fields**

- `ACCOUNTS_ZIP_URL`: Only if you want to load your Service Account externally from an Index Link or by any direct download link NOT webpage link. Archive the accounts folder to ZIP file. Fill this with the direct download link of zip file. If index need authentication so add direct download as shown below:
  - `https://username:password@example.workers.dev/...`
- `TOKEN_PICKLE_URL`: Only if you want to load your **token.pickle** externally from an Index Link. Fill this with the direct link of that file.
- `DATABASE_URL`: Your SQL Database URL. Follow the Generate Database Guide below. Data will be saved in Database: auth and sudo users, leech settings including thumbnails for each user, rss data and incomplete tasks. **NOTE**: If deploying on heroku and using heroku postgresql delete this variable from **config.env** file. **DATABASE_URL** will be grabbed from heroku variables.
- `AUTHORIZED_CHATS`: Fill user_id and chat_id of groups/users you want to authorize. Separate them by space.
- `SUDO_USERS`: Fill user_id of users whom you want to give sudo permission. Separate them by space.
- `IS_TEAM_DRIVE`: Set `True` if uploading to TeamDrive. Default is `False`. `Bool`
- `USE_SERVICE_ACCOUNTS`: Whether to use Service Accounts or not. For this to work see Using Service Accounts section below. Default is `False`. `Bool`
- `INDEX_URL`: Refer to [Bhadoo Index](https://github.com/rahulkhatri137/Google-Drive-Index) [GoIndex](https://github.com/rahulkhatri137/goindex) [GD Index](https://github.com/rahulkhatri137/GDIndex).
- `MEGA_KEY`: Mega.nz API key to mirror mega.nz links. Get it from [Mega SDK Page](https://mega.nz/sdk)
- `MEGA_USERNAME`: E-Mail ID used to sign up on mega.nz for using premium account.
- `MEGA_PASSWORD`: Password for mega.nz account.
- `UPTOBOX_TOKEN`: Uptobox token to mirror uptobox links. Get it from [Uptobox Premium Account](https://uptobox.com/my_account).
- `STOP_DUPLICATE_CLONE`: Bot will check file in Drive, if it is present in Drive, downloading or cloning will be stopped. (**NOTE**: File will be checked using filename not file hash, so this feature is not perfect yet). Default is `False`. `Bool`
- `CLONE_LIMIT`: To limit the size of Google Drive folder/file which you can clone. Don't add unit. Default unit is `GB`.
- `VIEW_LINK`: View Link button to open file Index Link in browser instead of direct download link, you can figure out if it's compatible with your Index code or not, open any video from you Index and check if its URL ends with `?a=view`, if yes make it `True`, compatible with [BhadooIndex](https://gitlab.com/ParveenBhadooOfficial/Google-Drive-Index) Code. Default is `False`. `Bool`
- `IGNORE_PENDING_REQUESTS`: Ignore pending requests after restart. Default is `False`. `Bool`
- `TG_SPLIT_SIZE`: Size of split in bytes. Default is `2GB`.
- `AS_DOCUMENT`: Default type of Telegram file upload. Default is `False` mean as media. `Bool`
- `CUSTOM_FILENAME`: Add custom word to leeched file name.
- `SHORTENER_API`: Fill your Shortener API key.
- `SHORTENER`: Shortener URL.
  - Supported URL Shorteners:
  >exe.io gplinks.in shrinkme.io urlshortx.com shortzon.com
- `CRYPT`: Cookie for gdtot google drive link generator.
- `PHPSESSID`: Cookie for gdtot google drive link generator.
- `RECURSIVE_SEARCH`: T/F And Fill drive_folder File Using Driveid.py Script.

  - `BUTTON_THREE_NAME`:
  - `BUTTON_THREE_URL`:
  - `BUTTON_FOUR_NAME`:
  - `BUTTON_FOUR_URL`:
  - `BUTTON_FIVE_NAME`:
  - `BUTTON_FIVE_URL`:

Note: You can limit maximum concurrent downloads by changing the value of
MAX_CONCURRENT_DOWNLOADS in aria.sh.

## Getting Google OAuth API credential file

- Visit the
  [Google Cloud Console](https://console.developers.google.com/apis/credentials)
- Go to the OAuth Consent tab, fill it, and save.
- Go to the Credentials tab and click Create Credentials -> OAuth Client ID
- Choose Other and Create.
- Use the download button to download your credentials.
- Move that file to the root of mirror-bot, and rename it to credentials.json
- Visit [Google API page](https://console.developers.google.com/apis/library)
- Search for Drive and enable it if it is disabled
- Finally, run the script to generate token file (token.pickle) for Google
  Drive:

```
pip install google-api-python-client google-auth-httplib2
google-auth-oauthlib python3 generate_drive_token.py 
```

## Gdtot Cookies
To Clone or Leech gdtot link follow these steps:
1. Login/Register to [gdtot](https://new.gdtot.top).
2. Copy this script and paste it in browser address bar.
   - **Note**: After pasting it check at the beginning of the script in broswer address bar if `javascript:` exists or not, if not so write it as shown below.
   ```
   javascript:(function () {
     const input = document.createElement('input');
     input.value = JSON.stringify({url : window.location.href, cookie : document.cookie});
     document.body.appendChild(input);
     input.focus();
     input.select();
     var result = document.execCommand('copy');
     document.body.removeChild(input);
     if(result)
       alert('Cookie copied to clipboard');
     else
       prompt('Failed to copy cookie. Manually copy below cookie\n\n', input.value);
   })();
   ```
   - After pressing enter your browser will prompt a alert.
3. Now you'll get this type of data in your clipboard
   ```
   {"url":"https://new.gdtot.org/","cookie":"PHPSESSID=k2xxxxxxxxxxxxxxxxxxxxj63o; crypt=NGxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxWdSVT0%3D"}

   ```
4. From this you have to paste value of PHPSESSID and crypt in config.env file.

## Generate Database

**1. Using ElephantSQL**
- Go to https://elephantsql.com and create account (skip this if you already have **ElephantSQL** account)
- Hit `Create New Instance`
- Follow the further instructions in the screen
- Hit `Select Region`
- Hit `Review`
- Hit `Create instance`
- Select your database name
- Copy your database url, and fill to `DATABASE_URL` in config

**2. Using Heroku PostgreSQL**
<p><a href="https://dev.to/prisma/how-to-setup-a-free-postgresql-database-on-heroku-1dc1"> <img src="https://img.shields.io/badge/See%20Dev.to-black?style=for-the-badge&logo=dev.to" width="160""/></a></p>

## Using service accounts for uploading to avoid user rate limit

For Service Account to work, you must set USE_SERVICE_ACCOUNTS="True" in config
file or environment variables Many thanks to
[AutoRClone](https://github.com/xyou365/AutoRclone) for the scripts **NOTE:**
Using service accounts is only recommended while uploading to a team drive.

## Generating service accounts

Generate service accounts [What is service account](https://cloud.google.com/iam/docs/service-accounts)

Let us create only the service accounts that we need. **Warning:** abuse of this
feature is not the aim of this project and we do **NOT** recommend that you make
a lot of projects, just one project and 100 sa allow you plenty of use, its also
possible that over abuse might get your projects banned by google.

Note: 1 service account can copy around 750gb a day, 1 project can make 100
service accounts so that's 75tb a day, for most users this should easily
suffice.

```
python3 gen_sa_accounts.py --quick-setup 1 --new-only
```

A folder named accounts will be created which will contain keys for the service
accounts

NOTE: If you have created SAs in past from this script, you can also just re
download the keys by running:

```
python3 gen_sa_accounts.py --download-keys project_id
```

### Add all the service accounts to the Team Drive

- Run:

```
python3 add_to_team_drive.py -d SharedTeamDriveSrcID
```

## Youtube-dl authentication using .netrc file

For using your premium accounts in youtube-dl, edit the netrc file (in the root
directory of this repository) according to following format:

```
machine host login username password my_youtube_password
```

where host is the name of extractor (eg. youtube, twitch). Multiple accounts of
different hosts can be added each separated by a new line.

</details>


## Deploy on [GitHub actions](https://github.com/rahulkhatri137/mirrorbot-workflow)
* [Deploy Video Tutorial](https://youtu.be/U9uxTKsfvaE)


## Deploying on Heroku
- Token Pickle URL is must for deploying on Heorku!

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://dashboard.heroku.com/new?button-url=https://github.com/rahulkhatri137/mirrorbot137-deployer&template=https://github.com/rahulkhatri137/mirrorbot137-deployer)


- Deploying on Heroku with Github Workflow
<p><a href="https://telegra.ph/Heroku-Deployment-10-04"> <img src="https://img.shields.io/badge/Deploy%20Guide-blueviolet?style=for-the-badge&logo=heroku" width="170""/></a></p>

## Credits :-

- First of all, full credit goes to
  [Shivam Jha aka lzzy12](https://github.com/lzzy12) and
  [JaskaranSM aka Zero Cool](https://github.com/jaskaranSM) They build up this bot from scratch.
- Then a huge thanks to Sreeraj V R [Repo](https://github.com/SVR666/LoaderX-Bot)
- Features added from SlamBot [Repo](https://github.com/breakdowns/slam-mirrorbot) (Archived)
- Thanks To Ken For Base [Repo](https://github.com/KenHV/Mirror-Bot)
- Thanks to Harsh For Improvements [Repo](https://github.com/harshpreets63/Mirror-Bot)
