"""
Configuration management for DBP Cleaner.
"""

import os
import json
import tempfile
from .constants import DBP_DIR, CONFIG_FILE, DEFAULT_CONFIG, LOG_SIZE_BYTES
from .i18n import set_language

def ensure_dbp_dir():
    """Stellt sicher, dass das Anwendungsdatenverzeichnis existiert."""
    if not os.path.exists(DBP_DIR):
        os.makedirs(DBP_DIR, exist_ok=True)

def load_config():
    """Lädt die Konfigurationsdatei oder gibt Standardwerte zurück."""
    if not os.path.exists(CONFIG_FILE):
        cfg = DEFAULT_CONFIG.copy()
        set_language(cfg.get("language", "English"))
        return cfg

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            c = json.load(f)

        # Abwärtskompatibilität für alte Intervallbezeichnungen
        if c.get("interval") == "Bei jedem Start": c["interval"] = "startup"
        if c.get("interval") == "Täglich": c["interval"] = "daily"
        if c.get("interval") == "Wöchentlich": c["interval"] = "weekly"
        if c.get("interval") == "Monatlich": c["interval"] = "monthly"

        if str(c.get("max_log_size")) not in LOG_SIZE_BYTES:
            c["max_log_size"] = "0.5"

        for k, v in DEFAULT_CONFIG.items():
            if k not in c:
                c[k] = v

        set_language(c.get("language", "English"))
        return c
    except Exception:
        cfg = DEFAULT_CONFIG.copy()
        set_language(cfg.get("language", "English"))
        return cfg

def save_config(cfg):
    """Speichert die Konfiguration atomar ab, um Dateibeschädigungen zu verhindern."""
    ensure_dbp_dir()
    set_language(cfg.get("language", "English"))
    
    # Atomares Schreiben via Temp-Datei
    temp_file = os.path.join(DBP_DIR, f"config.tmp.{os.getpid()}")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
        os.replace(temp_file, CONFIG_FILE)
    except Exception:
        # Fallback falls os.replace fehlschlägt
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4, ensure_ascii=False)
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass
