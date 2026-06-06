"""
TrustNet Windows Context Menu Uninstaller
Run as Administrator: python uninstall.py
"""

import sys
import winreg


def delete_key_tree(base, path: str) -> None:
    try:
        # Delete children first
        key = winreg.OpenKey(base, path, 0, winreg.KEY_READ | winreg.KEY_WRITE)
        while True:
            try:
                subkey_name = winreg.EnumKey(key, 0)
                winreg.CloseKey(key)
                delete_key_tree(base, f"{path}\\{subkey_name}")
                key = winreg.OpenKey(base, path, 0, winreg.KEY_READ | winreg.KEY_WRITE)
            except OSError:
                break
        winreg.CloseKey(key)
        winreg.DeleteKey(base, path)
        print(f"  Removed: {path}")
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"  Warning: could not remove {path}: {e}")


def main() -> None:
    if sys.platform != "win32":
        print("This uninstaller is for Windows only.")
        sys.exit(1)

    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        is_admin = False

    if not is_admin:
        print("[TrustNet] ERROR: Please run as Administrator.")
        sys.exit(1)

    print("[TrustNet] Removing context menu entries...")

    for target in ["*", "Directory"]:
        delete_key_tree(winreg.HKEY_CLASSES_ROOT, f"{target}\\shell\\TrustNet")

    delete_key_tree(winreg.HKEY_CLASSES_ROOT, ".trustsig")
    delete_key_tree(winreg.HKEY_CLASSES_ROOT, "TrustNet.Signature")

    print("[TrustNet] Uninstalled successfully.")


if __name__ == "__main__":
    main()
