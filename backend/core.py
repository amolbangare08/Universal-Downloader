import os
import sys
import socket
import random
import glob
import shutil
import zipfile
import hashlib
import requests

# --- REGEX ---
YOUTUBE_REGEX = r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+"
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
HANDBRAKE_URL = "https://github.com/HandBrake/HandBrake/releases/download/1.8.2/HandBrakeCLI-1.8.2-win-x86_64.zip"

# --- COLOR CONSTANTS (used by downloaders.py finish methods in GUI mode) ---
C_SUCCESS = ("#10b981", "#10b981")
C_ERROR = ("#ef4444", "#ef4444")
C_STOP = ("#ef4444", "#ef4444")
C_STOP_HOVER = ("#dc2626", "#dc2626")
C_TEXT_SUB = ("#71717a", "#a1a1aa")

# --- PROXY LOADING ---
def load_proxies():
    proxy_file = "proxies.txt"
    if os.path.exists(proxy_file):
        try:
            with open(proxy_file, "r") as f:
                return [line.strip() for line in f if line.strip()]
        except OSError:
            return []
    return []

PROXY_POOL = load_proxies()

# --- HELPER FUNCTIONS ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def check_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def parse_time_to_seconds(time_str):
    """Converts various time formats to integer seconds."""
    if not time_str:
        return 0
    try:
        if time_str.isdigit():
            return int(time_str)
        parts = list(map(int, time_str.strip().split(':')))
        if len(parts) == 3:
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        if len(parts) == 2:
            return parts[0] * 60 + parts[1]
        return parts[0]
    except (ValueError, IndexError):
        return 0

def format_seconds_to_str(seconds):
    """Converts integer seconds back to MM:SS or HH:MM:SS."""
    if seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"
    else:
        h, remainder = divmod(seconds, 3600)
        m, s = divmod(remainder, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"

def verify_file_not_empty(filepath):
    """Basic integrity check: ensure downloaded file exists and isn't truncated."""
    if not os.path.exists(filepath):
        return False
    return os.path.getsize(filepath) > 1024  # at least 1KB

def check_tool_dependencies():
    print("-" * 50)
    print("SYSTEM INITIALIZATION...")
    print("-" * 50)
    cwd = os.getcwd()
    ffmpeg_path = os.path.join(cwd, "ffmpeg.exe")
    handbrake_path = os.path.join(cwd, "HandBrakeCLI.exe")

    if not os.path.exists(ffmpeg_path):
        if shutil.which("ffmpeg"):
            ffmpeg_path = shutil.which("ffmpeg")
        else:
            try:
                r = requests.get(FFMPEG_URL, stream=True, timeout=30, proxies={"http": None, "https": None})
                if r.status_code == 200:
                    with open("ffmpeg.zip", 'wb') as f:
                        shutil.copyfileobj(r.raw, f)
                    if not verify_file_not_empty("ffmpeg.zip"):
                        os.remove("ffmpeg.zip")
                        raise RuntimeError("Downloaded ffmpeg archive is too small or corrupt")
                    with zipfile.ZipFile("ffmpeg.zip", 'r') as z:
                        for i in z.infolist():
                            if i.filename.endswith("bin/ffmpeg.exe"):
                                i.filename = "ffmpeg.exe"
                                z.extract(i, cwd)
                                break
                    os.remove("ffmpeg.zip")
            except (requests.RequestException, zipfile.BadZipFile, RuntimeError, OSError) as e:
                print(f"[Warning] Could not auto-install ffmpeg: {e}")

    if not os.path.exists(handbrake_path):
        try:
            h = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(HANDBRAKE_URL, headers=h, stream=True, timeout=30, proxies={"http": None, "https": None})
            if r.status_code == 200:
                with open("handbrake.zip", 'wb') as f:
                    shutil.copyfileobj(r.raw, f)
                if not verify_file_not_empty("handbrake.zip"):
                    os.remove("handbrake.zip")
                    raise RuntimeError("Downloaded HandBrake archive is too small or corrupt")
                with zipfile.ZipFile("handbrake.zip", 'r') as z:
                    for i in z.infolist():
                        if i.filename.endswith("HandBrakeCLI.exe"):
                            i.filename = "HandBrakeCLI.exe"
                            z.extract(i, cwd)
                            break
                os.remove("handbrake.zip")
        except (requests.RequestException, zipfile.BadZipFile, RuntimeError, OSError) as e:
            print(f"[Warning] Could not auto-install HandBrakeCLI: {e}")

    return ffmpeg_path, handbrake_path
