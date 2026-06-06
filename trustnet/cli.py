"""Command-line interface for TrustNet."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from trustnet.network import DEFAULT_PORT
from trustnet.core import (
    fingerprint,
    generate_keypair,
    get_config_dir,
    get_public_key_b64,
    sign_directory,
    sign_file,
    verify_directory,
    verify_file,
)


def _fmt_time(ts: int) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts)) if ts else "unknown"


def cmd_sign(args: argparse.Namespace) -> int:
    path = Path(args.path)
    try:
        if path.is_dir():
            result = sign_directory(path)
            print(f"[TrustNet] Directory signed.")
            print(f"  Directory : {result['directory']}")
            print(f"  Files     : {result['file_count']}")
            print(f"  Root hash : {result['root_hash'][:16]}...")
            print(f"  Manifest  : {result['manifest_file']}")
            print(f"  Key       : {result['fingerprint']}")
        else:
            result = sign_file(path)
            print(f"[TrustNet] File signed.")
            print(f"  File      : {result['file']}")
            print(f"  SHA-256   : {result['hash'][:16]}...")
            print(f"  Signature : {result['sig_file']}")
            print(f"  Key       : {result['fingerprint']}")

        if args.json:
            print(json.dumps(result, indent=2))
        return 0
    except Exception as e:
        print(f"[TrustNet] Error: {e}", file=sys.stderr)
        return 1


def cmd_verify(args: argparse.Namespace) -> int:
    path = Path(args.path)
    try:
        if path.is_dir():
            result = verify_directory(path)
        else:
            result = verify_file(path)

        status = result["status"]
        ok = result["success"]
        symbol = "[OK]" if ok else "[FAIL]"
        print(f"[TrustNet] {symbol} {status}")
        print(f"  {result['message']}")
        print(f"  Key       : {result.get('fingerprint', '-')}")
        print(f"  Signed at : {_fmt_time(result.get('timestamp', 0))}")

        # Network trust info
        n_atts = result.get("network_attestations", 0)
        n_signers = result.get("network_signers", [])
        if result.get("network_online"):
            print(f"  Network   : {n_atts} attestation(s) from {len(n_signers)} unique signer(s)")
            for s in n_signers:
                print(f"    - {s}")
        else:
            print(f"  Network   : offline (run: trustnet node start)")

        if not ok and result.get("changed_files"):
            print(f"  Changed files ({len(result['changed_files'])}):")
            for f in result["changed_files"][:10]:
                print(f"    - {f}")

        if args.json:
            print(json.dumps(result, indent=2))

        return 0 if ok else 2
    except Exception as e:
        print(f"[TrustNet] Error: {e}", file=sys.stderr)
        return 1


def cmd_keygen(args: argparse.Namespace) -> int:
    config = get_config_dir()
    private_path = config / "private.key"
    if private_path.exists() and not args.force:
        print("[TrustNet] Key already exists.")
        print(f"  Location  : {config}")
        print(f"  Key       : {fingerprint(get_public_key_b64())}")
        print("  Use --force to regenerate (this invalidates all existing signatures).")
        return 0

    if private_path.exists() and args.force:
        private_path.unlink()
        (config / "public.key").unlink(missing_ok=True)

    generate_keypair()
    pub_b64 = get_public_key_b64()
    print("[TrustNet] New keypair generated.")
    print(f"  Location  : {config}")
    print(f"  Fingerprint: {fingerprint(pub_b64)}")
    print(f"  Public key : {pub_b64[:24]}...")
    return 0


def cmd_pubkey(args: argparse.Namespace) -> int:
    try:
        pub_b64 = get_public_key_b64()
        fp = fingerprint(pub_b64)
        if args.json:
            print(json.dumps({"public_key": pub_b64, "fingerprint": fp}))
        else:
            print(f"Fingerprint : {fp}")
            print(f"Public key  : {pub_b64}")
        return 0
    except Exception as e:
        print(f"[TrustNet] Error: {e}", file=sys.stderr)
        return 1


def cmd_node(args: argparse.Namespace) -> int:
    from trustnet.network import node as n, DEFAULT_PORT

    sub = args.node_cmd

    if sub == "start":
        if n.is_running():
            print("[TrustNet] Node is already running.")
            info = n.get_local_info()
            if info:
                print(f"  Port         : {info.get('port', DEFAULT_PORT)}")
                print(f"  Attestations : {info.get('attestations', 0)}")
                print(f"  Peers        : {info.get('peers', 0)}")
            return 0
        port = getattr(args, "port", DEFAULT_PORT)
        print(f"[TrustNet] Starting node on port {port}...")
        try:
            n.start_daemon(port)
            print(f"[TrustNet] Node started.")
            print(f"  Port    : {port}")
            print(f"  Other TrustNet nodes on your network will be discovered automatically.")
        except Exception as e:
            print(f"[TrustNet] Failed to start: {e}", file=sys.stderr)
            return 1
        return 0

    elif sub == "stop":
        if not n.is_running():
            print("[TrustNet] Node is not running.")
            return 0
        if n.stop_daemon():
            print("[TrustNet] Node stopped.")
        else:
            print("[TrustNet] Could not stop node.", file=sys.stderr)
            return 1
        return 0

    elif sub == "status":
        if n.is_running():
            info = n.get_local_info()
            print("[TrustNet] Node is RUNNING")
            if info:
                print(f"  Port         : {info.get('port', DEFAULT_PORT)}")
                print(f"  Attestations : {info.get('attestations', 0)}")
                print(f"  Peers        : {info.get('peers', 0)}")
        else:
            print("[TrustNet] Node is STOPPED")
            print("  Run: trustnet node start")
        return 0

    elif sub == "peers":
        if not n.is_running():
            print("[TrustNet] Node is not running. Start it first: trustnet node start")
            return 1
        from trustnet.network.ledger import Ledger
        db = Ledger()
        peers = db.get_peers()
        if not peers:
            print("[TrustNet] No peers known yet.")
            print("  Peers on your LAN are discovered automatically.")
            print("  Add a remote peer: trustnet node add <host>")
        else:
            print(f"[TrustNet] {len(peers)} peer(s):")
            for p in peers:
                last = _fmt_time(p.get("last_seen", 0))
                sync = _fmt_time(p.get("last_sync", 0))
                print(f"  {p['host']}:{p['port']}  seen={last}  sync={sync}")
        return 0

    elif sub == "add":
        host = args.host
        port = getattr(args, "port", DEFAULT_PORT)
        if not n.is_running():
            print("[TrustNet] Node is not running. Start it first: trustnet node start")
            return 1
        from trustnet.network import client
        info = client.get_info(host, port)
        if not info:
            print(f"[TrustNet] Cannot reach {host}:{port}", file=sys.stderr)
            return 1
        from trustnet.network.ledger import Ledger
        Ledger().add_peer(host, port, info.get("node_id", ""))
        print(f"[TrustNet] Peer added: {host}:{port}")
        print(f"  Attestations on that node : {info.get('attestations', 0)}")
        print("  Syncing in background...")
        return 0

    elif sub == "sync":
        if not n.is_running():
            print("[TrustNet] Node is not running.")
            return 1
        from trustnet.network.ledger import Ledger
        from trustnet.network import client
        from trustnet.network.protocol import verify_attestation
        db = Ledger()
        peers = db.get_peers()
        if not peers:
            print("[TrustNet] No peers to sync with.")
            return 0
        total = 0
        for p in peers:
            atts = client.sync_since(p["host"], p["port"], p.get("last_sync", 0))
            new = sum(1 for a in atts if verify_attestation(a) and db.add(a))
            total += new
            db.update_sync(p["host"], p["port"])
            print(f"  {p['host']}:{p['port']} -> {new} new attestation(s)")
        print(f"[TrustNet] Sync complete. {total} new attestation(s) total.")
        return 0

    print(f"[TrustNet] Unknown node command: {sub}", file=sys.stderr)
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trustnet",
        description="TrustNet — cryptographic file & package signing",
    )
    parser.add_argument("--json", action="store_true", help="Output JSON")
    sub = parser.add_subparsers(dest="command", required=True)

    p_sign = sub.add_parser("sign", help="Sign a file or directory")
    p_sign.add_argument("path", help="File or directory to sign")
    p_sign.set_defaults(func=cmd_sign)

    p_verify = sub.add_parser("verify", help="Verify a file or directory")
    p_verify.add_argument("path", help="File or directory to verify")
    p_verify.set_defaults(func=cmd_verify)

    p_keygen = sub.add_parser("keygen", help="Generate a new keypair")
    p_keygen.add_argument("--force", action="store_true", help="Overwrite existing key")
    p_keygen.set_defaults(func=cmd_keygen)

    p_pub = sub.add_parser("pubkey", help="Show your public key and fingerprint")
    p_pub.set_defaults(func=cmd_pubkey)

    # node subcommand with sub-subcommands
    p_node = sub.add_parser("node", help="Manage the TrustNet P2P node")
    node_sub = p_node.add_subparsers(dest="node_cmd", required=True)

    ns = node_sub.add_parser("start",  help="Start the P2P node daemon")
    ns.add_argument("--port", type=int, default=DEFAULT_PORT)

    node_sub.add_parser("stop",   help="Stop the node daemon")
    node_sub.add_parser("status", help="Show node status")
    node_sub.add_parser("peers",  help="List known peers")
    node_sub.add_parser("sync",   help="Force sync with all peers")

    na = node_sub.add_parser("add", help="Manually add a peer by host")
    na.add_argument("host", help="Peer hostname or IP address")
    na.add_argument("--port", type=int, default=DEFAULT_PORT)

    p_node.set_defaults(func=cmd_node)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
