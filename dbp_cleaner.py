import os
import sys
import shutil
import json
import datetime
import time
import argparse
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

if sys.platform == "win32":
    import winreg

# --- Pfade und Setup ---
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
    "last_run_cleanup": ""
}

LOG_SIZE_BYTES = {
    "0.5": int(0.5 * 1024 * 1024),
    "1": 1 * 1024 * 1024,
    "5": 5 * 1024 * 1024,
    "10": 10 * 1024 * 1024,
    "unlimited": None
}

# --- Übersetzungen (i18n) ---
TRANSLATIONS = {
    "English": {
        "title_portable": "DBP - Portable Mode",
        "title_config": "DBP - Configuration",
        "menu_options": "Options",
        "menu_portable": "Open Portable Mode",
        "menu_config": "Open Configuration",
        "menu_language": "Language",
        "menu_uninstall": "Uninstall DBP Cleaner",
        "lbl_source": "Source folder (e.g. Downloads):",
        "lbl_target": "Target folder (Archive):",
        "lbl_exts": "Extensions to keep (comma-separated):",
        "lbl_interval": "Interval:",
        "lbl_log_size": "Max. Log Size:",
        "btn_browse": "Browse",
        "btn_execute": "Execute once now",
        "btn_save": "Save Configuration",
        "btn_logs": "View latest logs in text editor",
        "btn_uninstall": "Uninstall Program Completely",
        "chk_autostart": "Run in background on PC startup (Autostart)",
        "msg_error_title": "Error",
        "msg_error_dirs": "Please specify source and target folders.",
        "msg_saved_title": "Saved",
        "msg_saved_text": "Configuration saved!\nLogs and Config are located at:\n{path}",
        "msg_no_logs": "No logs have been written yet.",
        "confirm_portable_title": "Confirm Permanent Deletion",
        "confirm_portable_text": (
            "In Portable Mode, the Trash is skipped!\n\n"
            "Files matching your extensions will be moved to the Archive folder, "
            "and ALL OTHER FILES in the source folder will be PERMANENTLY deleted immediately.\n\n"
            "Do you really want to continue?"
        ),
        "confirm_uninstall_title": "Uninstall DBP Cleaner",
        "confirm_uninstall_text": (
            "Do you really want to completely uninstall DBP Cleaner?\n\n"
            "The following will be permanently deleted:\n"
            "- All App Data (Configuration & Logs)\n"
            "- All files inside the DBP_Trash folder\n"
            "- Autostart & Start Menu entries\n"
            "- Windows / Revo Uninstaller registration\n\n"
            "Your archived files in the target folder will NOT be touched."
        ),
        "msg_uninstall_done_title": "Uninstalled",
        "msg_uninstall_done_text": "DBP Cleaner and all associated data have been completely removed.",
        "int_startup": "At every startup",
        "int_daily": "Daily",
        "int_weekly": "Weekly",
        "int_monthly": "Monthly",
        "size_0_5": "0.5 MB (Default)",
        "size_1": "1 MB",
        "size_5": "5 MB",
        "size_10": "10 MB",
        "size_unlimited": "Unlimited",
        "log_archive": "ARCHIVE:",
        "log_trash": "TRASH:",
        "log_deleted_direct": "PERMANENTLY DELETED (Portable):",
        "log_trash_cleaned": "TRASH CLEANED UP: {count} old elements (>= 7 days) permanently deleted.",
        "log_error_arch": "ERROR archiving",
        "log_error_trash": "ERROR moving to trash",
        "log_error_delete": "ERROR permanently deleting",
        "log_error_trash_item": "TRASH ERROR on item '{item}' ({action}): [{err_type}] {err_msg}",
        "log_summary": "Summary: {moved} to Archive, {trashed} to Trash.",
        "log_summary_portable": "Summary (Portable): {moved} to Archive, {deleted} permanently deleted.",
        "err_src_missing": "FATAL ERROR: Source folder does not exist: {path}",
        "err_src_access": "FATAL ERROR: Cannot read source folder '{path}': [{err_type}] {err_msg}",
        "err_tgt_create": "FATAL ERROR: Target folder '{path}' could not be created: [{err_type}] {err_msg}",
        "err_trash_create": "FATAL ERROR: Trash folder '{path}' could not be created: [{err_type}] {err_msg}",
        "err_trash_access": "FATAL ERROR: Trash folder '{path}' cannot be accessed: [{err_type}] {err_msg}",
        "notify_fatal_title": "DBP Cleaner - Fatal Error",
        "info_os_not_win": "This feature is only supported on Windows.",
        "info_title": "Info"
    },
    "Deutsch": {
        "title_portable": "DBP - Portable Modus",
        "title_config": "DBP - Konfiguration",
        "menu_options": "Optionen",
        "menu_portable": "Portable Modus öffnen",
        "menu_config": "Konfiguration öffnen",
        "menu_language": "Sprache",
        "menu_uninstall": "DBP Cleaner deinstallieren",
        "lbl_source": "Quellordner (z.B. Downloads):",
        "lbl_target": "Zielordner (Archiv):",
        "lbl_exts": "Dateiendungen behalten (kommagetrennt):",
        "lbl_interval": "Intervall:",
        "lbl_log_size": "Max. Log-Größe:",
        "btn_browse": "Suchen",
        "btn_execute": "Jetzt einmalig Ausführen",
        "btn_save": "Konfiguration speichern",
        "btn_logs": "Letzte Logs im Texteditor ansehen",
        "btn_uninstall": "Programm restlos deinstallieren",
        "chk_autostart": "Beim PC-Start im Hintergrund ausführen (Autostart)",
        "msg_error_title": "Fehler",
        "msg_error_dirs": "Bitte Quell- und Zielordner angeben.",
        "msg_saved_title": "Gespeichert",
        "msg_saved_text": "Konfiguration gespeichert!\nLogs und Config liegen in:\n{path}",
        "msg_no_logs": "Es wurden noch keine Logs geschrieben.",
        "confirm_portable_title": "Endgültiges Löschen bestätigen",
        "confirm_portable_text": (
            "Im Portable-Modus wird der Papierkorb übersprungen!\n\n"
            "Dateien mit den gewünschten Endungen werden in das Archiv verschoben. "
            "ALLE ANDEREN DATEIEN im Quellordner werden SOFORT und ENDGÜLTIG gelöscht.\n\n"
            "Möchten Sie wirklich fortfahren?"
        ),
        "confirm_uninstall_title": "DBP Cleaner deinstallieren",
        "confirm_uninstall_text": (
            "Möchten Sie DBP Cleaner wirklich restlos deinstallieren?\n\n"
            "Folgendes wird unwiderruflich gelöscht:\n"
            "- Alle App-Daten (Konfiguration & Logs)\n"
            "- Alle Dateien im DBP_Trash Papierkorb\n"
            "- Autostart- & Startmenü-Einträge\n"
            "- Windows- / Revo-Uninstaller-Registrierung\n\n"
            "Ihre archivierten Dateien im Zielordner bleiben selbstverständlich erhalten."
        ),
        "msg_uninstall_done_title": "Deinstalliert",
        "msg_uninstall_done_text": "DBP Cleaner und alle zugehörigen Daten wurden restlos entfernt.",
        "int_startup": "Bei jedem Start",
        "int_daily": "Täglich",
        "int_weekly": "Wöchentlich",
        "int_monthly": "Monatlich",
        "size_0_5": "0,5 MB (Standard)",
        "size_1": "1 MB",
        "size_5": "5 MB",
        "size_10": "10 MB",
        "size_unlimited": "Unendlich",
        "log_archive": "ARCHIV:",
        "log_trash": "PAPIERKORB:",
        "log_deleted_direct": "ENDGÜLTIG GELÖSCHT (Portable):",
        "log_trash_cleaned": "PAPIERKORB AUFGERÄUMT: {count} alte Elemente (>= 7 Tage) endgültig gelöscht.",
        "log_error_arch": "FEHLER beim Archivieren von",
        "log_error_trash": "FEHLER beim Verschieben in den Papierkorb von",
        "log_error_delete": "FEHLER beim direkten Löschen von",
        "log_error_trash_item": "PAPIERKORB-FEHLER bei Element '{item}' ({action}): [{err_type}] {err_msg}",
        "log_summary": "Zusammenfassung: {moved} ins Archiv, {trashed} in den Papierkorb.",
        "log_summary_portable": "Zusammenfassung (Portable): {moved} ins Archiv, {deleted} endgültig gelöscht.",
        "err_src_missing": "FATALER FEHLER: Quellordner existiert nicht: {path}",
        "err_src_access": "FATALER FEHLER: Quellordner '{path}' kann nicht gelesen werden: [{err_type}] {err_msg}",
        "err_tgt_create": "FATALER FEHLER: Zielordner '{path}' konnte nicht erstellt werden: [{err_type}] {err_msg}",
        "err_trash_create": "FATALER FEHLER: Papierkorb-Ordner '{path}' konnte nicht erstellt werden: [{err_type}] {err_msg}",
        "err_trash_access": "FATALER FEHLER: Zugriff auf Papierkorb-Ordner '{path}' fehlgeschlagen: [{err_type}] {err_msg}",
        "notify_fatal_title": "DBP Cleaner - Fataler Fehler",
        "info_os_not_win": "Diese Funktion wird nur unter Windows unterstützt.",
        "info_title": "Info"
    }
}

