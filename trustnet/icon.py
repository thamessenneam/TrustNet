"""Generates the TrustNet window icon: $:TN in Cascadia Code."""

from __future__ import annotations

import os
import sys
from pathlib import Path

GOLD  = "#bf9000"
WHITE = "#faf9f6"
BG    = "#1a1a1a"

_ICON_CACHE: Path | None = None


def _find_font() -> str | None:
    candidates = [
        # Cascadia Code — user-installed
        r"C:\Windows\Fonts\CascadiaCode.ttf",
        r"C:\Windows\Fonts\CascadiaCodePL.ttf",
        r"C:\Windows\Fonts\CascadiaMono.ttf",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts\CascadiaCode.ttf"),
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts\CascadiaCodePL.ttf"),
        # macOS
        "/Library/Fonts/CascadiaCode.ttf",
        os.path.expanduser("~/Library/Fonts/CascadiaCode.ttf"),
        # Linux
        "/usr/share/fonts/truetype/cascadia-code/CascadiaCode.ttf",
        os.path.expanduser("~/.local/share/fonts/CascadiaCode.ttf"),
        # Fallback: Consolas (always on Windows)
        r"C:\Windows\Fonts\consola.ttf",
        r"C:\Windows\Fonts\Consolas.ttf",
        "/Library/Fonts/Consolas.ttf",
    ]
    for p in candidates:
        if p and os.path.isfile(p):
            return p
    return None


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _make_icon_image(size: int):
    from PIL import Image, ImageDraw, ImageFont

    bg_rgb  = _hex_to_rgb(BG)
    gold_rgb = _hex_to_rgb(GOLD)
    white_rgb = _hex_to_rgb(WHITE)

    img  = Image.new("RGBA", (size, size), (*bg_rgb, 255))
    draw = ImageDraw.Draw(img)

    font_path = _find_font()
    font_size = max(8, int(size * 0.36))

    try:
        font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
    except Exception:
        font = ImageFont.load_default()

    prefix, suffix = "$:", "TN"

    bb_pre = draw.textbbox((0, 0), prefix, font=font)
    bb_suf = draw.textbbox((0, 0), suffix, font=font)

    pre_w = bb_pre[2] - bb_pre[0]
    suf_w = bb_suf[2] - bb_suf[0]
    total_w = pre_w + suf_w
    text_h  = max(bb_pre[3] - bb_pre[1], bb_suf[3] - bb_suf[1])

    x = (size - total_w) // 2 - bb_pre[0]
    y = (size - text_h)  // 2 - bb_pre[1]

    draw.text((x,           y), prefix, fill=(*white_rgb, 255), font=font)
    draw.text((x + pre_w,   y), suffix, fill=(*gold_rgb,  255), font=font)

    return img


def get_icon_path() -> str | None:
    global _ICON_CACHE
    if _ICON_CACHE and _ICON_CACHE.exists():
        return str(_ICON_CACHE)

    try:
        from PIL import Image
        from trustnet.core import get_config_dir
        out = get_config_dir() / "trustnet.ico"

        images = [_make_icon_image(s) for s in (256, 48, 32, 16)]
        images[0].save(
            str(out),
            format="ICO",
            sizes=[(256, 256), (48, 48), (32, 32), (16, 16)],
            append_images=images[1:],
        )
        _ICON_CACHE = out
        return str(out)
    except Exception:
        return None


def apply_icon(window) -> None:
    """Set the TrustNet icon on a tkinter window."""
    try:
        path = get_icon_path()
        if path:
            window.iconbitmap(path)
    except Exception:
        pass
