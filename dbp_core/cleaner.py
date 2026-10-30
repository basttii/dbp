"""
Core Cleanup Engine for DBP Cleaner.

Handles file archiving, smart trash evaluation, recursive subfolder scanning,
folder deletion, and trash retention management.
"""

import os
import sys
import time
import shutil
import datetime
from .constants import DBP_DIR, LOG_FILE, LOG_SIZE_BYTES
from .i18n import t
from .config import save_config, ensure_dbp_dir
from .system import send_windows_notification, safe_remove_file, safe_rmtree
from .smart_trash import evaluate_file_importance, is_in_progress_download

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
            f.seek(max(0, current_size - max_bytes))
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
    """Schreibt Log-Einträge in die Logdatei und führt die Größenbegrenzung durch."""
    ensure_dbp_dir()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    max_size = (cfg or {}).get("max_log_size", "0.5")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"--- Lauf am {now} ---\n")
            for msg in messages:
                f.write(msg + "\n")
            f.write("\n")
        enforce_log_size(max_size)
    except Exception as e:
        send_windows_notification(t("notify_fatal_title"), f"Log-Datei Fehler: {e}")

def check_interval(interval, last_run_str):
    """Prüft, ob basierend auf dem konfigurierten Intervall eine Bereinigung fällig ist."""
    if interval == "startup":
        return True
    if not last_run_str:
        return True

    try:
        last_run = datetime.datetime.strptime(last_run_str, "%Y-%m-%d").date()
    except ValueError:
        return True

    today = datetime.date.today()
    if interval == "daily":
        return today > last_run
    elif interval == "weekly":
        return (today - last_run).days >= 7
    elif interval == "monthly":
        return today.month != last_run.month or today.year != last_run.year
    return True

def get_unique_path(directory, filename):
    """Erzeugt einen kollisionsfreien Zielpfad im Zielverzeichnis."""
    base, ext = os.path.splitext(filename)
    counter = 1
    new_path = os.path.join(directory, filename)
    while os.path.exists(new_path):
        new_path = os.path.join(directory, f"{base}_{counter}{ext}")
        counter += 1
    return new_path

def is_same_or_subpath(child_path, parent_path):
    """Prüft sicher, ob child_path identisch mit parent_path oder darin enthalten ist."""
    try:
        norm_child = os.path.normcase(os.path.abspath(child_path))
        norm_parent = os.path.normcase(os.path.abspath(parent_path))
        if norm_child == norm_parent:
            return True
        rel = os.path.relpath(norm_child, norm_parent)
        return not (rel.startswith("..") or os.path.isabs(rel))
    except Exception:
        return False

def process_trash(trash_dir):
    """Löscht Elemente im DBP_Trash-Ordner, die 7 Tage oder älter sind."""
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
                    safe_remove_file(item_path)
                elif os.path.isdir(item_path):
                    safe_rmtree(item_path)
                deleted_count += 1
            except Exception as e:
                trash_logs.append(
                    t("log_error_trash_item", item=item, action="Endgültig löschen", err_type=type(e).__name__, err_msg=str(e))
                )

    if deleted_count > 0:
        trash_logs.append(t("log_trash_cleaned", count=deleted_count))
    return trash_logs

def handle_fatal_error(msg, cfg, is_portable):
    """Dokumentiert fatale Fehler im Log und sendet eine Benachrichtigung."""
    if not is_portable:
        write_log([msg], cfg)
    send_windows_notification(t("notify_fatal_title"), msg)
    return [msg]