# --- Hilfsfunktion für das Icon ---
def resource_path(relative_path):
    """Holt den absoluten Pfad zur Ressource, kompatibel mit PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Windows Benachrichtigung ---
def send_windows_notification(title, message):
    """Zeigt bei fatalen Fehlern eine native Nachricht in der Windows-Benachrichtigungsleiste an."""
    if sys.platform != "win32":
        return

    safe_title = title.replace("'", "''").replace('"', '`"').replace("\r", " ").replace("\n", " ")
    safe_msg = message.replace("'", "''").replace('"', '`"').replace("\r", " ").replace("\n", " ")

    ps_script = f"""
    $ErrorActionPreference = 'SilentlyContinue'
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
    $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
    $textNodes =$template.GetElementsByTagName("text")
    $textNodes.Item(0).AppendChild($template.CreateTextNode('{safe_title}')) | Out-Null
    $textNodes.Item(1).AppendChild($template.CreateTextNode('{safe_msg}')) | Out-Null
    $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
    $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("DBP Cleaner")
    $notifier.Show($toast)

    if (-not $?) {{
        Add-Type -AssemblyName System.Windows.Forms
        Add-Type -AssemblyName System.Drawing
        $notify = New-Object System.Windows.Forms.NotifyIcon
        $notify.Icon = [System.Drawing.SystemIcons]::Error
        $notify.Visible = $true
        $notify.ShowBalloonTip(7000, '{safe_title}', '{safe_msg}', [System.Windows.Forms.ToolTipIcon]::Error)
        Start-Sleep -Seconds 7
        $notify.Dispose()
    }}
    """
    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
        )
    except Exception:
        pass

# --- Kernfunktionen ---
def ensure_dbp_dir():
    if not os.path.exists(DBP_DIR):
        os.makedirs(DBP_DIR)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            c = json.load(f)

            if c.get("interval") == "Bei jedem Start": c["interval"] = "startup"
            if c.get("interval") == "Täglich": c["interval"] = "daily"
            if c.get("interval") == "Wöchentlich": c["interval"] = "weekly"
            if c.get("interval") == "Monatlich": c["interval"] = "monthly"

            if str(c.get("max_log_size")) not in LOG_SIZE_BYTES:
                c["max_log_size"] = "0.5"

            for k, v in DEFAULT_CONFIG.items():
                if k not in c:
                    c[k] = v
            return c
    except Exception:
        return DEFAULT_CONFIG.copy()

config = load_config()

def t(key, **kwargs):
    """Holt die Übersetzung für das gewählte Wort/den Satz."""
    lang = config.get("language", "English")
    text = TRANSLATIONS.get(lang, TRANSLATIONS["English"]).get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text

def save_config(cfg):
    ensure_dbp_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4)

def get_app_paths():
    """Gibt Zielpfade für Startmenü, Autostart und Uninstaller zurück und sichert ggf. die EXE in DBP_DIR."""
    ensure_dbp_dir()
    ico_src = resource_path("besen.ico")
    if os.path.exists(ico_src) and not os.path.exists(INSTALLED_ICO):
        try:
            shutil.copy2(ico_src, INSTALLED_ICO)
        except Exception:
            pass

    if getattr(sys, "frozen", False):
        current_exe = os.path.abspath(sys.executable)
        if current_exe.lower() != os.path.abspath(INSTALLED_EXE).lower():
            try:
                shutil.copy2(current_exe, INSTALLED_EXE)
            except Exception:
                pass
        target_exe = INSTALLED_EXE if os.path.exists(INSTALLED_EXE) else current_exe
        icon_path = INSTALLED_ICO if os.path.exists(INSTALLED_ICO) else f"{target_exe},0"
        return {
            "target_bin": target_exe,
            "args_gui": "",
            "args_autostart": "-autostart",
            "uninstall_cmd": f'"{target_exe}" -uninstall',
            "icon_path": icon_path
        }
    else:
        python_dir = os.path.dirname(sys.executable)
        pythonw_exe = os.path.join(python_dir, "pythonw.exe")
        if not os.path.exists(pythonw_exe):
            pythonw_exe = sys.executable
        script_path = os.path.abspath(__file__)
        icon_path = INSTALLED_ICO if os.path.exists(INSTALLED_ICO) else f"{pythonw_exe},0"
        return {
            "target_bin": pythonw_exe,
            "args_gui": f'"{script_path}"',
            "args_autostart": f'"{script_path}" -autostart',
            "uninstall_cmd": f'"{pythonw_exe}" "{script_path}" -uninstall',
            "icon_path": icon_path
        }

def setup_startmenu_shortcut(enable=True):
    """Erstellt oder entfernt den Startmenü-Eintrag 'DBP Cleaner' (ohne .exe Endung)."""
    if sys.platform != "win32" or not STARTMENU_LNK:
        return

    if not enable:
        if os.path.exists(STARTMENU_LNK):
            try:
                os.remove(STARTMENU_LNK)
            except Exception:
                pass
        return

    paths = get_app_paths()
    icon_loc = paths["icon_path"]
    temp_vbs = os.path.join(DBP_DIR, "_create_shortcut.vbs")

    vbs_lines = [
        'Set oWS = WScript.CreateObject("WScript.Shell")',
        f'Set oLink = oWS.CreateShortcut("{STARTMENU_LNK}")',
        f'oLink.TargetPath = "{paths["target_bin"]}"',
        f'oLink.Arguments = "{paths["args_gui"].replace(chr(34), chr(34)*2)}"',
        f'oLink.WorkingDirectory = "{DBP_DIR}"',
        'oLink.Description = "DBP Cleaner"',
        f'oLink.IconLocation = "{icon_loc}"',
        'oLink.Save'
    ]
    try:
        with open(temp_vbs, "w", encoding="mbcs", errors="replace") as f:
            f.write("\r\n".join(vbs_lines))
        subprocess.run(
            ["cscript", "//NoLogo", temp_vbs],
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000),
            timeout=5
        )
    except Exception:
        pass
    finally:
        if os.path.exists(temp_vbs):
            try:
                os.remove(temp_vbs)
            except Exception:
                pass

def setup_uninstall_registry(enable=True):
    """Registriert oder entfernt das Programm für Windows 'Installierte Apps' & Revo Uninstaller."""
    if sys.platform != "win32":
        return

    if not enable:
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, UNINSTALL_REG_KEY)
        except FileNotFoundError:
            pass
        except Exception:
            pass
        return

    paths = get_app_paths()
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, UNINSTALL_REG_KEY)
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "DBP Cleaner")
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "DBP Cleaner")
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0")
        winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, DBP_DIR)
        winreg.SetValueEx(key, "DisplayIcon", 0, winreg.REG_SZ, paths["icon_path"])
        winreg.SetValueEx(key, "UninstallString", 0, winreg.REG_SZ, paths["uninstall_cmd"])
        winreg.SetValueEx(key, "QuietUninstallString", 0, winreg.REG_SZ, paths["uninstall_cmd"])
        winreg.SetValueEx(key, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoRepair", 0, winreg.REG_DWORD, 1)

        total_size_kb = 1024
        try:
            total_bytes = sum(
                os.path.getsize(os.path.join(DBP_DIR, f))
                for f in os.listdir(DBP_DIR)
                if os.path.isfile(os.path.join(DBP_DIR, f))
            )
            if total_bytes > 0:
                total_size_kb = max(1, total_bytes // 1024)
        except Exception:
            pass
        winreg.SetValueEx(key, "EstimatedSize", 0, winreg.REG_DWORD, int(total_size_kb))
        winreg.CloseKey(key)
    except Exception:
        pass

def register_system_integration():
    """Richtet Startmenü-Eintrag ('DBP Cleaner') und Windows/Revo-Deinstallation ein."""
    if sys.platform == "win32":
        setup_startmenu_shortcut(True)
        setup_uninstall_registry(True)

def setup_autostart(enable):
    """Erstellt oder entfernt das Autostart-VBScript mit dem Parameter -autostart."""
    if sys.platform != "win32":
        messagebox.showinfo(t("info_title"), t("info_os_not_win"))
        return

    if enable:
        paths = get_app_paths()
        if getattr(sys, "frozen", False):
            vbs_content = (
                'Set WshShell = CreateObject("WScript.Shell")\n'
                f'WshShell.Run """{paths["target_bin"]}"" -autostart", 0, False'
            )
        else:
            script_path = os.path.abspath(__file__)
            vbs_content = (
                'Set WshShell = CreateObject("WScript.Shell")\n'
                f'WshShell.Run """{paths["target_bin"]}"" ""{script_path}"" -autostart", 0, False'
            )

        try:
            with open(AUTOSTART_VBS, "w", encoding="utf-8") as f:
                f.write(vbs_content)
        except Exception as e:
            messagebox.showwarning(t("msg_error_title"), f"Autostart Error: {e}")
    else:
        if AUTOSTART_VBS and os.path.exists(AUTOSTART_VBS):
            try:
                os.remove(AUTOSTART_VBS)
            except Exception:
                pass

