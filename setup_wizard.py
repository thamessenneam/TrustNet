"""
TrustNet Setup Wizard
Run: python setup_wizard.py
"""

from __future__ import annotations

import os
import sys
import subprocess
import threading
import time
import tkinter as tk
from tkinter import ttk
from pathlib import Path

# ── Palette ───────────────────────────────────────────────────────────────────
GOLD    = "#bf9000"
WHITE   = "#faf9f6"
BLUE    = "#4a86e8"
BG      = "#1a1a1a"
SURFACE = "#252525"
BORDER  = "#333333"
SUBTEXT = "#888888"
RED     = "#c0392b"
GREEN   = "#27ae60"

FONT        = ("Cascadia Code", 10)
FONT_BOLD   = ("Cascadia Code", 10, "bold")
FONT_LARGE  = ("Cascadia Code", 20, "bold")
FONT_TITLE  = ("Cascadia Code", 13, "bold")
FONT_SMALL  = ("Cascadia Code", 9)
FONT_MONO   = ("Cascadia Code", 9)

WIN_W, WIN_H = 600, 480

# ── Helpers ───────────────────────────────────────────────────────────────────

def _center(win: tk.Tk) -> None:
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    win.geometry(f"{WIN_W}x{WIN_H}+{(sw-WIN_W)//2}+{(sh-WIN_H)//2}")


def _sep(parent: tk.Widget) -> None:
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=0, pady=0)


def _btn(parent, text, cmd, color=BLUE, width=14):
    return tk.Button(
        parent, text=text, command=cmd,
        font=FONT_BOLD, bg=color, fg=BG,
        relief="flat", padx=16, pady=8,
        width=width, cursor="hand2",
        activebackground=WHITE, activeforeground=BG,
    )


def _is_windows() -> bool: return sys.platform == "win32"
def _is_mac()     -> bool: return sys.platform == "darwin"
def _is_linux()   -> bool: return sys.platform.startswith("linux")


def _get_install_dir() -> Path:
    if _is_windows():
        return Path(os.environ.get("PROGRAMFILES", "C:\\Program Files")) / "TrustNet"
    elif _is_mac():
        return Path("/usr/local/bin")
    else:
        return Path("/usr/local/bin")


def _get_script_dir() -> Path:
    return Path(__file__).resolve().parent


# ── Wizard ────────────────────────────────────────────────────────────────────

