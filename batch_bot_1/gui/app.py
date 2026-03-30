# ─────────────────────────────────────────────────────────────
#  gui/app.py  –  Tkinter control panel for Batch Bot
#
#  Layout
#  ┌──────────────────────────────────────────────────┐
#  │  File Picker  (top bar)                          │
#  ├──────────────────────────────────────────────────┤
#  │  Data Preview  (treeview table)                  │
#  ├──────────────────────────────────────────────────┤
#  │  Progress bar + counter                          │
#  ├──────────────────────────────────────────────────┤
#  │  Controls  [Start Batch]  [Pause]  [Stop]        │
#  ├──────────────────────────────────────────────────┤
#  │  Live log (scrollable text)                      │
#  └──────────────────────────────────────────────────┘
# ─────────────────────────────────────────────────────────────

import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

import config
from bot.excel_handler import ExcelHandler
from bot.selenium_bot  import BatchBot


# ─── Colour palette ───────────────────────────────────────────
BG          = "#1e1e2e"
SURFACE     = "#2a2a3e"
ACCENT      = "#7c6af7"
ACCENT_DARK = "#5a4fd4"
TEXT        = "#e0e0f0"
TEXT_DIM    = "#9898b0"
SUCCESS     = "#4caf82"
DANGER      = "#e06c75"
WARNING     = "#e5c07b"
BORDER      = "#3a3a54"


class BatchBotApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("Batch Automation Bot")
        self.geometry("980x720")
        self.minsize(800, 600)
        self.configure(bg=BG)

        # ── State ──────────────────────────────────────────
        self._file_path   : str | None   = None
        self._excel       : ExcelHandler | None = None
        self._bot         : BatchBot | None     = None
        self._bot_thread  : threading.Thread | None = None
        self._paused      : bool = False

        # ── Build UI ───────────────────────────────────────
        self._build_header()
        self._build_file_bar()
        self._build_table()
        self._build_progress()
        self._build_controls()
        self._build_log()

        self._set_controls_state("idle")

    # ══════════════════════════════════════════════════════════
    #  UI Construction
    # ══════════════════════════════════════════════════════════

    def _build_header(self):
        hdr = tk.Frame(self, bg=ACCENT, height=50)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(
            hdr, text="⚡  Batch Automation & Data Integration Bot",
            bg=ACCENT, fg="white",
            font=("Segoe UI", 14, "bold"), padx=16
        ).pack(side="left", pady=10)

    def _build_file_bar(self):
        bar = tk.Frame(self, bg=SURFACE, pady=10, padx=14)
        bar.pack(fill="x", padx=0, pady=(0, 2))

        tk.Label(bar, text="Excel / CSV File:", bg=SURFACE, fg=TEXT_DIM,
                 font=("Segoe UI", 10)).pack(side="left")

        self._file_label = tk.Label(
            bar, text="No file selected",
            bg=SURFACE, fg=TEXT_DIM, font=("Segoe UI", 10, "italic"),
            wraplength=560, anchor="w"
        )
        self._file_label.pack(side="left", padx=10, fill="x", expand=True)

        self._pick_btn = tk.Button(
            bar, text="Browse …", command=self._pick_file,
            bg=ACCENT, fg="white", relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=14, pady=4, cursor="hand2",
            activebackground=ACCENT_DARK, activeforeground="white"
        )
        self._pick_btn.pack(side="right", padx=(6, 0))

    def _build_table(self):
        frm = tk.Frame(self, bg=BG)
        frm.pack(fill="both", expand=True, padx=14, pady=(6, 0))

        tk.Label(frm, text="Data Preview", bg=BG, fg=TEXT_DIM,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")

        # Treeview
        tv_frame = tk.Frame(frm, bg=BORDER, bd=1, relief="flat")
        tv_frame.pack(fill="both", expand=True, pady=(4, 0))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Bot.Treeview",
                        background=SURFACE, foreground=TEXT,
                        rowheight=24, fieldbackground=SURFACE,
                        bordercolor=BORDER, borderwidth=0)
        style.configure("Bot.Treeview.Heading",
                        background=ACCENT_DARK, foreground="white",
                        font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Bot.Treeview", background=[("selected", ACCENT)])

        columns = (
            config.COL_FIRST_NAME, config.COL_LAST_NAME,
            config.COL_EMAIL, config.COL_PHONE_NUMBER,
            config.COL_PREFERRED_CONTACT, config.COL_HOW_LOCATED,
            config.COL_STATUS
        )
        self._tree = ttk.Treeview(tv_frame, columns=columns,
                                  show="headings", style="Bot.Treeview",
                                  height=10)

        col_widths = {
            config.COL_FIRST_NAME: 90,
            config.COL_LAST_NAME: 90,
            config.COL_EMAIL: 160,
            config.COL_PHONE_NUMBER: 100,
            config.COL_PREFERRED_CONTACT: 110,
            config.COL_HOW_LOCATED: 100,
            config.COL_STATUS: 120,
        }
        for col in columns:
            self._tree.heading(col, text=col)
            self._tree.column(col, width=col_widths.get(col, 100), anchor="w")

        v_scroll = ttk.Scrollbar(tv_frame, orient="vertical",
                                 command=self._tree.yview)
        h_scroll = ttk.Scrollbar(tv_frame, orient="horizontal",
                                 command=self._tree.xview)
        self._tree.configure(yscrollcommand=v_scroll.set,
                             xscrollcommand=h_scroll.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        tv_frame.rowconfigure(0, weight=1)
        tv_frame.columnconfigure(0, weight=1)

    def _build_progress(self):
        frm = tk.Frame(self, bg=BG, pady=6)
        frm.pack(fill="x", padx=14)

        self._progress_label = tk.Label(
            frm, text="Ready", bg=BG, fg=TEXT_DIM,
            font=("Segoe UI", 9)
        )
        self._progress_label.pack(anchor="w")

        style = ttk.Style()
        style.configure("Bot.Horizontal.TProgressbar",
                        troughcolor=SURFACE, background=ACCENT,
                        thickness=14)
        self._progress_bar = ttk.Progressbar(
            frm, style="Bot.Horizontal.TProgressbar",
            orient="horizontal", mode="determinate", length=400
        )
        self._progress_bar.pack(fill="x", pady=(2, 0))

    def _build_controls(self):
        frm = tk.Frame(self, bg=SURFACE, pady=10, padx=14)
        frm.pack(fill="x", pady=(6, 0))

        btn_cfg = dict(font=("Segoe UI", 11, "bold"), relief="flat",
                       padx=22, pady=6, cursor="hand2")

        self._start_btn = tk.Button(
            frm, text="▶  Start Batch", command=self._start,
            bg=SUCCESS, fg="white",
            activebackground="#3a9a6a", activeforeground="white",
            **btn_cfg
        )
        self._start_btn.pack(side="left", padx=(0, 8))

        self._pause_btn = tk.Button(
            frm, text="⏸  Pause", command=self._toggle_pause,
            bg=WARNING, fg="#1e1e2e",
            activebackground="#c8a060", activeforeground="#1e1e2e",
            **btn_cfg
        )
        self._pause_btn.pack(side="left", padx=(0, 8))

        self._stop_btn = tk.Button(
            frm, text="⏹  Stop", command=self._stop,
            bg=DANGER, fg="white",
            activebackground="#b85560", activeforeground="white",
            **btn_cfg
        )
        self._stop_btn.pack(side="left")

        self._continue_btn = tk.Button(
            frm, text="✅  Continue", command=self._continue_captcha,
            bg=SUCCESS, fg="white",
            activebackground="#3a9a6a", activeforeground="white",
            **btn_cfg
        )
        self._continue_btn.pack(side="left", padx=(8, 0))

        # Captcha mode indicator (right side)
        tk.Label(frm, text="Captcha mode: ", bg=SURFACE,
                 fg=TEXT_DIM, font=("Segoe UI", 9)).pack(side="right", padx=(0, 2))
        mode_color = {
            "demo": WARNING, "ocr": ACCENT, "api": SUCCESS
        }.get(config.CAPTCHA_MODE, TEXT)
        tk.Label(frm, text=config.CAPTCHA_MODE.upper(), bg=SURFACE,
                 fg=mode_color, font=("Segoe UI", 9, "bold")).pack(side="right")

    def _build_log(self):
        frm = tk.Frame(self, bg=BG)
        frm.pack(fill="both", expand=False, padx=14, pady=(6, 10))

        tk.Label(frm, text="Live Log", bg=BG, fg=TEXT_DIM,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")

        log_frame = tk.Frame(frm, bg=BORDER, bd=1, relief="flat")
        log_frame.pack(fill="both", expand=True, pady=(4, 0))

        self._log_text = tk.Text(
            log_frame, bg="#12121e", fg=TEXT,
            font=("Consolas", 9), height=9,
            state="disabled", wrap="word",
            insertbackground=TEXT, relief="flat",
            padx=8, pady=6
        )
        log_scroll = ttk.Scrollbar(log_frame, command=self._log_text.yview)
        self._log_text.configure(yscrollcommand=log_scroll.set)

        self._log_text.pack(side="left", fill="both", expand=True)
        log_scroll.pack(side="right", fill="y")

        # Tag colours for log
        self._log_text.tag_configure("success", foreground=SUCCESS)
        self._log_text.tag_configure("error",   foreground=DANGER)
        self._log_text.tag_configure("info",    foreground=ACCENT)
        self._log_text.tag_configure("warn",    foreground=WARNING)

    # ══════════════════════════════════════════════════════════
    #  File Handling
    # ══════════════════════════════════════════════════════════

    def _pick_file(self):
        path = filedialog.askopenfilename(
            title="Select Excel or CSV file",
            filetypes=[
                ("Excel files", "*.xlsx *.xls"),
                ("CSV files",   "*.csv"),
                ("All files",   "*.*"),
            ]
        )
        if not path:
            return

        try:
            self._excel     = ExcelHandler(path)
            self._file_path = path
            self._file_label.config(text=Path(path).name, fg=TEXT)
            self._populate_table()
            self._log_append(f"Loaded: {path}", "info")
            self._set_controls_state("ready")
        except Exception as exc:
            messagebox.showerror("File Error", str(exc))
            self._log_append(f"Error loading file: {exc}", "error")

    def _populate_table(self):
        """Refresh the treeview with current Excel data."""
        for row in self._tree.get_children():
            self._tree.delete(row)

        if self._excel is None:
            return

        records = self._excel.get_all_records()
        for rec in records:
            status = rec.get(config.COL_STATUS, "Pending")
            tag = (
                "success" if status == "Success"
                else "error" if "Failed" in str(status)
                else ""
            )
            self._tree.insert("", "end", values=(
                rec.get(config.COL_FIRST_NAME,        ""),
                rec.get(config.COL_LAST_NAME,         ""),
                rec.get(config.COL_EMAIL,             ""),
                rec.get(config.COL_PHONE_NUMBER,      ""),
                rec.get(config.COL_PREFERRED_CONTACT, ""),
                rec.get(config.COL_HOW_LOCATED,       ""),
                status,
            ), tags=(tag,))

        self._tree.tag_configure("success", foreground=SUCCESS)
        self._tree.tag_configure("error",   foreground=DANGER)

    # ══════════════════════════════════════════════════════════
    #  Bot Controls
    # ══════════════════════════════════════════════════════════

    def _start(self):
        if self._excel is None:
            messagebox.showwarning("No File", "Please select an Excel file first.")
            return

        # FIX #10: Guard against starting a second bot thread while
        # the first is still alive. This prevents race conditions on the
        # Excel file and driver instance when the user clicks Start twice.
        if self._bot_thread and self._bot_thread.is_alive():
            messagebox.showwarning(
                "Bot Running",
                "A batch is already running.\n"
                "Please stop it first before starting a new one."
            )
            return

        self._paused = False
        self._set_controls_state("running")
        self._log_append("─" * 55, "info")
        self._log_append("Batch started.", "info")

        self._bot = BatchBot(
            excel_handler     = self._excel,
            log_callback      = lambda msg: self.after(0, self._log_append, msg),
            progress_callback = lambda cur, total: self.after(0, self._update_progress, cur, total),
            done_callback     = lambda: self.after(0, self._on_bot_done),
        )

        self._bot_thread = threading.Thread(target=self._bot.run, daemon=True)
        self._bot_thread.start()

    def _toggle_pause(self):
        if self._bot is None:
            return

        if not self._paused:
            self._bot.pause()
            self._paused = True
            self._pause_btn.config(text="▶  Resume")
            self._log_append("Paused — will stop after current record.", "warn")
        else:
            self._bot.resume()
            self._paused = False
            self._pause_btn.config(text="⏸  Pause")
            self._log_append("Resumed.", "info")

    def _continue_captcha(self):
        if self._bot:
            self._bot.continue_captcha()
        # FIX #9: Disable the button immediately after click so it
        # cannot be double-clicked. It will be re-enabled automatically
        # when the next record enters captcha-wait state via _log_append.
        self._continue_btn.config(state="disabled")

    def _stop(self):
        if self._bot:
            self._bot.stop()
        self._set_controls_state("idle")
        self._log_append("Stop requested. Finishing current record …", "warn")

    def _on_bot_done(self):
        """Called (on main thread) when the bot thread finishes."""
        self._populate_table()   # refresh statuses
        self._set_controls_state("ready")
        self._progress_label.config(text="Batch complete.")
        self._log_append("─" * 55, "info")
        self._log_append("Batch finished. Check the table for results.", "success")

    # ══════════════════════════════════════════════════════════
    #  Progress & Log
    # ══════════════════════════════════════════════════════════

    def _update_progress(self, current: int, total: int):
        pct = int((current / total) * 100) if total else 0
        self._progress_bar["value"] = pct
        self._progress_label.config(
            text=f"Processing record {current} of {total}  ({pct}%)"
        )
        # FIX #11: Refresh the table EVERY time progress fires so that
        # status changes (written to df before this callback is triggered)
        # are always visible immediately in the GUI.
        self._populate_table()

        # FIX #9 (part 2): Reset the Continue button to disabled at the
        # start of each new record. _log_append will re-enable it if
        # the record enters captcha-wait mode.
        self._continue_btn.config(state="disabled")

    def _log_append(self, msg: str, tag: str = ""):
        self._log_text.configure(state="normal")
        # Detect tag from message content if not explicit
        if not tag:
            m = msg.lower()
            if "✅" in msg or "success" in m:
                tag = "success"
            elif "❌" in msg or "error" in m or "fail" in m:
                tag = "error"
            elif "warn" in m or "pausing" in m:
                tag = "warn"
            else:
                tag = "info"

        # Switch GUI to "captcha" state when the bot is waiting for manual solve
        if "manual captcha mode" in msg.lower():
            self._set_controls_state("captcha")
        # Switch back to running once the bot confirms it's continuing
        elif "captcha confirmed" in msg.lower():
            self._set_controls_state("running")

        self._log_text.insert("end", msg + "\n", tag)
        self._log_text.see("end")
        self._log_text.configure(state="disabled")

    # ══════════════════════════════════════════════════════════
    #  Button State Management
    # ══════════════════════════════════════════════════════════

    def _set_controls_state(self, state: str):
        """
        state: "idle"    → Start disabled, Pause disabled, Stop disabled, Continue disabled
               "ready"   → Start enabled,  Pause disabled, Stop disabled, Continue disabled
               "running" → Start disabled, Pause enabled,  Stop enabled,  Continue disabled
               "captcha" → Start disabled, Pause disabled, Stop enabled,  Continue enabled
        """
        s = state.lower()
        self._start_btn.config(   state="normal" if s == "ready"   else "disabled")
        self._pause_btn.config(   state="normal" if s == "running" else "disabled")
        self._stop_btn.config(    state="normal" if s in ("running", "captcha") else "disabled")
        self._continue_btn.config(state="normal" if s == "captcha" else "disabled")