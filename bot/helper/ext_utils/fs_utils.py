import os
import shutil
import sys
import pathlib
import tarfile
import magic

from bot import DOWNLOAD_DIR, LOGGER, aria2
import subprocess
import time

from PIL import Image
from hachoir.parser import createParser
from hachoir.metadata import extractMetadata
from bot import aria2, LOGGER, DOWNLOAD_DIR, TG_SPLIT_SIZE

VIDEO_SUFFIXES = ("M4V", "MP4", "MOV", "FLV", "WMV", "3GP", "MPG", "WEBM", "MKV", "AVI")

from .exceptions import NotSupportedExtractionArchive


def clean_download(path: str):
    if os.path.exists(path):
        LOGGER.info(f"Cleaning download: {path}")
        shutil.rmtree(path)


def start_cleanup():
    try:
        shutil.rmtree(DOWNLOAD_DIR)
    except FileNotFoundError:
        pass


def clean_all():
    aria2.remove_all(True)
    try:
        shutil.rmtree(DOWNLOAD_DIR)
    except FileNotFoundError:
        pass


def exit_clean_up(signal, frame):
    try:
        LOGGER.info(
            "Please wait, while we clean up the downloads and stop running downloads"
        )
        clean_all()
        sys.exit(0)
    except KeyboardInterrupt:
        LOGGER.warning("Force Exiting before the cleanup finishes!")
        sys.exit(1)


def get_path_size(path):
    if os.path.isfile(path):
        return os.path.getsize(path)
    total_size = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            abs_path = os.path.join(root, f)
            total_size += os.path.getsize(abs_path)
    return total_size

def tar(org_path):
    tar_path = f"{org_path}.tar"
    path = pathlib.PurePath(org_path)
    LOGGER.info(f"Tar: orig_path: {org_path}, tar_path: {tar_path}")
    tar = tarfile.open(tar_path, "w")
    tar.add(org_path, arcname=path.name)
    tar.close()
    return tar_path

def get_base_name(orig_path: str):
    if orig_path.endswith(".tar.bz2"):
        return orig_path.replace(".tar.bz2", "")
    elif orig_path.endswith(".tar.gz"):
        return orig_path.replace(".tar.gz", "")
    elif orig_path.endswith(".bz2"):
        return orig_path.replace(".bz2", "")
    elif orig_path.endswith(".gz"):
        return orig_path.replace(".gz", "")
    elif orig_path.endswith(".tar.xz"):
        return orig_path.replace(".tar.xz", "")
    elif orig_path.endswith(".tar"):
        return orig_path.replace(".tar", "")
    elif orig_path.endswith(".tbz2"):
        return orig_path.replace("tbz2", "")
    elif orig_path.endswith(".tgz"):
        return orig_path.replace(".tgz", "")
    elif orig_path.endswith(".zip"):
        return orig_path.replace(".zip", "")
    elif orig_path.endswith(".7z"):
        return orig_path.replace(".7z", "")
    elif orig_path.endswith(".Z"):
        return orig_path.replace(".Z", "")
    elif orig_path.endswith(".rar"):
        return orig_path.replace(".rar", "")
    elif orig_path.endswith(".iso"):
        return orig_path.replace(".iso", "")
    elif orig_path.endswith(".wim"):
        return orig_path.replace(".wim", "")
    elif orig_path.endswith(".cab"):
        return orig_path.replace(".cab", "")
    elif orig_path.endswith(".apm"):
        return orig_path.replace(".apm", "")
    elif orig_path.endswith(".arj"):
        return orig_path.replace(".arj", "")
    elif orig_path.endswith(".chm"):
        return orig_path.replace(".chm", "")
    elif orig_path.endswith(".cpio"):
        return orig_path.replace(".cpio", "")
    elif orig_path.endswith(".cramfs"):
        return orig_path.replace(".cramfs", "")
    elif orig_path.endswith(".deb"):
        return orig_path.replace(".deb", "")
    elif orig_path.endswith(".dmg"):
        return orig_path.replace(".dmg", "")
    elif orig_path.endswith(".fat"):
        return orig_path.replace(".fat", "")
    elif orig_path.endswith(".hfs"):
        return orig_path.replace(".hfs", "")
    elif orig_path.endswith(".lzh"):
        return orig_path.replace(".lzh", "")
    elif orig_path.endswith(".lzma"):
        return orig_path.replace(".lzma", "")
    elif orig_path.endswith(".lzma2"):
        return orig_path.replace(".lzma2", "")
    elif orig_path.endswith(".mbr"):
        return orig_path.replace(".mbr", "")
    elif orig_path.endswith(".msi"):
        return orig_path.replace(".msi", "")
    elif orig_path.endswith(".mslz"):
        return orig_path.replace(".mslz", "")
    elif orig_path.endswith(".nsis"):
        return orig_path.replace(".nsis", "")
    elif orig_path.endswith(".ntfs"):
        return orig_path.replace(".ntfs", "")
    elif orig_path.endswith(".rpm"):
        return orig_path.replace(".rpm", "")
    elif orig_path.endswith(".squashfs"):
        return orig_path.replace(".squashfs", "")
    elif orig_path.endswith(".udf"):
        return orig_path.replace(".udf", "")
    elif orig_path.endswith(".vhd"):
        return orig_path.replace(".vhd", "")
    elif orig_path.endswith(".xar"):
        return orig_path.replace(".xar", "")
    else:
        raise NotSupportedExtractionArchive("File format not supported for extraction")


def get_mime_type(file_path):
    mime = magic.Magic(mime=True)
    mime_type = mime.from_file(file_path)
    mime_type = mime_type or "text/plain"
    return mime_type
def take_ss(video_file):
    des_dir = 'Thumbnails'
    if not os.path.exists(des_dir):
        os.mkdir(des_dir)
    des_dir = os.path.join(des_dir, f"{time.time()}.jpg")
    metadata = extractMetadata(createParser(video_file))
    duration = metadata.get('duration').seconds if metadata.has("duration") else 5
    duration = int(duration) / 2
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", str(duration),
                    "-i", video_file, "-vframes", "1", des_dir])
    if not os.path.lexists(des_dir):
        return None

    Image.open(des_dir).convert("RGB").save(des_dir)
    img = Image.open(des_dir)
    img.resize((480, 320))
    img.save(des_dir, "JPEG")
    return des_dir

def split(path, size, file, dirpath, split_size, start_time=0, i=1):
    if file.upper().endswith(VIDEO_SUFFIXES):
        base_name, extension = os.path.splitext(file)
        metadata = extractMetadata(createParser(path))
        total_duration = metadata.get('duration').seconds - 8
        split_size = split_size - 3000000
        while start_time < total_duration:
            parted_name = f"{str(base_name)}.part{str(i).zfill(3)}{str(extension)}"
            out_path = os.path.join(dirpath, parted_name)
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", 
                            path, "-ss", str(start_time), "-fs", str(split_size),
                            "-strict", "-2", "-c", "copy", out_path])
            out_size = get_path_size(out_path)
            if out_size > TG_SPLIT_SIZE:
                dif = out_size - TG_SPLIT_SIZE
                split_size = split_size - dif + 2000000
                os.remove(out_path)
                return split(path, size, file, dirpath, split_size, start_time, i)
            metadata = extractMetadata(createParser(out_path))
            start_time = start_time + metadata.get('duration').seconds - 5
            i = i + 1
    else:
        out_path = os.path.join(dirpath, f"{file}.")
        subprocess.run(["split", "--numeric-suffixes=1", "--suffix-length=3", f"--bytes={split_size}", path, out_path])