def uninstall_application(parent_window=None):
    """Entfernt restlos alle App-Daten, den DBP_Trash-Ordner, Autostart, Startmenü und Registry-Einträge."""
    own_root = None
    if parent_window is None:
        own_root = tk.Tk()
        own_root.withdraw()
        try:
            own_root.iconbitmap(resource_path("besen.ico"))
        except Exception:
            pass

    confirmed = messagebox.askyesno(
        t("confirm_uninstall_title"),
        t("confirm_uninstall_text"),
        icon="warning",
        parent=parent_window if parent_window else own_root
    )
    if not confirmed:
        if own_root:
            own_root.destroy()
        return

    # 1. Papierkorb (DBP_Trash) im Zielordner restlos löschen
    current_cfg = load_config()
    target_dir = current_cfg.get("target_dir", "")
    if target_dir:
        trash_dir = os.path.join(target_dir, "DBP_Trash")
        if os.path.exists(trash_dir):
            shutil.rmtree(trash_dir, ignore_errors=True)

    # 2. Autostart entfernen
    if AUTOSTART_VBS and os.path.exists(AUTOSTART_VBS):
        try:
            os.remove(AUTOSTART_VBS)
        except Exception:
            pass

    # 3. Startmenü-Verknüpfung ('DBP Cleaner.lnk') entfernen
    setup_startmenu_shortcut(False)

    # 4. Windows & Revo Uninstaller Registry-Eintrag entfernen
    setup_uninstall_registry(False)

    # 5. AppData-Ordner (Config, Logs, kopierte Dateien) löschen
    if os.path.exists(DBP_DIR):
        shutil.rmtree(DBP_DIR, ignore_errors=True)

    messagebox.showinfo(
        t("msg_uninstall_done_title"),
        t("msg_uninstall_done_text"),
        parent=parent_window if parent_window else own_root
    )

    if parent_window:
        parent_window.destroy()
    if own_root:
        own_root.destroy()

    # Falls die laufende EXE aus DBP_DIR gestartet wurde, Ordner verzögert nach Prozessende entfernen
    if sys.platform == "win32" and os.path.exists(DBP_DIR):
        try:
            subprocess.Popen(
                f'cmd.exe /c timeout /t 2 /nobreak > NUL & rmdir /s /q "{DBP_DIR}"',
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            )
        except Exception:
            pass

    sys.exit(0)

