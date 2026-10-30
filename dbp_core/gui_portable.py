"""
Portable Mode GUI for DBP Cleaner.
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from .i18n import t, set_language
from .config import load_config, save_config
from .system import resource_path, uninstall_application
from .cleaner import perform_cleanup

def run_portable_gui(initial_values=None):
    cfg = load_config()
    root = tk.Tk()
    root.title(t("title_portable"))

    try:
        root.iconbitmap(resource_path("besen.ico"))
    except Exception:
        pass

    root.geometry("560x560")
    root.minsize(500, 480)

    # Menüleiste
    menubar = tk.Menu(root)
    optmenu = tk.Menu(menubar, tearoff=0)

    from .gui_config import run_config_gui
    optmenu.add_command(label=t("menu_config"), command=lambda: [root.destroy(), run_config_gui()])

    lang_menu = tk.Menu(optmenu, tearoff=0)

    def change_lang(new_lang):
        cfg["language"] = new_lang
        set_language(new_lang)
        save_config(cfg)
        current_vals = {
            "source_dir": src_var.get(),
            "target_dir": tgt_var.get(),
            "extensions": ext_var.get(),
            "smart_trash": smart_trash_var.get(),
            "include_subfolders": subfolders_var.get()
        }
        root.destroy()
        run_portable_gui(current_vals)

    lang_menu.add_command(label="English", command=lambda: change_lang("English"))
    lang_menu.add_command(label="Deutsch", command=lambda: change_lang("Deutsch"))

    optmenu.add_cascade(label=t("menu_language"), menu=lang_menu)
    optmenu.add_separator()
    optmenu.add_command(label=t("menu_uninstall"), command=lambda: uninstall_application(root, lambda: cfg))
    menubar.add_cascade(label=t("menu_options"), menu=optmenu)
    root.config(menu=menubar)

    # Initialwerte bestimmen
    init_src = (initial_values or {}).get("source_dir", cfg.get("source_dir", ""))
    init_tgt = (initial_values or {}).get("target_dir", cfg.get("target_dir", ""))
    init_ext = (initial_values or {}).get("extensions", ".pdf, .docx, .zip")
    init_smart = (initial_values or {}).get("smart_trash", cfg.get("smart_trash", True))
    init_sub = (initial_values or {}).get("include_subfolders", cfg.get("include_subfolders", True))

    # Formular-Elemente
    ttk.Label(root, text=t("lbl_source")).pack(pady=(10, 0), padx=10, anchor="w")
    src_var = tk.StringVar(value=init_src)
    src_frame = ttk.Frame(root)
    src_frame.pack(fill="x", padx=10)
    ttk.Entry(src_frame, textvariable=src_var).pack(side="left", fill="x", expand=True)
    ttk.Button(src_frame, text=t("btn_browse"), command=lambda: src_var.set(filedialog.askdirectory())).pack(side="right", padx=(5, 0))

    ttk.Label(root, text=t("lbl_target")).pack(pady=(10, 0), padx=10, anchor="w")
    tgt_var = tk.StringVar(value=init_tgt)
    tgt_frame = ttk.Frame(root)
    tgt_frame.pack(fill="x", padx=10)
    ttk.Entry(tgt_frame, textvariable=tgt_var).pack(side="left", fill="x", expand=True)
    ttk.Button(tgt_frame, text=t("btn_browse"), command=lambda: tgt_var.set(filedialog.askdirectory())).pack(side="right", padx=(5, 0))

    ttk.Label(root, text=t("lbl_exts")).pack(pady=(10, 0), padx=10, anchor="w")
    ext_var = tk.StringVar(value=init_ext)
    ttk.Entry(root, textvariable=ext_var).pack(fill="x", padx=10)

    # Optionen: Smart Trash & Unterordner
    opt_frame = ttk.Frame(root)
    opt_frame.pack(fill="x", padx=10, pady=5)
    smart_trash_var = tk.BooleanVar(value=init_smart)
    ttk.Checkbutton(opt_frame, text=t("chk_smart_trash"), variable=smart_trash_var).pack(anchor="w")
    subfolders_var = tk.BooleanVar(value=init_sub)
    ttk.Checkbutton(opt_frame, text=t("chk_subfolders"), variable=subfolders_var).pack(anchor="w")

    # Log-Ausgabebereich mit Scrollbar
    log_frame = ttk.Frame(root)
    log_frame.pack(fill="both", expand=True, padx=10, pady=5)
    scrollbar = ttk.Scrollbar(log_frame)
    scrollbar.pack(side="right", fill="y")
    log_text = tk.Text(log_frame, height=12, yscrollcommand=scrollbar.set)
    log_text.pack(side="left", fill="both", expand=True)
    scrollbar.config(command=log_text.yview)

    def execute():
        log_text.delete(1.0, tk.END)
        if not src_var.get() or not tgt_var.get():
            messagebox.showwarning(t("msg_error_title"), t("msg_error_dirs"))
            return

        if os.path.normcase(os.path.abspath(src_var.get())) == os.path.normcase(os.path.abspath(tgt_var.get())):
            messagebox.showerror(t("msg_error_title"), t("msg_error_same_dirs"))
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
            "extensions": ext_var.get(),
            "smart_trash": smart_trash_var.get(),
            "include_subfolders": subfolders_var.get(),
            "clean_empty_folders": True,
            "protect_recent_hours": cfg.get("protect_recent_hours", 24)
        }

        result_log = perform_cleanup(temp_config, is_portable=True)
        for line in result_log:
            log_text.insert(tk.END, line + "\n")
        log_text.see(tk.END)

    ttk.Button(root, text=t("btn_execute"), command=execute).pack(pady=10)
    root.mainloop()