def perform_cleanup(cfg, is_portable=False):
    """
    Führt die Bereinigung durch.
    - Findet Dateien und Unterordner (rekursiv falls konfiguriert)
    - Erkennt wichtige Dateien via Smart Trash
    - Schützt laufende Downloads vor Abbruch
    - Verschiebt Treffer ins Archiv
    - Befördert Müll in den Papierkorb (oder löscht direkt im Portable-Modus)
    - Entfernt leere / bereinigte Unterordner
    """
    source = cfg.get("source_dir", "").strip()
    target = cfg.get("target_dir", "").strip()
    extensions_str = cfg.get("extensions", "")
    include_subfolders = cfg.get("include_subfolders", True)
    clean_empty_folders = cfg.get("clean_empty_folders", True)
    smart_trash_enabled = cfg.get("smart_trash", True)
    protect_recent_hours = cfg.get("protect_recent_hours", 24)

    if not source or not os.path.exists(source):
        return handle_fatal_error(t("err_src_missing", path=source), cfg, is_portable)

    norm_src = os.path.normcase(os.path.abspath(source))
    norm_tgt = os.path.normcase(os.path.abspath(target)) if target else ""

    if norm_src == norm_tgt:
        return handle_fatal_error(t("msg_error_same_dirs"), cfg, is_portable)

    if not os.path.exists(target):
        try:
            os.makedirs(target, exist_ok=True)
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
                os.makedirs(trash_dir, exist_ok=True)
            except Exception as e:
                return handle_fatal_error(
                    t("err_trash_create", path=trash_dir, err_type=type(e).__name__, err_msg=str(e)),
                    cfg,
                    is_portable
                )

    # Geschützte Pfade festlegen, die niemals berührt werden dürfen
    protected_paths = [norm_tgt, os.path.normcase(os.path.abspath(DBP_DIR))]
    if trash_dir:
        protected_paths.append(os.path.normcase(os.path.abspath(trash_dir)))

    ext_list = []
    for e in extensions_str.split(","):
        e = e.strip().lower()
        if e:
            if not e.startswith("."):
                e = "." + e
            ext_list.append(e)

    log = []
    moved_count = 0
    smart_count = 0
    trashed_count = 0
    deleted_count = 0
    folders_cleaned = 0

    own_exe = os.path.abspath(sys.executable).lower() if getattr(sys, "frozen", False) else os.path.abspath(sys.argv[0]).lower()

    # 1. Dateisammlung (Rekursiv oder flach)
    files_to_process = []
    subdirs_encountered = []

    try:
        if include_subfolders:
            for root, dirs, files in os.walk(source, topdown=True):
                # Verhindern, dass in geschützte Ordner (z.B. Target im Source oder DBP_Dir) hinabgestiegen wird
                dirs[:] = [
                    d for d in dirs
                    if not any(is_same_or_subpath(os.path.join(root, d), p) for p in protected_paths)
                ]
                
                norm_root = os.path.normcase(os.path.abspath(root))
                if norm_root != norm_src:
                    subdirs_encountered.append(root)

                for f in files:
                    full_p = os.path.join(root, f)
                    if os.path.abspath(full_p).lower() == own_exe:
                        continue
                    files_to_process.append(full_p)
        else:
            for item in os.listdir(source):
                full_p = os.path.join(source, item)
                if os.path.abspath(full_p).lower() == own_exe:
                    continue
                if any(is_same_or_subpath(full_p, p) for p in protected_paths):
                    continue
                if os.path.isfile(full_p):
                    files_to_process.append(full_p)
                elif os.path.isdir(full_p):
                    subdirs_encountered.append(full_p)
    except Exception as e:
        return handle_fatal_error(
            t("err_src_access", path=source, err_type=type(e).__name__, err_msg=str(e)),
            cfg,
            is_portable
        )

    # 2. Dateien verarbeiten
    for file_path in files_to_process:
        filename = os.path.basename(file_path)
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        # A) Wichtige Bedingung: Treffer bei den konfigurierten Dateiendungen
        if ext in ext_list:
            try:
                target_path = get_unique_path(target, filename)
                shutil.move(file_path, target_path)
                log.append(f"{t('log_archive')} {filename} -> {os.path.basename(target_path)}")
                moved_count += 1
            except Exception as e:
                log.append(f"{t('log_error_arch')} '{filename}': [{type(e).__name__}] {e}")
            continue

        # B) Smart Trash Prüfung (falls aktiviert)
        if smart_trash_enabled:
            is_important, reason, is_active = evaluate_file_importance(file_path, protect_recent_hours)
            
            if is_active:
                log.append(f"{t('log_in_progress_skipped')} {filename}")
                continue

            if is_important:
                try:
                    target_path = get_unique_path(target, filename)
                    shutil.move(file_path, target_path)
                    log.append(f"{t('log_smart_archive', reason=reason)} {filename} -> {os.path.basename(target_path)}")
                    moved_count += 1
                    smart_count += 1
                except Exception as e:
                    log.append(f"{t('log_error_arch')} '{filename}': [{type(e).__name__}] {e}")
                continue

        # C) Nicht passend -> In Papierkorb oder Portable-Löschung
        if is_portable:
            try:
                safe_remove_file(file_path)
                log.append(f"{t('log_deleted_direct')} {filename}")
                deleted_count += 1
            except Exception as e:
                log.append(f"{t('log_error_delete')} '{filename}': [{type(e).__name__}] {e}")
        else:
            try:
                trash_path = get_unique_path(trash_dir, filename)
                shutil.move(file_path, trash_path)
                try:
                    os.utime(trash_path, None)
                except Exception:
                    pass
                log.append(f"{t('log_trash')} {filename} -> {os.path.basename(trash_path)}")
                trashed_count += 1
            except Exception as e:
                log.append(f"{t('log_error_trash')} '{filename}' (Ziel: '{trash_dir}'): [{type(e).__name__}] {e}")

    # 3. Unterordner behandeln & aufräumen ("unterordner findet und diese mit löscht")
    if clean_empty_folders and subdirs_encountered:
        # Von tief nach hoch sortieren (längste Pfade zuerst), um leere Kinder vor Eltern zu entfernen
        sorted_subdirs = sorted(subdirs_encountered, key=lambda p: len(p), reverse=True)
        for sdir in sorted_subdirs:
            if not os.path.exists(sdir) or not os.path.isdir(sdir):
                continue
            if any(is_same_or_subpath(sdir, p) for p in protected_paths):
                continue

            try:
                # Prüfen, ob der Ordner nun leer ist
                remaining = os.listdir(sdir)
                if not remaining:
                    try:
                        os.rmdir(sdir)
                        log.append(f"{t('log_folder_deleted')} {os.path.relpath(sdir, source)}")
                        folders_cleaned += 1
                    except Exception as e:
                        log.append(f"{t('log_error_folder')} '{sdir}': [{type(e).__name__}] {e}")
                elif not include_subfolders:
                    # Wenn Unterordner nicht rekursiv gescannt wurden, aber der Ordner selbst verschoben/gelöscht werden soll
                    if is_portable:
                        safe_rmtree(sdir)
                        log.append(f"{t('log_deleted_direct')} [Folder] {os.path.basename(sdir)}")
                        folders_cleaned += 1
                    else:
                        trash_sub_path = get_unique_path(trash_dir, os.path.basename(sdir))
                        shutil.move(sdir, trash_sub_path)
                        try:
                            os.utime(trash_sub_path, None)
                        except Exception:
                            pass
                        log.append(f"{t('log_folder_trash')} {os.path.basename(sdir)}")
                        folders_cleaned += 1
            except Exception as e:
                log.append(f"{t('log_error_folder')} '{sdir}': [{type(e).__name__}] {e}")

    # 4. Alten Papierkorb (>= 7 Tage) aufräumen
    if not is_portable and trash_dir:
        trash_logs = process_trash(trash_dir)
        log.extend(trash_logs)

    # 5. Zusammenfassung protokollieren
    if is_portable:
        summary = t("log_summary_portable", moved=moved_count, deleted=deleted_count, folders=folders_cleaned)
    else:
        summary = t("log_summary", moved=moved_count, smart_count=smart_count, trashed=trashed_count, folders=folders_cleaned)
    log.append(summary)

    if not is_portable:
        write_log(log, cfg)
        cfg["last_run_cleanup"] = datetime.date.today().strftime("%Y-%m-%d")
        save_config(cfg)

    return log
