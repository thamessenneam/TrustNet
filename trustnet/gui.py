"""Tkinter dialogs for TrustNet."""

import sys
import time
import tkinter as tk
from tkinter import ttk

# ── Palette ───────────────────────────────────────────────────────────────────
GOLD    = "#bf9000"
WHITE   = "#faf9f6"
BLUE    = "#4a86e8"
RED     = "#c0392b"
YELLOW  = "#e67e22"
BG      = "#1a1a1a"
SURFACE = "#252525"
SUBTEXT = "#888888"
BORDER  = "#333333"

# ── Fonts ─────────────────────────────────────────────────────────────────────
_CC = "Cascadia Code"   # preferred
_FB = "Consolas"        # fallback (always on Windows)

def _font(size=10, bold=False, mono=False):
    family = _CC if mono else _CC
    weight = "bold" if bold else "normal"
    return (family, size, weight)

FONT       = _font(10)
FONT_BOLD  = _font(10, bold=True)
FONT_LARGE = _font(18, bold=True)
FONT_MONO  = _font(9,  mono=True)
FONT_SMALL = _font(9)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _center(win) -> None:
    win.update_idletasks()
    w, h = win.winfo_width(), win.winfo_height()
    sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
    win.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")


def _base_window(title: str, width: int = 480, height: int = 320) -> tk.Tk:
    root = tk.Tk()
    root.title(title)
    root.geometry(f"{width}x{height}")
    root.resizable(False, False)
    root.configure(bg=BG)

    from trustnet.icon import apply_icon
    apply_icon(root)

    return root


def _divider(parent: tk.Widget) -> None:
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=12)


def _row(parent: tk.Widget, label: str, value: str, value_color: str = WHITE) -> None:
    frame = tk.Frame(parent, bg=SURFACE)
    frame.pack(fill="x", padx=0, pady=0)
    tk.Label(
        frame, text=label, font=FONT_SMALL, bg=SURFACE, fg=SUBTEXT,
        width=14, anchor="w",
    ).pack(side="left", padx=(12, 4), pady=5)
    tk.Label(
        frame, text=value, font=FONT_MONO, bg=SURFACE, fg=value_color,
        anchor="w", wraplength=290, justify="left",
    ).pack(side="left", padx=(0, 12), pady=5)


def _fmt_time(ts: int) -> str:
    if not ts:
        return "unknown"
    return time.strftime("%Y-%m-%d  %H:%M:%S", time.localtime(ts))


def _btn(parent: tk.Widget, text: str, cmd, color: str = BLUE) -> tk.Button:
    return tk.Button(
        parent, text=text, font=FONT_BOLD,
        bg=color, fg=BG,
        relief="flat", padx=24, pady=7,
        cursor="hand2", command=cmd,
        activebackground=WHITE, activeforeground=BG,
    )


# ── Header bar ────────────────────────────────────────────────────────────────

def _header(root: tk.Tk, text: str, bg: str) -> None:
    bar = tk.Frame(root, bg=bg, height=58)
    bar.pack(fill="x")
    bar.pack_propagate(False)
    tk.Label(bar, text=text, font=FONT_LARGE, bg=bg, fg=BG).pack(expand=True)


# ── Sign result ───────────────────────────────────────────────────────────────

def show_sign_result(result: dict) -> None:
    root = _base_window("TrustNet — Signed", 480, 290)

    _header(root, "Signed Successfully", GOLD)

    details = tk.Frame(root, bg=SURFACE)
    details.pack(fill="x", padx=12, pady=(10, 0))

    name = result.get("file", "")
    _row(details, "File",        name.split("\\")[-1].split("/")[-1] or "—")
    h = result.get("hash", "")
    _row(details, "SHA-256",     (h[:20] + "..." + h[-8:]) if h else "—")
    _row(details, "Fingerprint", result.get("fingerprint", "—"), GOLD)
    _row(details, "Signed at",   _fmt_time(result.get("timestamp", 0)))
    sig = result.get("sig_file", "")
    _row(details, "Saved as",    sig.split("\\")[-1].split("/")[-1] or "—")

    tk.Frame(root, bg=BG).pack(expand=True)
    _btn(root, "Close", root.destroy, BLUE).pack(pady=10)

    _center(root)
    root.mainloop()


# ── Verify result ─────────────────────────────────────────────────────────────

def show_verify_result(result: dict) -> None:
    status   = result.get("status", "UNKNOWN")
    is_ok    = result.get("success", False)

    if is_ok:
        hdr_bg, hdr_label = GOLD,   "Verified"
    elif status == "TAMPERED":
        hdr_bg, hdr_label = RED,    "Tampered"
    else:
        hdr_bg, hdr_label = YELLOW, "Warning"

    root = _base_window("TrustNet — Verify", 480, 350)

    _header(root, hdr_label, hdr_bg)

    # Message
    msg_frame = tk.Frame(root, bg=BG)
    msg_frame.pack(fill="x", padx=16, pady=(10, 6))
    tk.Label(
        msg_frame, text=result.get("message", ""),
        font=FONT_SMALL, bg=BG, fg=WHITE,
        wraplength=440, justify="left",
    ).pack(anchor="w")

    _divider(root)

    details = tk.Frame(root, bg=SURFACE)
    details.pack(fill="x", padx=12, pady=(0, 0))

    name = result.get("file", "") or result.get("directory", "")
    _row(details, "Target",      name.split("\\")[-1].split("/")[-1] or "—")

    if "file_count" in result:
        _row(details, "Files", str(result["file_count"]))
        changed = result.get("changed_files", [])
        if changed:
            _row(details, "Changed", f"{len(changed)} file(s)", RED)

    hash_col = GOLD  if result.get("hash_match")      else RED
    sig_col  = GOLD  if result.get("signature_valid") else RED
    _row(details, "Hash",        "Match"   if result.get("hash_match")      else "Mismatch", hash_col)
    _row(details, "Signature",   "Valid"   if result.get("signature_valid") else "Invalid",  sig_col)
    _row(details, "Fingerprint", result.get("fingerprint", "—"), GOLD)
    _row(details, "Signed at",   _fmt_time(result.get("timestamp", 0)))

    tk.Frame(root, bg=BG).pack(expand=True)
    _btn(root, "Close", root.destroy, BLUE).pack(pady=10)

    _center(root)
    root.mainloop()


# ── Error dialog ──────────────────────────────────────────────────────────────

def show_error(message: str) -> None:
    root = _base_window("TrustNet — Error", 420, 190)

    _header(root, "Error", RED)

    tk.Label(
        root, text=message, font=FONT,
        bg=BG, fg=WHITE,
        wraplength=380, justify="center",
    ).pack(pady=18, padx=16)

    tk.Frame(root, bg=BG).pack(expand=True)
    _btn(root, "Close", root.destroy, BLUE).pack(pady=10)

    _center(root)
    root.mainloop()