def enforce_log_size(max_size_key):
    """Stellt sicher, dass die Logdatei das eingestellte Größenlimit nicht überschreitet."""
    max_bytes = LOG_SIZE_BYTES.get(str(max_size_key), LOG_SIZE_BYTES["0.5"])
    if max_bytes is None or not os.path.exists(LOG_FILE):
        return

    try:
        current_size = os.path.getsize(LOG_FILE)
        if current_size <= max_bytes:
            return

        with open(LOG_FILE, "rb") as f:
            f.seek(current_size - max_bytes)
            data = f.read()

        text = data.decode("utf-8", errors="ignore")
        marker_pos = text.find("--- Lauf am ")
        if marker_pos != -1:
            text = text[marker_pos:]
        else:
            newline_pos = text.find("\n")
            if newline_pos != -1:
                text = text[newline_pos + 1:]

        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception:
        pass

def write_log(messages, cfg=None):
    ensure_dbp_dir()
    active_cfg = cfg if cfg is not None else config
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"--- Lauf am {now} ---\n")
            for msg in messages:
                f.write(msg + "\n")
            f.write("\n")
        enforce_log_size(active_cfg.get("max_log_size", "0.5"))
    except Exception as e:
        send_windows_notification(t("notify_fatal_title"), f"Log-Datei Fehler: {e}")

