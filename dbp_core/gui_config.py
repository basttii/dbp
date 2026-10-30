"""
Main Configuration GUI for DBP Cleaner.
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from .constants import DBP_DIR, LOG_FILE
from .i18n import t, set_language
from .config import load_config, save_config
from .system import (
    resource_path, register_system_integration,
    setup_autostart, uninstall_application
)
from .cleaner import perform_cleanup, enforce_log_size

def open_logs():
    """Öffnet die Logdatei im Standard-Texteditor."""
    if os.path.exists(LOG_FILE):
        if sys.platform == "win32":
            os.startfile(LOG_FILE)
        else:
            import subprocess
            subprocess.Popen(["xdg-open", LOG_FILE])
    else:
        messagebox.showinfo(t("title_logs"), t("msg_no_logs"))

def run_config_gui(initial_values=None):
    cfg = load_config()
    register_system_integration()

    root = tk.Tk()
    root.title(t("title_config"))

    try:
        root.iconbitmap(resource_path("besen.ico"))
    except Exception:
        pass

    root.geometry("580x600")
    root.minsize(520, 560)

    # Menüleiste
    menubar = tk.Menu(root)
    filemenu = tk.Menu(menubar, tearoff=0)

    from .gui_portable import run_portable_gui
    filemenu.add_command(label=t("menu_portable"), command=lambda: [root.destroy(), run_portable_gui()])

    lang_menu = tk.Menu(filemenu, tearoff=0)

    def change_lang(new_lang):
        cfg["language"] = new_lang
        set_language(new_lang)
        save_config(cfg)
        current_vals = {
            "source_dir": src_var.get(),
            "target_dir": tgt_var.get(),
            "extensions": ext_var.get(),
            "interval": inverse_interval_map.get(interval_var.get(), "startup"),
            "max_log_size": inverse_log_size_map.get(log_size_var.get(), "0.5"),
            "autostart": autostart_var.get(),
            "smart_trash": smart_trash_var.get(),
            "include_subfolders": subfolders_var.get(),
            "clean_empty_folders": clean_empty_var.get()
        }
        root.destroy()
        run_config_gui(current_vals)

    lang_menu.add_command(label="English", command=lambda: change_lang("English"))
    lang_menu.add_command(label="Deutsch", command=lambda: change_lang("Deutsch"))

    filemenu.add_cascade(label=t("menu_language"), menu=lang_menu)
    filemenu.add_separator()
    filemenu.add_command(label=t("menu_uninstall"), command=lambda: uninstall_application(root, lambda: cfg))
    menubar.add_cascade(label=t("menu_options"), menu=filemenu)
    root.config(menu=menubar)

    # Initialwerte bestimmen
    init_src = (initial_values or {}).get("source_dir", cfg.get("source_dir", ""))
    init_tgt = (initial_values or {}).get("target_dir", cfg.get("target_dir", ""))
    init_ext = (initial_values or {}).get("extensions", cfg.get("extensions", ".pdf, .docx, .xlsx, .jpg, .png, .zip"))
    init_interval = (initial_values or {}).get("interval", cfg.get("interval", "startup"))
    init_size = str((initial_values or {}).get("max_log_size", cfg.get("max_log_size", "0.5")))
    init_autostart = (initial_values or {}).get("autostart", cfg.get("autostart", False))
    init_smart = (initial_values or {}).get("smart_trash", cfg.get("smart_trash", True))
    init_sub = (initial_values or {}).get("include_subfolders", cfg.get("include_subfolders", True))
    init_clean_empty = (initial_values or {}).get("clean_empty_folders", cfg.get("clean_empty_folders", True))

    # Grid Layout
    current_row = 0

    # 1. Quellordner
    ttk.Label(root, text=t("lbl_source")).grid(row=current_row, column=0, padx=12, pady=6, sticky="w")
    src_var = tk.StringVar(value=init_src)
    ttk.Entry(root, textvariable=src_var, width=32).grid(row=current_row, column=1, padx=5, sticky="we")
    ttk.Button(root, text=t("btn_browse"), command=lambda: src_var.set(filedialog.askdirectory())).grid(row=current_row, column=2, padx=10, pady=6)
    current_row += 1

    # 2. Zielordner
    ttk.Label(root, text=t("lbl_target")).grid(row=current_row, column=0, padx=12, pady=6, sticky="w")
    tgt_var = tk.StringVar(value=init_tgt)
    ttk.Entry(root, textvariable=tgt_var, width=32).grid(row=current_row, column=1, padx=5, sticky="we")
    ttk.Button(root, text=t("btn_browse"), command=lambda: tgt_var.set(filedialog.askdirectory())).grid(row=current_row, column=2, padx=10, pady=6)
    current_row += 1

    # 3. Dateiendungen
    ttk.Label(root, text=t("lbl_exts")).grid(row=current_row, column=0, padx=12, pady=6, sticky="w")
    ext_var = tk.StringVar(value=init_ext)
    ttk.Entry(root, textvariable=ext_var, width=32).grid(row=current_row, column=1, columnspan=2, padx=5, sticky="we")
    current_row += 1

    # 4. Intervall
    ttk.Label(root, text=t("lbl_interval")).grid(row=current_row, column=0, padx=12, pady=6, sticky="w")
    interval_map = {
        "startup": t("int_startup"),
        "daily": t("int_daily"),
        "weekly": t("int_weekly"),
        "monthly": t("int_monthly")
    }
    inverse_interval_map = {v: k for k, v in interval_map.items()}
    interval_var = tk.StringVar(value=interval_map.get(init_interval, interval_map["startup"]))
    ttk.Combobox(
        root,
        textvariable=interval_var,
        values=list(interval_map.values()),
        state="readonly",
        width=30
    ).grid(row=current_row, column=1, columnspan=2, padx=5, sticky="w")
    current_row += 1

    # 5. Maximale Log-Größe
    ttk.Label(root, text=t("lbl_log_size")).grid(row=current_row, column=0, padx=12, pady=6, sticky="w")
    log_size_map = {
        "0.5": t("size_0_5"),
        "1": t("size_1"),
        "5": t("size_5"),
        "10": t("size_10"),
        "unlimited": t("size_unlimited")
    }
    inverse_log_size_map = {v: k for k, v in log_size_map.items()}
    log_size_var = tk.StringVar(value=log_size_map.get(init_size, log_size_map["0.5"]))
    ttk.Combobox(
        root,
        textvariable=log_size_var,
        values=list(log_size_map.values()),
        state="readonly",
        width=30
    ).grid(row=current_row, column=1, columnspan=2, padx=5, sticky="w")
    current_row += 1

    # Trennlinie
    ttk.Separator(root, orient="horizontal").grid(row=current_row, column=0, columnspan=3, sticky="we", padx=10, pady=8)
    current_row += 1

    # 6. Checkboxen für Optionen
    smart_trash_var = tk.BooleanVar(value=init_smart)
    ttk.Checkbutton(
        root,
        text=t("chk_smart_trash"),
        variable=smart_trash_var
    ).grid(row=current_row, column=0, columnspan=3, padx=12, pady=4, sticky="w")
    current_row += 1

    subfolders_var = tk.BooleanVar(value=init_sub)
    ttk.Checkbutton(
        root,
        text=t("chk_subfolders"),
        variable=subfolders_var
    ).grid(row=current_row, column=0, columnspan=3, padx=12, pady=4, sticky="w")
    current_row += 1

    clean_empty_var = tk.BooleanVar(value=init_clean_empty)
    ttk.Checkbutton(
        root,
        text=t("chk_clean_empty_folders"),
        variable=clean_empty_var
    ).grid(row=current_row, column=0, columnspan=3, padx=12, pady=4, sticky="w")
    current_row += 1

    autostart_var = tk.BooleanVar(value=init_autostart)
    ttk.Checkbutton(
        root,
        text=t("chk_autostart"),
        variable=autostart_var
    ).grid(row=current_row, column=0, columnspan=3, padx=12, pady=4, sticky="w")
    current_row += 1

    # Trennlinie
    ttk.Separator(root, orient="horizontal").grid(row=current_row, column=0, columnspan=3, sticky="we", padx=10, pady=8)
    current_row += 1

    def apply_inputs():
        cfg["source_dir"] = src_var.get().strip()
        cfg["target_dir"] = tgt_var.get().strip()
        cfg["extensions"] = ext_var.get().strip()
        cfg["interval"] = inverse_interval_map.get(interval_var.get(), "startup")
        cfg["max_log_size"] = inverse_log_size_map.get(log_size_var.get(), "0.5")
        cfg["autostart"] = autostart_var.get()
        cfg["smart_trash"] = smart_trash_var.get()
        cfg["include_subfolders"] = subfolders_var.get()
        cfg["clean_empty_folders"] = clean_empty_var.get()

    def execute_normal():
        apply_inputs()
        if not cfg["source_dir"] or not cfg["target_dir"]:
            messagebox.showwarning(t("msg_error_title"), t("msg_error_dirs"))
            return

        if os.path.normcase(os.path.abspath(cfg["source_dir"])) == os.path.normcase(os.path.abspath(cfg["target_dir"])):
            messagebox.showerror(t("msg_error_title"), t("msg_error_same_dirs"))
            return

        save_config(cfg)
        logs = perform_cleanup(cfg, is_portable=False)
        summary = logs[-1] if logs else ""
        messagebox.showinfo(
            t("msg_execute_done_title"),
            t("msg_execute_done_text", summary=summary)
        )

    def save_and_close():
        apply_inputs()
        save_config(cfg)
        register_system_integration()
        enforce_log_size(cfg["max_log_size"])
        setup_autostart(autostart_var.get())

        messagebox.showinfo(t("msg_saved_title"), t("msg_saved_text", path=DBP_DIR))
        root.destroy()

    # Buttons
    btn_frame = ttk.Frame(root)
    btn_frame.grid(row=current_row, column=0, columnspan=3, pady=10)

    ttk.Button(btn_frame, text=t("btn_execute_normal"), command=execute_normal).pack(fill="x", pady=3)
    ttk.Button(btn_frame, text=t("btn_save"), command=save_and_close).pack(fill="x", pady=3)
    ttk.Button(btn_frame, text=t("btn_logs"), command=open_logs).pack(fill="x", pady=3)
    ttk.Button(btn_frame, text=t("btn_uninstall"), command=lambda: uninstall_application(root, lambda: cfg)).pack(fill="x", pady=(8, 3))

    root.mainloop()
