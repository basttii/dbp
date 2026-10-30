"""
System integration, shortcuts, registry and uninstaller for DBP Cleaner.
"""

import os
import sys
import stat
import shutil
import subprocess
import tkinter as tk
from tkinter import messagebox

if sys.platform == "win32":
    import winreg

from .constants import (
    DBP_DIR, CONFIG_FILE, INSTALLED_EXE, INSTALLED_ICO,
    AUTOSTART_VBS, STARTMENU_LNK, UNINSTALL_REG_KEY
)
from .i18n import t

def resource_path(relative_path):
    """Holt den absoluten Pfad zur Ressource, kompatibel mit PyInstaller."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def safe_remove_file(file_path):
    """Löscht eine Datei sicher, auch wenn sie schreibgeschützt (Read-Only) ist."""
    try:
        os.remove(file_path)
    except PermissionError:
        try:
            os.chmod(file_path, stat.S_IWRITE)
            os.remove(file_path)
        except Exception:
            raise

def on_rmtree_error(func, path, exc_info):
    """Fehlerbehandlung für shutil.rmtree, um schreibgeschützte Dateien auf Windows zu löschen."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        pass

def safe_rmtree(dir_path):
    """Löscht ein Verzeichnis mitsamt allen Dateien, auch bei Schreibschutz."""
    if not os.path.exists(dir_path):
        return
    try:
        shutil.rmtree(dir_path, onerror=on_rmtree_error)
    except TypeError:
        # Python 3.12+ unterstützt on_exc
        shutil.rmtree(dir_path, on_exc=on_rmtree_error)

def send_windows_notification(title, message):
    """Zeigt bei Fehlern eine native Benachrichtigung in Windows an."""
    if sys.platform != "win32":
        return

    safe_title = title.replace("'", "''").replace('"', '`"').replace("\r", " ").replace("\n", " ").replace("$", "`$")
    safe_msg = message.replace("'", "''").replace('"', '`"').replace("\r", " ").replace("\n", " ").replace("$", "`$")

    ps_script = f"""
    $ErrorActionPreference = 'SilentlyContinue'
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
    $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
    $textNodes = $template.GetElementsByTagName("text")
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

def get_app_paths():
    """Gibt Zielpfade für Startmenü, Autostart und Uninstaller zurück und sichert ggf. die EXE in DBP_DIR."""
    if not os.path.exists(DBP_DIR):
        os.makedirs(DBP_DIR, exist_ok=True)

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
        
        # Einstiegsskript ermitteln
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        script_path = os.path.join(root_dir, "dbp_cleaner.py")
        if not os.path.exists(script_path):
            script_path = os.path.abspath(sys.argv[0])

        icon_path = INSTALLED_ICO if os.path.exists(INSTALLED_ICO) else f"{pythonw_exe},0"
        return {
            "target_bin": pythonw_exe,
            "args_gui": f'"{script_path}"',
            "args_autostart": f'"{script_path}" -autostart',
            "uninstall_cmd": f'"{pythonw_exe}" "{script_path}" -uninstall',
            "icon_path": icon_path
        }

def setup_startmenu_shortcut(enable=True):
    """Erstellt oder entfernt den Startmenü-Eintrag 'DBP Cleaner'."""
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
        with open(temp_vbs, "w", encoding="utf-16", errors="replace") as f:
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
        except (FileNotFoundError, OSError):
            pass
        return

    paths = get_app_paths()
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, UNINSTALL_REG_KEY)
        winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "DBP Cleaner")
        winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "DBP Cleaner")
        winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.1.0")
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
    """Erstellt oder entfernt das Autostart-VBScript mit UTF-8-BOM-Kodierung."""
    if sys.platform != "win32":
        messagebox.showinfo(t("info_title"), t("info_os_not_win"))
        return

    if enable:
        paths = get_app_paths()
        if getattr(sys, "frozen", False):
            vbs_content = (
                'Set WshShell = CreateObject("WScript.Shell")\n'
                f'WshShell.Run """{paths["target_bin"]}"" -autostart", 0, False\n'
            )
        else:
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            script_path = os.path.join(root_dir, "dbp_cleaner.py")
            if not os.path.exists(script_path):
                script_path = os.path.abspath(sys.argv[0])
            vbs_content = (
                'Set WshShell = CreateObject("WScript.Shell")\n'
                f'WshShell.Run """{paths["target_bin"]}"" ""{script_path}"" -autostart", 0, False\n'
            )

        try:
            # UTF-16 mit LE-BOM, damit Windows Script Host (WScript/CScript) alle Zeichen fehlerfrei liest
            with open(AUTOSTART_VBS, "w", encoding="utf-16") as f:
                f.write(vbs_content)
        except Exception as e:
            messagebox.showwarning(t("msg_error_title"), f"Autostart Error: {e}")
    else:
        if AUTOSTART_VBS and os.path.exists(AUTOSTART_VBS):
            try:
                os.remove(AUTOSTART_VBS)
            except Exception:
                pass

def uninstall_application(parent_window=None, cfg_getter=None):
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

    from .config import load_config
    current_cfg = cfg_getter() if cfg_getter else load_config()
    target_dir = current_cfg.get("target_dir", "")
    if target_dir:
        trash_dir = os.path.join(target_dir, "DBP_Trash")
        if os.path.exists(trash_dir):
            safe_rmtree(trash_dir)

    # Autostart entfernen
    if AUTOSTART_VBS and os.path.exists(AUTOSTART_VBS):
        try:
            os.remove(AUTOSTART_VBS)
        except Exception:
            pass

    # Startmenü entfernen
    setup_startmenu_shortcut(False)

    # Registry-Eintrag entfernen
    setup_uninstall_registry(False)

    # AppData entfernen
    if os.path.exists(DBP_DIR):
        safe_rmtree(DBP_DIR)

    messagebox.showinfo(
        t("msg_uninstall_done_title"),
        t("msg_uninstall_done_text"),
        parent=parent_window if parent_window else own_root
    )

    if parent_window:
        parent_window.destroy()
    if own_root:
        own_root.destroy()

    if sys.platform == "win32" and os.path.exists(DBP_DIR):
        try:
            subprocess.Popen(
                f'cmd.exe /c timeout /t 2 /nobreak > NUL & rmdir /s /q "{DBP_DIR}"',
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            )
        except Exception:
            pass

    sys.exit(0)
