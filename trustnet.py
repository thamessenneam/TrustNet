#!/usr/bin/env python3
"""
TrustNet — entry point.

Called from context menus as:
    trustnet.py sign   <path>
    trustnet.py verify <path>
    trustnet.py keygen
    trustnet.py pubkey

When invoked via GUI (context menu), results are shown in a dialog window.
When invoked from a terminal (stdout is a TTY), results are printed as text.
"""

import sys
import os


def _is_gui_mode() -> bool:
    """Detect whether we were launched from a context menu (no terminal)."""
    if sys.platform == "win32":
        # On Windows, context menu launches have no console attached
        try:
            import ctypes
            return ctypes.windll.kernel32.GetConsoleWindow() == 0
        except Exception:
            return not sys.stdout.isatty()
    return not sys.stdout.isatty()


def main() -> None:
    if len(sys.argv) < 2:
        # No arguments: show a simple info dialog
        from trustnet.gui import show_error
        show_error("Usage: trustnet sign <file>\n       trustnet verify <file>")
        return

    command = sys.argv[1].lower()

    if command in ("sign", "verify") and len(sys.argv) < 3:
        if _is_gui_mode():
            from trustnet.gui import show_error
            show_error(f"Please provide a file or folder path for '{command}'.")
        else:
            print(f"[TrustNet] Error: '{command}' requires a path argument.", file=sys.stderr)
        sys.exit(1)

    gui = _is_gui_mode()

    if command == "sign":
        path = sys.argv[2]
        try:
            from pathlib import Path
            from trustnet import core
            p = Path(path)
            result = core.sign_directory(p) if p.is_dir() else core.sign_file(p)
            if gui:
                from trustnet.gui import show_sign_result
                show_sign_result(result)
            else:
                from trustnet.cli import cmd_sign
                import argparse
                ns = argparse.Namespace(path=path, json=False)
                sys.exit(cmd_sign(ns))
        except Exception as e:
            if gui:
                from trustnet.gui import show_error
                show_error(str(e))
            else:
                print(f"[TrustNet] Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif command == "verify":
        path = sys.argv[2]
        try:
            from pathlib import Path
            from trustnet import core
            p = Path(path)
            result = core.verify_directory(p) if p.is_dir() else core.verify_file(p)
            if gui:
                from trustnet.gui import show_verify_result
                show_verify_result(result)
            else:
                from trustnet.cli import cmd_verify
                import argparse
                ns = argparse.Namespace(path=path, json=False)
                sys.exit(cmd_verify(ns))
        except Exception as e:
            if gui:
                from trustnet.gui import show_error
                show_error(str(e))
            else:
                print(f"[TrustNet] Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif command == "keygen":
        force = "--force" in sys.argv
        from trustnet.cli import cmd_keygen
        import argparse
        ns = argparse.Namespace(force=force, json=False)
        sys.exit(cmd_keygen(ns))

    elif command == "pubkey":
        from trustnet.cli import cmd_pubkey
        import argparse
        ns = argparse.Namespace(json="--json" in sys.argv)
        sys.exit(cmd_pubkey(ns))

    else:
        # Fall through to full CLI parser
        from trustnet.cli import main as cli_main
        sys.exit(cli_main(sys.argv[1:]))


if __name__ == "__main__":
    main()
