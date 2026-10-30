"""
Command-Line Interface and Main Entry Point for DBP Cleaner.
"""

import argparse
from .config import load_config
from .cleaner import check_interval, perform_cleanup
from .system import uninstall_application
from .gui_config import run_config_gui
from .gui_portable import run_portable_gui

def main():
    parser = argparse.ArgumentParser(description="Download Bereinigungs Programm (DBP)")
    parser.add_argument("-gui", action="store_true", help="Open Configuration GUI")
    parser.add_argument("-portable", action="store_true", help="Open Portable Mode")
    parser.add_argument("-autostart", action="store_true", help="Run background cleanup via Autostart")
    parser.add_argument("-uninstall", action="store_true", help="Completely uninstall DBP Cleaner")
    args = parser.parse_args()

    config = load_config()

    if args.uninstall:
        uninstall_application(config=config)
    elif args.portable:
        run_portable_gui()
    elif args.autostart:
        src = config.get("source_dir", "").strip()
        tgt = config.get("target_dir", "").strip()
        if src and tgt:
            interval = config.get("interval", "startup")
            last_run = config.get("last_run_cleanup", "")
            if check_interval(interval, last_run):
                perform_cleanup(config, is_portable=False)
    else:
        # Standard bei normalem Doppelklick auf die .exe (oder -gui): Konfigurationsmenü öffnen
        run_config_gui()

if __name__ == "__main__":
    main()