class Wizard(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TrustNet Setup")
        self.geometry(f"{WIN_W}x{WIN_H}")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Install options
        self.opt_context  = tk.BooleanVar(value=True)
        self.opt_node     = tk.BooleanVar(value=True)
        self.opt_path     = tk.BooleanVar(value=True)
        self.install_dir  = tk.StringVar(value=str(_get_install_dir()))

        # Apply icon
        try:
            from trustnet.icon import apply_icon
            apply_icon(self)
        except Exception:
            pass

        self._pages: list[tk.Frame] = []
        self._current = 0

        self._build_header()
        self._build_content()
        self._build_footer()

        self._pages = [
            self._page_welcome(),
            self._page_options(),
            self._page_install(),
            self._page_done(),
        ]

        _center(self)
        self._show_page(0)

    # ── Layout skeleton ───────────────────────────────────────────────────────

    def _build_header(self) -> None:
        self._header = tk.Frame(self, bg=SURFACE, height=80)
        self._header.pack(fill="x")
        self._header.pack_propagate(False)

        left = tk.Frame(self._header, bg=SURFACE)
        left.pack(side="left", fill="both", expand=True, padx=24, pady=16)

        self._hdr_title = tk.Label(left, text="", font=FONT_LARGE,
                                   bg=SURFACE, fg=GOLD, anchor="w")
        self._hdr_title.pack(anchor="w")

        self._hdr_sub = tk.Label(left, text="", font=FONT_SMALL,
                                 bg=SURFACE, fg=SUBTEXT, anchor="w")
        self._hdr_sub.pack(anchor="w")

        # $:TN logo
        logo = tk.Frame(self._header, bg=SURFACE)
        logo.pack(side="right", padx=24)
        tk.Label(logo, text="$:", font=("Cascadia Code", 22, "bold"),
                 bg=SURFACE, fg=WHITE).pack(side="left")
        tk.Label(logo, text="TN", font=("Cascadia Code", 22, "bold"),
                 bg=SURFACE, fg=GOLD).pack(side="left")

        _sep(self)

    def _build_content(self) -> None:
        self._content = tk.Frame(self, bg=BG)
        self._content.pack(fill="both", expand=True)

    def _build_footer(self) -> None:
        _sep(self)
        foot = tk.Frame(self, bg=SURFACE, height=56)
        foot.pack(fill="x")
        foot.pack_propagate(False)

        self._btn_cancel = _btn(foot, "Cancel", self._on_close, RED, 10)
        self._btn_cancel.pack(side="left", padx=16, pady=10)

        self._btn_next = _btn(foot, "Next →", self._next, BLUE, 12)
        self._btn_next.pack(side="right", padx=16, pady=10)

        self._btn_back = _btn(foot, "← Back", self._back, SURFACE, 10)
        self._btn_back.configure(fg=WHITE, activebackground=BORDER)
        self._btn_back.pack(side="right", padx=4, pady=10)

        # Step dots
        self._dots_frame = tk.Frame(foot, bg=SURFACE)
        self._dots_frame.pack(side="right", padx=16)
        self._dots = []
        for _ in range(4):
            d = tk.Label(self._dots_frame, text="●", font=("Cascadia Code", 10),
                         bg=SURFACE, fg=BORDER)
            d.pack(side="left", padx=2)
            self._dots.append(d)

    # ── Pages ─────────────────────────────────────────────────────────────────

    def _page_welcome(self) -> tk.Frame:
        f = tk.Frame(self._content, bg=BG)

        tk.Label(f, text="Welcome to TrustNet", font=FONT_LARGE,
                 bg=BG, fg=GOLD).pack(pady=(36, 8))
        tk.Label(f, text="Decentralized cryptographic file & package trust network.",
                 font=FONT, bg=BG, fg=WHITE).pack()

        tk.Frame(f, bg=BORDER, height=1).pack(fill="x", padx=40, pady=24)

        items = [
            ("Sign",    "Cryptographically sign any file or folder"),
            ("Verify",  "Detect if files were tampered with"),
            ("Network", "P2P network of independent witnesses"),
            ("Menus",   "Right-click integration in your file manager"),
        ]
        for icon, desc in items:
            row = tk.Frame(f, bg=BG)
            row.pack(fill="x", padx=48, pady=4)
            tk.Label(row, text=icon, font=FONT_BOLD, bg=BG,
                     fg=GOLD, width=10, anchor="w").pack(side="left")
            tk.Label(row, text=desc, font=FONT_SMALL, bg=BG,
                     fg=WHITE, anchor="w").pack(side="left")

        tk.Frame(f, bg=BORDER, height=1).pack(fill="x", padx=40, pady=24)

        tk.Label(f, text="Click Next to begin installation.",
                 font=FONT_SMALL, bg=BG, fg=SUBTEXT).pack()

        return f

    def _page_options(self) -> tk.Frame:
        f = tk.Frame(self._content, bg=BG)

        tk.Label(f, text="Installation Options", font=FONT_TITLE,
                 bg=BG, fg=WHITE).pack(pady=(14, 2), padx=32, anchor="w")
        tk.Label(f, text="Choose what to install:",
                 font=FONT_SMALL, bg=BG, fg=SUBTEXT).pack(padx=32, anchor="w")

        tk.Frame(f, bg=BORDER, height=1).pack(fill="x", padx=32, pady=8)

        opts = [
            (self.opt_context, "Add right-click context menu",
             "Sign and verify files directly from File Explorer / Finder"),
            (self.opt_node,    "Start P2P node automatically at login",
             "Joins the TrustNet network and syncs attestations in the background"),
            (self.opt_path,    "Add trustnet to system PATH",
             "Use the 'trustnet' command from any terminal"),
        ]

        for var, label, desc in opts:
            box = tk.Frame(f, bg=SURFACE, padx=16, pady=6)
            box.pack(fill="x", padx=32, pady=3)

            top = tk.Frame(box, bg=SURFACE)
            top.pack(fill="x")

            tk.Checkbutton(top, variable=var, bg=SURFACE,
                           activebackground=SURFACE,
                           selectcolor=BG, fg=GOLD,
                           cursor="hand2").pack(side="left")

            tk.Label(top, text=label, font=FONT_BOLD,
                     bg=SURFACE, fg=WHITE).pack(side="left", padx=4)

            tk.Label(box, text=desc, font=FONT_SMALL,
                     bg=SURFACE, fg=SUBTEXT, anchor="w").pack(anchor="w", padx=24)

        tk.Frame(f, bg=BORDER, height=1).pack(fill="x", padx=32, pady=8)

        dir_row = tk.Frame(f, bg=BG)
        dir_row.pack(fill="x", padx=32, pady=(0, 8))
        tk.Label(dir_row, text="Install to:", font=FONT_SMALL,
                 bg=BG, fg=SUBTEXT, width=10, anchor="w").pack(side="left")
        tk.Entry(dir_row, textvariable=self.install_dir, font=FONT_MONO,
                 bg=SURFACE, fg=WHITE, insertbackground=WHITE,
                 relief="flat", bd=4).pack(side="left", fill="x", expand=True)

        return f

    def _page_install(self) -> tk.Frame:
        f = tk.Frame(self._content, bg=BG)

        tk.Label(f, text="Installing TrustNet...", font=FONT_TITLE,
                 bg=BG, fg=WHITE).pack(pady=(28, 4), padx=32, anchor="w")

        tk.Frame(f, bg=BORDER, height=1).pack(fill="x", padx=32, pady=12)

        # Progress bar
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TN.Horizontal.TProgressbar",
                        troughcolor=SURFACE, background=GOLD,
                        darkcolor=GOLD, lightcolor=GOLD,
                        bordercolor=BORDER, thickness=14)

        self._progress_var = tk.DoubleVar(value=0)
        self._progress = ttk.Progressbar(f, variable=self._progress_var,
                                         maximum=100, length=520,
                                         style="TN.Horizontal.TProgressbar")
        self._progress.pack(padx=32, pady=(0, 8))

        self._progress_label = tk.Label(f, text="Preparing...",
                                        font=FONT_SMALL, bg=BG, fg=GOLD)
        self._progress_label.pack(padx=32, anchor="w")

        tk.Frame(f, bg=BORDER, height=1).pack(fill="x", padx=32, pady=12)

        # Log box
        log_frame = tk.Frame(f, bg=SURFACE)
        log_frame.pack(fill="both", expand=True, padx=32, pady=(0, 16))

        self._log = tk.Text(log_frame, bg=SURFACE, fg=WHITE,
                            font=FONT_MONO, relief="flat",
                            state="disabled", wrap="word",
                            height=10, bd=8)
        self._log.pack(fill="both", expand=True)
        self._log.tag_config("ok",   foreground=GREEN)
        self._log.tag_config("err",  foreground=RED)
        self._log.tag_config("info", foreground=GOLD)

        return f

    def _page_done(self) -> tk.Frame:
        f = tk.Frame(self._content, bg=BG)

        tk.Label(f, text="✓", font=("Cascadia Code", 56, "bold"),
                 bg=BG, fg=GOLD).pack(pady=(32, 0))

        tk.Label(f, text="Installation Complete!", font=FONT_LARGE,
                 bg=BG, fg=WHITE).pack(pady=(8, 4))

        tk.Label(f, text="TrustNet is ready to use.",
                 font=FONT, bg=BG, fg=SUBTEXT).pack()

        tk.Frame(f, bg=BORDER, height=1).pack(fill="x", padx=40, pady=24)

        cmds = [
            ("Sign a file",    "trustnet sign   myfile.zip"),
            ("Verify a file",  "trustnet verify myfile.zip"),
            ("Start node",     "trustnet node start"),
            ("Node status",    "trustnet node status"),
        ]
        for label, cmd in cmds:
            row = tk.Frame(f, bg=BG)
            row.pack(fill="x", padx=48, pady=3)
            tk.Label(row, text=label, font=FONT_SMALL, bg=BG,
                     fg=SUBTEXT, width=14, anchor="w").pack(side="left")
            tk.Label(row, text=cmd, font=FONT_MONO, bg=BG,
                     fg=GOLD, anchor="w").pack(side="left")

        tk.Frame(f, bg=BORDER, height=1).pack(fill="x", padx=40, pady=20)

        tk.Label(f, text="Right-click any file to use TrustNet from your file manager.",
                 font=FONT_SMALL, bg=BG, fg=SUBTEXT).pack()

        return f

    # ── Navigation ────────────────────────────────────────────────────────────

    def _show_page(self, idx: int) -> None:
        for p in self._pages:
            p.pack_forget()

        self._pages[idx].pack(fill="both", expand=True)
        self._current = idx

        titles = [
            ("Welcome",            "Let's get started"),
            ("Options",            "Customize your installation"),
            ("Installing",         "Please wait..."),
            ("Done",               "TrustNet is ready"),
        ]
        self._hdr_title.config(text=titles[idx][0])
        self._hdr_sub.config(text=titles[idx][1])

        for i, d in enumerate(self._dots):
            d.config(fg=GOLD if i == idx else BORDER)

        # Button states
        self._btn_back.config(state="normal" if idx > 0 else "disabled")

        if idx == 0:
            self._btn_next.config(text="Next →", command=self._next, state="normal")
        elif idx == 1:
            self._btn_next.config(text="Install  →", bg=GOLD,
                                  state="normal", command=self._next)
        elif idx == 2:
            self._btn_next.config(state="disabled")
            self._btn_back.config(state="disabled")
            self._btn_cancel.config(state="disabled")
            self.after(100, self._run_install)
        elif idx == 3:
            self._btn_next.config(text="Finish", command=self.destroy,
                                  state="normal", bg=GREEN)
            self._btn_back.config(state="disabled")
            self._btn_cancel.config(state="disabled")

    def _next(self) -> None:
        if self._current < len(self._pages) - 1:
            self._show_page(self._current + 1)

    def _back(self) -> None:
        if self._current > 0:
            self._show_page(self._current - 1)

    def _on_close(self) -> None:
        if self._current == 2:
            return  # don't close during install
        self.destroy()

    # ── Installation logic ────────────────────────────────────────────────────

    def _log_write(self, text: str, tag: str = "") -> None:
        self._log.config(state="normal")
        self._log.insert("end", text + "\n", tag)
        self._log.see("end")
        self._log.config(state="disabled")

    def _set_progress(self, pct: float, label: str) -> None:
        self._progress_var.set(pct)
        self._progress_label.config(text=label)
        self.update_idletasks()

    def _run_install(self) -> None:
        threading.Thread(target=self._install_thread, daemon=True).start()

    def _install_thread(self) -> None:
        try:
            self._do_install()
            self.after(0, lambda: self._show_page(3))
        except Exception as e:
            self.after(0, lambda: self._install_failed(str(e)))

    def _do_install(self) -> None:
        steps = []

        steps.append(("Generating cryptographic keys...", 10,  self._step_keygen))
        if self.opt_context.get():
            steps.append(("Installing context menu...",   35,  self._step_context_menu))
        if self.opt_node.get():
            steps.append(("Starting P2P node...",         65,  self._step_start_node))
        if self.opt_path.get():
            steps.append(("Adding to PATH...",            80,  self._step_path))
        steps.append(("Finalizing...",                    95,  self._step_finalize))

        for label, pct, fn in steps:
            self.after(0, lambda l=label, p=pct: self._set_progress(p, l))
            time.sleep(0.3)
            try:
                fn()
                self.after(0, lambda l=label: self._log_write(f"  ✓  {l}", "ok"))
            except Exception as e:
                self.after(0, lambda l=label, err=str(e):
                           self._log_write(f"  ✗  {l}: {err}", "err"))

        self.after(0, lambda: self._set_progress(100, "Complete!"))
        time.sleep(0.5)

    def _step_keygen(self) -> None:
        from trustnet.core import generate_keypair
        generate_keypair()

    def _step_context_menu(self) -> None:
        if _is_windows():
            self._install_context_windows()
        elif _is_mac():
            self._install_context_mac()
        else:
            self._install_context_linux()

    def _install_context_windows(self) -> None:
        import winreg

        pythonw = sys.executable.replace("python.exe", "pythonw.exe")
        if not os.path.exists(pythonw):
            pythonw = sys.executable

        script = str(_get_script_dir() / "trustnet.py")
        sign_cmd   = f'"{pythonw}" "{script}" sign "%1"'
        verify_cmd = f'"{pythonw}" "{script}" verify "%1"'

        def create(base, path, values):
            try:
                key = winreg.CreateKeyEx(base, path, 0, winreg.KEY_WRITE)
                for name, val in values.items():
                    winreg.SetValueEx(key, name, 0, winreg.REG_SZ, val)
                winreg.CloseKey(key)
            except PermissionError:
                # Fall back to HKCU if HKCR needs admin
                key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER,
                                         f"Software\\Classes\\{path}",
                                         0, winreg.KEY_WRITE)
                for name, val in values.items():
                    winreg.SetValueEx(key, name, 0, winreg.REG_SZ, val)
                winreg.CloseKey(key)

        for target in ["*", "Directory"]:
            base = f"{target}\\shell\\TrustNet"
            create(winreg.HKEY_CLASSES_ROOT, base,
                   {"": "TrustNet", "MUIVerb": "TrustNet", "SubCommands": ""})
            label_s = "Sign File" if target == "*" else "Sign Folder"
            label_v = "Verify File" if target == "*" else "Verify Folder"
            create(winreg.HKEY_CLASSES_ROOT, f"{base}\\shell\\01sign",
                   {"": label_s, "MUIVerb": label_s, "Icon": "shell32.dll,2"})
            create(winreg.HKEY_CLASSES_ROOT, f"{base}\\shell\\01sign\\command",
                   {"": sign_cmd})
            create(winreg.HKEY_CLASSES_ROOT, f"{base}\\shell\\02verify",
                   {"": label_v, "MUIVerb": label_v, "Icon": "shell32.dll,104"})
            create(winreg.HKEY_CLASSES_ROOT, f"{base}\\shell\\02verify\\command",
                   {"": verify_cmd})

    def _install_context_mac(self) -> None:
        services = Path.home() / "Library" / "Services"
        services.mkdir(parents=True, exist_ok=True)
        binary = _get_install_dir() / "trustnet"
        exe = str(binary) if binary.exists() else sys.executable + " " + str(_get_script_dir() / "trustnet.py")

        for action in ("sign", "verify"):
            label = f"TrustNet {'Sign' if action == 'sign' else 'Verify'}"
            wf = services / f"{label}.workflow" / "Contents"
            wf.mkdir(parents=True, exist_ok=True)
            (wf / "document.wflow").write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>actions</key><array><dict><key>action</key><dict>