def check_interval(interval, last_run_str):
    if interval == "startup": return True
    if not last_run_str: return True

    try:
        last_run = datetime.datetime.strptime(last_run_str, "%Y-%m-%d").date()
    except ValueError:
        return True

    today = datetime.date.today()
    if interval == "daily": return today > last_run
    elif interval == "weekly": return (today - last_run).days >= 7
    elif interval == "monthly": return today.month != last_run.month or today.year != last_run.year
    return True

def get_unique_path(directory, filename):
    base, ext = os.path.splitext(filename)
    counter = 1
    new_path = os.path.join(directory, filename)
    while os.path.exists(new_path):
        new_path = os.path.join(directory, f"{base}_{counter}{ext}")
        counter += 1
    return new_path

def process_trash(trash_dir):
    deleted_count = 0
    now = time.time()
    trash_logs = []

    try:
        items = os.listdir(trash_dir)
    except Exception as e:
        fatal_msg = t("err_trash_access", path=trash_dir, err_type=type(e).__name__, err_msg=str(e))
        send_windows_notification(t("notify_fatal_title"), fatal_msg)
        return [fatal_msg]

    for item in items:
        item_path = os.path.join(trash_dir, item)
        try:
            file_age_seconds = now - os.path.getmtime(item_path)
            file_age_days = file_age_seconds / (24 * 3600)
        except Exception as e:
            trash_logs.append(
                t("log_error_trash_item", item=item, action="Zeitstempel prüfen", err_type=type(e).__name__, err_msg=str(e))
            )
            continue

        if file_age_days >= 7:
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                deleted_count += 1
            except Exception as e:
                trash_logs.append(
                    t("log_error_trash_item", item=item, action="Endgültig löschen", err_type=type(e).__name__, err_msg=str(e))
                )

    if deleted_count > 0:
        trash_logs.append(t("log_trash_cleaned", count=deleted_count))
    return trash_logs

