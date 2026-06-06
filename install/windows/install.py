"""
TrustNet Windows Context Menu Installer
Run as Administrator: python install.py
"""

import os
import sys
import winreg
from pathlib import Path


def find_python() -> str:
    return sys.executable


def get_trustnet_script() -> str:
    # Resolve to the trustnet.py next to this installer's grandparent
    here = Path(__file__).resolve()
    root = here.parent.parent.parent  # TrustNet/
    script = root / "trustnet.py"
    if not script.exists():
        raise FileNotFoundError(f"Could not find trustnet.py at {script}")
    return str(script)


def create_key(base, path: str, values: dict) -> None:
    key = winreg.CreateKeyEx(base, path, 0, winreg.KEY_WRITE)
    for name, value in values.items():
        if name == "":
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, value)
        else:
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
    winreg.CloseKey(key)


def install_context_menu(python_exe: str, script: str) -> None:
    cmd_sign = f'"{python_exe}" "{script}" sign "%1"'
    cmd_verify = f'"{python_exe}" "{script}" verify "%1"'

    # ── Files (*) ─────────────────────────────────────────────────────────────
    for root_key, root_name in [
        (winreg.HKEY_CLASSES_ROOT, "HKCR"),
    ]:
        for target in ["*", "Directory"]:
            base_path = f"{target}\\shell\\TrustNet"

            # Parent menu item (cascading)
            create_key(root_key, base_path, {
                "": "TrustNet",
                "MUIVerb": "TrustNet",
                "SubCommands": "",
            })

            # Sign sub-item
            label = "Sign File" if target == "*" else "Sign Folder"
            create_key(root_key, f"{base_path}\\shell\\sign", {
                "": label,
                "MUIVerb": label,
            })
            create_key(root_key, f"{base_path}\\shell\\sign\\command", {
                "": cmd_sign,
            })

            # Verify sub-item
            label = "Verify File" if target == "*" else "Verify Folder"
            create_key(root_key, f"{base_path}\\shell\\verify", {
                "": label,
                "MUIVerb": label,
            })
            create_key(root_key, f"{base_path}\\shell\\verify\\command", {
                "": cmd_verify,
            })

    # ── .trustsig files ───────────────────────────────────────────────────────
    create_key(winreg.HKEY_CLASSES_ROOT, ".trustsig", {"": "TrustNet.Signature"})
    create_key(winreg.HKEY_CLASSES_ROOT, "TrustNet.Signature", {"": "TrustNet Signature File"})
    create_key(winreg.HKEY_CLASSES_ROOT, "TrustNet.Signature\\shell\\verify", {
        "": "Verify Original File",
        "MUIVerb": "Verify Original File",
    })
    create_key(winreg.HKEY_CLASSES_ROOT, "TrustNet.Signature\\shell\\verify\\command", {
        "": cmd_verify,
    })

    print("[TrustNet] Context menu installed successfully.")
    print(f"  Python : {python_exe}")
    print(f"  Script : {script}")
    print()
    print("Right-click any file or folder to see the TrustNet menu.")


def main() -> None:
    # Must run as admin on Windows
    if sys.platform != "win32":
        print("This installer is for Windows only.")
        sys.exit(1)

    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        is_admin = False

    if not is_admin:
        print("[TrustNet] ERROR: Please run this script as Administrator.")
        print("  Right-click install.py -> Run as administrator")
        print("  Or: Start an Admin PowerShell and run: python install.py")
        sys.exit(1)

    python_exe = find_python()
    script = get_trustnet_script()

    print(f"[TrustNet] Installing context menu...")
    print(f"  Python : {python_exe}")
    print(f"  Script : {script}")
    print()

    install_context_menu(python_exe, script)


if __name__ == "__main__":
    main()
