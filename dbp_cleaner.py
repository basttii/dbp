#!/usr/bin/env python3
"""
DBP Cleaner (Download Bereinigungs Programm)
Haupteinstiegspunkt für das Programm.
"""

import sys
from dbp_core.main import main
from dbp_core.cleaner import perform_cleanup, process_trash, check_interval, write_log
from dbp_core.config import load_config, save_config
from dbp_core.smart_trash import evaluate_file_importance
from dbp_core.system import uninstall_application
from dbp_core.gui_config import run_config_gui
from dbp_core.gui_portable import run_portable_gui

if __name__ == "__main__":
    main()