def handle_fatal_error(msg, cfg, is_portable):
    """Dokumentiert fatale Fehler im Log und sendet eine Windows-Benachrichtigung."""
    if not is_portable:
        write_log([msg], cfg)
    send_windows_notification(t("notify_fatal_title"), msg)
    return [msg]

def perform_cleanup(cfg, is_portable=False):
    source = cfg.get("source_dir", "")
    target = cfg.get("target_dir", "")
    extensions_str = cfg.get("extensions", "")

    if not source or not os.path.exists(source):
        return handle_fatal_error(t("err_src_missing", path=source), cfg, is_portable)

    if not os.path.exists(target):
        try:
            os.makedirs(target)
        except Exception as e:
            return handle_fatal_error(
                t("err_tgt_create", path=target, err_type=type(e).__name__, err_msg=str(e)),
                cfg,
                is_portable
            )

    trash_dir = None
    if not is_portable:
        trash_dir = os.path.join(target, "DBP_Trash")
        if not os.path.exists(trash_dir):
            try:
                os.makedirs(trash_dir)
            except Exception as e:
                return handle_fatal_error(
                    t("err_trash_create", path=trash_dir, err_type=type(e).__name__, err_msg=str(e)),
                    cfg,
                    is_portable
                )

    ext_list = []
    for e in extensions_str.split(","):
        e = e.strip().lower()
        if e:
            if not e.startswith("."):
                e = "." + e
            ext_list.append(e)

    try:
        source_items = os.listdir(source)
    except Exception as e:
        return handle_fatal_error(
            t("err_src_access", path=source, err_type=type(e).__name__, err_msg=str(e)),
            cfg,
            is_portable
        )

    log = []
    moved_count = 0
    trashed_count = 0
    deleted_count = 0

    own_exe = os.path.abspath(sys.executable).lower() if getattr(sys, "frozen", False) else os.path.abspath(__file__).lower()

    for item_name in source_items:
        item_path = os.path.join(source, item_name)
        if os.path.abspath(item_path).lower() == own_exe:
            continue

        if os.path.isfile(item_path):
            _, ext = os.path.splitext(item_name)
            ext = ext.lower()

            if ext in ext_list:
                try:
                    target_path = get_unique_path(target, item_name)
                    shutil.move(item_path, target_path)
                    log.append(f"{t('log_archive')} {item_name} -> {os.path.basename(target_path)}")
                    moved_count += 1
                except Exception as e:
                    log.append(f"{t('log_error_arch')} '{item_name}': [{type(e).__name__}] {e}")
            else:
                if is_portable:
                    try:
                        os.remove(item_path)
                        log.append(f"{t('log_deleted_direct')} {item_name}")
                        deleted_count += 1
                    except Exception as e:
                        log.append(f"{t('log_error_delete')} '{item_name}': [{type(e).__name__}] {e}")
                else:
                    try:
                        trash_path = get_unique_path(trash_dir, item_name)
                        shutil.move(item_path, trash_path)
                        os.utime(trash_path, None)
                        log.append(f"{t('log_trash')} {item_name} -> {os.path.basename(trash_path)}")
                        trashed_count += 1
                    except Exception as e:
                        log.append(
                            f"{t('log_error_trash')} '{item_name}' (Ziel: '{trash_dir}'): [{type(e).__name__}] {e}"
                        )

    if not is_portable and trash_dir:
        trash_logs = process_trash(trash_dir)
        log.extend(trash_logs)

    if is_portable:
        summary = t("log_summary_portable", moved=moved_count, deleted=deleted_count)
    else:
        summary = t("log_summary", moved=moved_count, trashed=trashed_count)
    log.append(summary)

    if not is_portable:
        write_log(log, cfg)
        cfg["last_run_cleanup"] = datetime.date.today().strftime("%Y-%m-%d")
        save_config(cfg)

    return log

# --- GUIs ---
def open_logs():
    if os.path.exists(LOG_FILE):
        if sys.platform == "win32":
            os.startfile(LOG_FILE)
    else:
        messagebox.showinfo("Logs", t("msg_no_logs"))