<key>ActionBundlePath</key><string>/System/Library/Automator/Run Shell Script.action</string>
<key>ActionParameters</key><dict>
<key>COMMAND_STRING</key><string>for f in "$@"; do {exe} {action} "$f"; done</string>
<key>shell</key><string>/bin/bash</string><key>source</key><string>pass-input</string>
</dict></dict></dict></array>
<key>workflowMetaData</key><dict>
<key>workflowTypeIdentifier</key><string>com.apple.Automator.servicesMenu</string>
</dict></dict></plist>""")

    def _install_context_linux(self) -> None:
        scripts = Path.home() / ".local" / "share" / "nautilus" / "scripts"
        scripts.mkdir(parents=True, exist_ok=True)
        exe = "trustnet"

        for action in ("sign", "verify"):
            label = f"TrustNet {'Sign' if action == 'sign' else 'Verify'}"
            s = scripts / label
            s.write_text(f"#!/bin/bash\nfor f in $NAUTILUS_SCRIPT_SELECTED_FILE_PATHS; do\n    {exe} {action} \"$f\"\ndone\n")
            s.chmod(0o755)

    def _step_start_node(self) -> None:
        from trustnet.network.node import is_running, start_daemon
        if not is_running():
            start_daemon()

        if _is_windows():
            import winreg
            script = str(_get_script_dir() / "trustnet.py")
            cmd = f'"{sys.executable}" "{script}" node start'
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run",
                                 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, "TrustNetNode", 0, winreg.REG_SZ, cmd)
            winreg.CloseKey(key)

        elif _is_mac():
            plist = Path.home() / "Library" / "LaunchAgents" / "com.thamessenneam.trustnet-node.plist"
            plist.parent.mkdir(parents=True, exist_ok=True)
            exe = str(_get_script_dir() / "trustnet.py")
            plist.write_text(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
<key>Label</key><string>com.thamessenneam.trustnet-node</string>
<key>ProgramArguments</key><array>
<string>{sys.executable}</string><string>{exe}</string>
<string>node</string><string>start</string>
</array>
<key>RunAtLoad</key><true/>
</dict></plist>""")
            subprocess.run(["launchctl", "load", str(plist)],
                           capture_output=True)

    def _step_path(self) -> None:
        script_dir = str(_get_script_dir())
        if _is_windows():
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE)
            try:
                old, _ = winreg.QueryValueEx(key, "PATH")
            except FileNotFoundError:
                old = ""
            if script_dir not in old:
                winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ,
                                  old + ";" + script_dir)
            winreg.CloseKey(key)
        else:
            shell_rc = Path.home() / (".zshrc" if _is_mac() else ".bashrc")
            line = f'\nexport PATH="$PATH:{script_dir}"\n'
            content = shell_rc.read_text() if shell_rc.exists() else ""
            if script_dir not in content:
                with open(shell_rc, "a") as f:
                    f.write(line)

    def _step_finalize(self) -> None:
        time.sleep(0.5)

    def _install_failed(self, error: str) -> None:
        self._log_write(f"\nInstallation failed: {error}", "err")
        self._set_progress(self._progress_var.get(), "Failed")
        self._btn_next.config(text="Close", command=self.destroy,
                              state="normal", bg=RED)
        self._btn_cancel.config(state="normal")


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Must run from TrustNet directory
    os.chdir(Path(__file__).resolve().parent)
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    app = Wizard()
    app.mainloop()
