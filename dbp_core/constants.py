import os
import sys

# Platform-specific paths
if sys.platform == "win32":
    BASE_DIR = os.environ.get("APPDATA", os.path.expanduser("~"))
    STARTUP_DIR = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
    STARTMENU_DIR = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs")
else:
    BASE_DIR = os.path.expanduser("~")
    STARTUP_DIR = ""
    STARTMENU_DIR = ""

DBP_DIR = os.path.join(BASE_DIR, "DBP_Cleaner")
CONFIG_FILE = os.path.join(DBP_DIR, "config.json")
LOG_FILE = os.path.join(DBP_DIR, "history.log")
INSTALLED_EXE = os.path.join(DBP_DIR, "DBP_Cleaner.exe")
INSTALLED_ICO = os.path.join(DBP_DIR, "besen.ico")

AUTOSTART_VBS = os.path.join(STARTUP_DIR, "DBP_Cleaner.vbs") if STARTUP_DIR else ""
STARTMENU_LNK = os.path.join(STARTMENU_DIR, "DBP Cleaner.lnk") if STARTMENU_DIR else ""
UNINSTALL_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\DBP_Cleaner"

DEFAULT_CONFIG = {
    "language": "English",
    "source_dir": "",
    "target_dir": "",
    "extensions": ".pdf, .docx, .xlsx, .jpg, .png, .zip",
    "interval": "startup",
    "max_log_size": "0.5",
    "autostart": False,
    "last_run_cleanup": "",
    "smart_trash": True,
    "include_subfolders": True,
    "clean_empty_folders": True,
    "protect_recent_hours": 24
}

LOG_SIZE_BYTES = {
    "0.5": int(0.5 * 1024 * 1024),
    "1": 1 * 1024 * 1024,
    "5": 5 * 1024 * 1024,
    "10": 10 * 1024 * 1024,
    "unlimited": None
}