def change_language(new_lang, window, callback):
    """Ändert die Sprache, speichert und lädt das UI neu."""
    config["language"] = new_lang
    save_config(config)
    window.destroy()
    callback()

def run_portable_gui():
    root = tk.Tk()
    root.title(t("title_portable"))

    try:
        root.iconbitmap(resource_path("besen.ico"))
    except Exception:
        pass

    root.geometry("520x500")

    menubar = tk.Menu(root)
    optmenu = tk.Menu(menubar, tearoff=0)
    optmenu.add_command(label=t("menu_config"), command=lambda: [root.destroy(), run_config_gui()])

    lang_menu = tk.Menu(optmenu, tearoff=0)
    lang_menu.add_command(label="English", command=lambda: change_language("English", root, run_portable_gui))
    lang_menu.add_command(label="Deutsch", command=lambda: change_language("Deutsch", root, run_portable_gui))

    optmenu.add_cascade(label=t("menu_language"), menu=lang_menu)
    optmenu.add_separator()
    optmenu.add_command(label=t("menu_uninstall"), command=lambda: uninstall_application(root))
    menubar.add_cascade(label=t("menu_options"), menu=optmenu)
    root.config(menu=menubar)

    ttk.Label(root, text=t("lbl_source")).pack(pady=(10, 0), padx=10, anchor="w")
    src_var = tk.StringVar()
    src_frame = ttk.Frame(root)
    src_frame.pack(fill="x", padx=10)
    ttk.Entry(src_frame, textvariable=src_var).pack(side="left", fill="x", expand=True)
    ttk.Button(src_frame, text=t("btn_browse"), command=lambda: src_var.set(filedialog.askdirectory())).pack(side="right")

    ttk.Label(root, text=t("lbl_target")).pack(pady=(10, 0), padx=10, anchor="w")
    tgt_var = tk.StringVar()
    tgt_frame = ttk.Frame(root)
    tgt_frame.pack(fill="x", padx=10)
    ttk.Entry(tgt_frame, textvariable=tgt_var).pack(side="left", fill="x", expand=True)
    ttk.Button(tgt_frame, text=t("btn_browse"), command=lambda: tgt_var.set(filedialog.askdirectory())).pack(side="right")

    ttk.Label(root, text=t("lbl_exts")).pack(pady=(10, 0), padx=10, anchor="w")
    ext_var = tk.StringVar(value=".pdf, .docx, .zip")
    ttk.Entry(root, textvariable=ext_var).pack(fill="x", padx=10)

    log_text = tk.Text(root, height=15)
    log_text.pack(fill="both", expand=True, padx=10, pady=10)

    def execute():
        log_text.delete(1.0, tk.END)
        if not src_var.get() or not tgt_var.get():
            messagebox.showwarning(t("msg_error_title"), t("msg_error_dirs"))
            return

        confirmed = messagebox.askyesno(
            t("confirm_portable_title"),
            t("confirm_portable_text"),
            icon="warning"
        )
        if not confirmed:
            return

        temp_config = {
            "source_dir": src_var.get(),
            "target_dir": tgt_var.get(),
            "extensions": ext_var.get()
        }

        result_log = perform_cleanup(temp_config, is_portable=True)
        for line in result_log:
            log_text.insert(tk.END, line + "\n")

    ttk.Button(root, text=t("btn_execute"), command=execute).pack(pady=10)
    root.mainloop()

