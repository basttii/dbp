"""
Smart Trash Detection Engine for DBP Cleaner.

Intelligently detects important files that should NOT be blindly trashed,
identifies active in-progress downloads, and categorizes candidate files.
"""

import os
import re
import time

# Dateiendungen aktiver Downloads & temporärer Sperrdateien
IN_PROGRESS_EXTENSIONS = {
    ".crdownload",  # Chromium, Chrome, Edge, Brave, Opera
    ".part",        # Firefox
    ".download",    # Safari, diverse Download-Manager
    ".tmpdownload",
    ".unconfirmed"
}

# Signalwörter in Dateinamen für wichtige Dokumente (Rechnungen, Verträge, etc.)
IMPORTANT_KEYWORDS = [
    "rechnung", "invoice", "beleg", "kontoauszug", "steuer", "tax",
    "vertrag", "contract", "gehalt", "salary", "ticket", "boardingpass",
    "zertifikat", "certificate", "quittung", "receipt", "bestaetigung",
    "confirmation", "police", "ausweis", "statement", "kuendigung",
    "bestellung", "order", "versicherung", "meldebescheinigung",
    "entgelt", "finanzamt", "lohn", "abrechnung"
]

# Kategorien wichtiger Dateiendungen
IMPORTANT_EXTENSIONS = {
    # Dokumente & Texte
    ".pdf", ".doc", ".docx", ".odt", ".rtf", ".txt", ".md", ".pages", ".tex",
    ".epub", ".mobi", ".azw3", ".djvu",
    # Tabellen & Daten
    ".xls", ".xlsx", ".csv", ".tsv", ".ods", ".numbers", ".parquet",
    # Präsentationen
    ".ppt", ".pptx", ".odp", ".key",
    # Kreativ- und Projektdateien
    ".psd", ".ai", ".blend", ".prproj", ".aep", ".svg", ".raw", ".cr2", ".nef", ".dng",
    # Quellcode & Skripte
    ".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".json", ".sql",
    ".sh", ".ps1", ".c", ".cpp", ".h", ".hpp", ".cs", ".rs", ".go", ".java",
    ".kt", ".swift", ".rb", ".php", ".xml", ".yaml", ".yml",
    # Archive & Backups
    ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso", ".bak"
}

# Dateiendungen, die definitiv als Müll/Temp gelten
JUNK_EXTENSIONS = {
    ".tmp", ".temp", ".log", ".chk", ".old", ".dmp", ".crash", ".cache"
}

def is_in_progress_download(file_path):
    """
    Prüft, ob eine Datei ein derzeit laufender Download oder eine temporäre Lock-Datei ist.
    Darf niemals verschoben oder gelöscht werden!
    """
    base_name = os.path.basename(file_path).lower()
    
    # Office-Lock-Dateien (z.B. ~$Dokument.docx oder .~lock.Dokument.docx#)
    if base_name.startswith("~$") or base_name.startswith(".~lock"):
        return True

    _, ext = os.path.splitext(base_name)
    if ext in IN_PROGRESS_EXTENSIONS:
        return True

    return False

def is_system_metadata_file(file_path):
    """Prüft auf Windows- und macOS-Systemmetadaten."""
    base_name = os.path.basename(file_path).lower()
    return base_name in {"desktop.ini", "thumbs.db", ".ds_store"}

def evaluate_file_importance(file_path, protect_recent_hours=24):
    """
    Bewertet eine Datei anhand intelligenter Kriterien:
    Rückgabe: (is_important: bool, reason: str, is_active: bool)
    """
    if is_in_progress_download(file_path):
        return False, "Active Download", True

    if is_system_metadata_file(file_path):
        return False, "System Metadata", False

    filename = os.path.basename(file_path)
    name_lower = filename.lower()
    _, ext = os.path.splitext(name_lower)

    # 1. Bekannter temporärer Müll
    if ext in JUNK_EXTENSIONS:
        return False, "Known Junk Extension", False

    # 0-Byte Dateien ohne Inhalt (sofern nicht aktiv)
    try:
        if os.path.getsize(file_path) == 0:
            return False, "Empty File (0 Bytes)", False
    except OSError:
        pass

    # 2. Schlüsselwörter im Dateinamen prüfen (z.B. "Rechnung_2026.pdf")
    for kw in IMPORTANT_KEYWORDS:
        # Wortgrenzen-Suche für präzisere Treffer (z.B. "rechnung" in "Rechnung-123.pdf")
        if re.search(r'(?i)(?:^|[\W_])' + re.escape(kw) + r'(?:$|[\W_])', name_lower) or kw in name_lower:
            return True, f"Keyword '{kw}'", False

    # 3. Wichtige Dateitypen / Dokumente / Code / Medien
    if ext in IMPORTANT_EXTENSIONS:
        return True, f"Important Type ({ext})", False

    # 4. Gnadenfrist für sehr neue Dateien (z.B. in den letzten 24h heruntergeladen)
    if protect_recent_hours and protect_recent_hours > 0:
        try:
            mtime = os.path.getmtime(file_path)
            age_hours = (time.time() - mtime) / 3600.0
            if 0 <= age_hours < protect_recent_hours:
                return True, f"Recent Download (<{protect_recent_hours}h)", False
        except OSError:
            pass

    return False, "Standard Non-matching", False
