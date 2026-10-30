# DBP Cleaner (Download Bereinigungs Programm)

**DBP Cleaner** is a versatile and lightweight utility tool written in Python with a graphical user interface (Tkinter). It helps you keep your download or workspace folders organized by automatically archiving specific file types while safely moving or cleaning up unneeded files.

## Features

* **Automated Cleanup**: Move desired files (e.g., documents, images, archives) to a secure target archive directory.

* **Smart Trash & Intelligent Detection**:
  * Files matching your specified extensions are safely moved to the target directory.
  * **Intelligent File Recognition**: In addition to fixed extensions, Smart Trash analyzes candidate files for important keywords (e.g., invoices, receipts, tax documents, certificates, contracts), critical file types, and recent grace-period downloads to prevent accidental trashing of important documents.
  * **Active Download Protection**: In-progress downloads (`.crdownload`, `.part`, `.download`, Office lock files) are automatically recognized and protected from premature deletion or movement.
  * Other files are moved to a temporary trash folder (`DBP_Trash`) within the target directory, where they are automatically deleted after 7 days.

* **Recursive Subfolder Scanning & Cleaning**:
  * Scans both the root source directory and its subfolders recursively.
  * Extracted files matching your archive extensions or Smart Trash rules are archived to the target folder.
  * Remaining unneeded files are moved to trash (or deleted in portable mode).
  * Cleans up and removes empty subfolders after processing.
  * Built-in safety boundary protections ensure nested target/trash directories are never mistakenly deleted.

* **Portable Mode**:
  * Lets you run quick, custom cleanups where matching and important files are archived, but **all other files are permanently and immediately deleted** (skipping the trash).

* **Direct Execution from GUI**:
  * Instantly trigger a full cleanup run with trash retention directly from the main Configuration GUI ("Execute Cleanup Now / Jetzt bereinigen").

* **Flexible Scheduling**:
  * Run checks at *Every startup*, *Daily*, *Weekly*, or *Monthly*.

* **Background Autostart (Windows)**:
  * Option to quietly run in the background on PC startup via Windows Task/VBS integration (with full UTF-8/BOM character encoding support).

* **Multilingual Support**:
  * Fully localized in **English** and **Deutsch** (German).

* **Complete System Integration & Uninstaller**:
  * Registers start menu shortcuts, Windows system tray notifications, and clean uninstallation entries (compatible with standard Windows apps and Revo Uninstaller).

* **Modular Architecture**:
  * Cleanly structured under the `dbp_core` package (`constants`, `config`, `i18n`, `smart_trash`, `cleaner`, `system`, `gui_config`, `gui_portable`).

## System Resource Usage

DBP Cleaner is engineered to be exceptionally lightweight and respectful of your hardware resources:

* **CPU and RAM Usage After Execution ($0\%$)**: 
  When the program is triggered via Autostart (or run manually) to perform its cleanup routine, it processes the folders and **terminates itself immediately** upon completion. Consequently, resource consumption drops to absolute **$0\%$** ($0\text{ CPU}$, $0\text{ RAM}$ overhead) as no background daemon or persistent service stays active in the system tray. 

* **Active Footprint**: 
  Resource consumption only occurs briefly during active GUI sessions or during the split second the background cleanup script runs. When idle or closed, it utilizes $0\text{ MB}$ of RAM and $0\%$ CPU.

* **Storage Footprint**: Disk usage is strictly limited to your user-defined target archives, the local configuration JSON, and a managed rolling log file (which automatically enforces size limits from $0.5\text{ MB}$ up to $10\text{ MB}$ or unlimited).

## Requirements

* **Python 3.x** (if running from source) or the compiled Windows `.exe`.

* **Operating System**: Primarily designed for **Windows** (uses Win32 registry, VBS scripts, and Windows Toast notifications), with basic fallback compatibility.

## Usage

You can run the script using command-line arguments or simply by executing it directly (which opens the configuration GUI by default):

```
python dbp_cleaner.py
```

### Command-Line Arguments

* `-gui`: Opens the main configuration panel.

* `-portable`: Opens the portable cleanup mode.

* `-autostart`: Executes the background scheduled cleanup based on your configured interval and terminates right after.

* `-uninstall`: Completely uninstalls the program, removing all configurations, local logs, and registry entries.

## Configuration

All configurations, logs, and state history are automatically stored locally inside:

* `%APPDATA%\DBP_Cleaner` (on Windows)

You can easily adjust:

* **Source Folder**: The directory you want to monitor and clean (e.g., your *Downloads* folder).

* **Target Folder**: The archive destination where important files are stored.

* **Extensions**: Comma-separated file extensions to keep (e.g., `.pdf, .docx, .xlsx, .zip`).

* **Smart Trash**: Enable or disable intelligent detection of important files and documents.

* **Subfolder Cleaning**: Enable recursive scanning and empty folder cleanup.

* **Interval & Max Log Size**: Tailor how often cleanups run and manage log file rotation limits.

## License

This project is provided as-is under open utility terms. Feel free to modify and adapt it to your workflow needs.