def run_config_gui():
    register_system_integration()

    root = tk.Tk()
    root.title(t("title_config"))

    try:
        root.iconbitmap(resource_path("besen.ico"))
    except Exception:
        pass

    root.geometry("540x480")

    menubar = tk.Menu(root)
    filemenu = tk.Menu(menubar, tearoff=0)
    filemenu.add_command(label=t("menu_portable"), command=lambda: [root.destroy(), run_portable_gui()])

    lang_menu = tk.Menu(filemenu, tearoff=0)
    lang_menu.add_command(label="English", command=lambda: change_language("English", root, run_config_gui))
    lang_menu.add_command(label="Deutsch", command=lambda: change_language("Deutsch", root, run_config_gui))

    filemenu.add_cascade(label=t("menu_language"), menu=lang_menu)
    filemenu.add_separator()
    filemenu.add_command(label=t("menu_uninstall"), command=lambda: uninstall_application(root))
    menubar.add_cascade(label=t("menu_options"), menu=filemenu)
    root.config(menu=menubar)

    ttk.Label(root, text=t("lbl_source")).grid(row=0, column=0, padx=10, pady=10, sticky="w")
    src_var = tk.StringVar(value=config.get("source_dir", ""))
    ttk.Entry(root, textvariable=src_var, width=30).grid(row=0, column=1)
    ttk.Button(root, text=t("btn_browse"), command=lambda: src_var.set(filedialog.askdirectory())).grid(row=0, column=2, padx=5)

    ttk.Label(root, text=t("lbl_target")).grid(row=1, column=0, padx=10, pady=10, sticky="w")
    tgt_var = tk.StringVar(value=config.get("target_dir", ""))
    ttk.Entry(root, textvariable=tgt_var, width=30).grid(row=1, column=1)
    ttk.Button(root, text=t("btn_browse"), command=lambda: tgt_var.set(filedialog.askdirectory())).grid(row=1, column=2, padx=5)

    ttk.Label(root, text=t("lbl_exts")).grid(row=2, column=0, padx=10, pady=10, sticky="w")
    ext_var = tk.StringVar(value=config.get("extensions", ""))
    ttk.Entry(root, textvariable=ext_var, width=30).grid(row=2, column=1, columnspan=2, sticky="w")

    ttk.Label(root, text=t("lbl_interval")).grid(row=3, column=0, padx=10, pady=10, sticky="w")
    interval_map = {
        "startup": t("int_startup"),
        "daily": t("int_daily"),
        "weekly": t("int_weekly"),
        "monthly": t("int_monthly")
    }
    inverse_interval_map = {v: k for k, v in interval_map.items()}
    current_interval_key = config.get("interval", "startup")
    interval_var = tk.StringVar(value=interval_map.get(current_interval_key, interval_map["startup"]))
    ttk.Combobox(
        root,
        textvariable=interval_var,
        values=list(interval_map.values()),
        state="readonly",
        width=27
    ).grid(row=3, column=1, columnspan=2, sticky="w")

    ttk.Label(root, text=t("lbl_log_size")).grid(row=4, column=0, padx=10, pady=10, sticky="w")
    log_size_map = {
        "0.5": t("size_0_5"),
        "1": t("size_1"),
        "5": t("size_5"),
        "10": t("size_10"),
        "unlimited": t("size_unlimited")
    }
    inverse_log_size_map = {v: k for k, v in log_size_map.items()}
    current_size_key = str(config.get("max_log_size", "0.5"))
    log_size_var = tk.StringVar(value=log_size_map.get(current_size_key, log_size_map["0.5"]))
    ttk.Combobox(
        root,
        textvariable=log_size_var,
        values=list(log_size_map.values()),
        state="readonly",
        width=27
    ).grid(row=4, column=1, columnspan=2, sticky="w")

    autostart_var = tk.BooleanVar(value=config.get("autostart", False))
    ttk.Checkbutton(
        root,
        text=t("chk_autostart"),
        variable=autostart_var
    ).grid(row=5, column=0, columnspan=3, padx=10, pady=10, sticky="w")

    def save_and_close():
        config["source_dir"] = src_var.get()
        config["target_dir"] = tgt_var.get()
        config["extensions"] = ext_var.get()
        config["interval"] = inverse_interval_map.get(interval_var.get(), "startup")
        config["max_log_size"] = inverse_log_size_map.get(log_size_var.get(), "0.5")
        config["autostart"] = autostart_var.get()

        save_config(config)
        register_system_integration()
        enforce_log_size(config["max_log_size"])
        setup_autostart(autostart_var.get())

        messagebox.showinfo(t("msg_saved_title"), t("msg_saved_text", path=DBP_DIR))
        root.destroy()

    ttk.Button(root, text=t("btn_save"), command=save_and_close).grid(row=6, column=0, columnspan=3, pady=(15, 5))
    ttk.Button(root, text=t("btn_logs"), command=open_logs).grid(row=7, column=0, columnspan=3, pady=5)
    ttk.Button(root, text=t("btn_uninstall"), command=lambda: uninstall_application(root)).grid(row=8, column=0, columnspan=3, pady=(10, 5))

    root.mainloop()

# --- Hauptlogik ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Bereinigungs Programm (DBP)")
    parser.add_argument("-gui", action="store_true", help="Open Configuration GUI")
    parser.add_argument("-portable", action="store_true", help="Open Portable Mode")
    parser.add_argument("-autostart", action="store_true", help="Run background cleanup via Autostart")
    parser.add_argument("-uninstall", action="store_true", help="Completely uninstall DBP Cleaner")
    args = parser.parse_args()

    if args.uninstall:
        uninstall_application()
    elif args.portable:
        run_portable_gui()
    elif args.autostart:
        src = config.get("source_dir", "")
        tgt = config.get("target_dir", "")
        if src and tgt:
            interval = config.get("interval", "startup")
            last_run = config.get("last_run_cleanup", "")
            if check_interval(interval, last_run):
                perform_cleanup(config, is_portable=False)
    else:
        # Standard bei normalem Doppelklick auf die .exe (oder -gui): Immer das Menü öffnen
        run_config_gui()