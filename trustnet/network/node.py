"""
TrustNet node — HTTP server + peer sync + mDNS discovery.

Run as a daemon:
    python -m trustnet.network.node

Or control via CLI:
    trustnet node start / stop / status / peers / add <host>
"""

import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from trustnet.network import DEFAULT_PORT
from trustnet.network.ledger import Ledger
from trustnet.network.protocol import verify_attestation

# ── Globals (set during start) ────────────────────────────────────────────────
_ledger: Ledger | None = None
_node_id: str = ""
_port: int = DEFAULT_PORT
_server: HTTPServer | None = None
_sync_thread: threading.Thread | None = None
_running = False

SYNC_INTERVAL = 60  # seconds between background syncs


def get_ledger() -> Ledger:
    global _ledger
    if _ledger is None:
        _ledger = Ledger()
    return _ledger


# ── HTTP Handler ──────────────────────────────────────────────────────────────

class _Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # quiet

    def _json(self, data: dict, code: int = 200) -> None:
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(n)) if n else {}

    def do_GET(self):
        parsed = urlparse(self.path)
        p      = parsed.path
        qs     = parse_qs(parsed.query)
        db     = get_ledger()

        if p == "/info":
            self._json({
                "node_id":      _node_id,
                "version":      "1.0.0",
                "port":         _port,
                "attestations": db.count(),
                "peers":        len(db.get_peers()),
            })

        elif p == "/attestations":
            h = qs.get("hash", [""])[0]
            if not h:
                self._json({"error": "hash required"}, 400); return
            atts = db.query(h)
            self._json({"attestations": atts, "count": len(atts)})

        elif p == "/peers":
            self._json({"peers": db.get_peers()})

        elif p == "/sync":
            since = int(qs.get("since", ["0"])[0])
            self._json({"attestations": db.since(since)})

        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        p  = urlparse(self.path).path
        db = get_ledger()

        try:
            body = self._body()
        except Exception:
            self._json({"error": "invalid JSON"}, 400); return

        if p == "/attestation":
            if not verify_attestation(body):
                self._json({"error": "invalid signature"}, 400); return
            is_new = db.add(body)
            if is_new:
                # propagate to peers without blocking
                threading.Thread(
                    target=_propagate, args=(body,), daemon=True
                ).start()
            self._json({"ok": True, "new": is_new})

        elif p == "/peer":
            host    = body.get("host", "")
            port    = int(body.get("port", DEFAULT_PORT))
            node_id = body.get("node_id", "")
            if not host:
                self._json({"error": "host required"}, 400); return
            db.add_peer(host, port, node_id)
            threading.Thread(
                target=_sync_with_peer, args=(host, port), daemon=True
            ).start()
            self._json({"ok": True})

        else:
            self._json({"error": "not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


# ── Peer sync ─────────────────────────────────────────────────────────────────

def _propagate(att: dict) -> None:
    """Send a new attestation to all known peers."""
    from trustnet.network import client
    db = get_ledger()
    for peer in db.get_peers():
        try:
            client.submit_attestation(peer["host"], peer["port"], att)
        except Exception:
            pass


def _sync_with_peer(host: str, port: int) -> None:
    """Pull all attestations from a peer that we haven't seen yet."""
    from trustnet.network import client
    db = get_ledger()

    # Find last sync time for this peer
    peers = {(p["host"], p["port"]): p for p in db.get_peers()}
    last_sync = peers.get((host, port), {}).get("last_sync", 0)

    try:
        atts = client.sync_since(host, port, last_sync)
        new_count = 0
        for att in atts:
            if verify_attestation(att):
                if db.add(att):
                    new_count += 1
        db.update_sync(host, port)
    except Exception:
        pass


def _sync_loop() -> None:
    """Background thread: sync with all peers every SYNC_INTERVAL seconds."""
    while _running:
        db = get_ledger()
        for peer in db.get_peers():
            if not _running:
                break
            _sync_with_peer(peer["host"], peer["port"])
        for _ in range(SYNC_INTERVAL):
            if not _running:
                break
            time.sleep(1)


# ── mDNS peer discovery ───────────────────────────────────────────────────────

def _on_peer_found(host: str, port: int, remote_node_id: str) -> None:
    db = get_ledger()
    db.add_peer(host, port, remote_node_id)
    # Tell them about us and sync
    from trustnet.network import client
    try:
        import socket
        my_host = socket.gethostbyname(socket.gethostname())
        client.register_peer(host, port, my_host, _port)
    except Exception:
        pass
    threading.Thread(
        target=_sync_with_peer, args=(host, port), daemon=True
    ).start()


def _on_peer_removed(host: str, port: int) -> None:
    pass  # keep in DB for history, just stops syncing


# ── PID file helpers ──────────────────────────────────────────────────────────

def _pid_path(port: int = DEFAULT_PORT) -> Path:
    from trustnet.core import get_config_dir
    return get_config_dir() / f"node.{port}.pid"


def _write_pid(port: int) -> None:
    _pid_path(port).write_text(json.dumps({"pid": os.getpid(), "port": port}))


def _read_pid(port: int = DEFAULT_PORT) -> dict | None:
    p = _pid_path(port)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def _clear_pid(port: int = DEFAULT_PORT) -> None:
    try:
        _pid_path(port).unlink(missing_ok=True)
    except Exception:
        pass


# ── Public API ────────────────────────────────────────────────────────────────

def is_running(port: int = DEFAULT_PORT) -> bool:
    from trustnet.network.client import is_alive
    return is_alive("127.0.0.1", port)


def get_local_info() -> dict | None:
    from trustnet.network.client import get_info
    info = _read_pid()
    if not info:
        return None
    return get_info("127.0.0.1", info.get("port", DEFAULT_PORT))


def start_daemon(port: int = DEFAULT_PORT) -> None:
    """Start node as a background subprocess (no window)."""
    import subprocess
    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    subprocess.Popen(
        [sys.executable, "-m", "trustnet.network.node", "--serve", f"--port={port}"],
        creationflags=flags,
        close_fds=True,
        cwd=str(Path(__file__).resolve().parent.parent.parent),
    )
    # Wait for it to come up
    from trustnet.network.client import is_alive
    for _ in range(20):
        time.sleep(0.3)
        if is_alive("127.0.0.1", port):
            return
    raise RuntimeError("Node did not start in time.")


def stop_daemon(port: int = DEFAULT_PORT) -> bool:
    info = _read_pid(port)
    if not info:
        # Try to stop by any means — node may have lost its PID file
        from trustnet.network.client import is_alive
        if not is_alive("127.0.0.1", port):
            return False
    try:
        pid = info["pid"] if info else None
        if pid:
            if sys.platform == "win32":
                import subprocess
                subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                               capture_output=True)
            else:
                import signal
                os.kill(pid, signal.SIGTERM)
        _clear_pid(port)
        return True
    except Exception:
        _clear_pid(port)
        return False


def publish_attestation(att: dict) -> bool:
    """Submit an attestation to the local node (non-blocking, fire-and-forget)."""
    if not is_running():
        return False
    from trustnet.network.client import submit_attestation
    info = _read_pid()
    port = info.get("port", DEFAULT_PORT) if info else DEFAULT_PORT
    try:
        return submit_attestation("127.0.0.1", port, att)
    except Exception:
        return False


def query_network(file_hash: str) -> list[dict]:
    """Query the local node (which has synced peers) for attestations of a hash."""
    if not is_running():
        return []
    from trustnet.network.client import query_attestations
    info = _read_pid()
    port = info.get("port", DEFAULT_PORT) if info else DEFAULT_PORT
    try:
        return query_attestations("127.0.0.1", port, file_hash)
    except Exception:
        return []


# ── Entry point (daemon mode) ─────────────────────────────────────────────────

def _serve(port: int) -> None:
    global _node_id, _port, _server, _running

    from trustnet.core import get_public_key_b64, generate_keypair
    generate_keypair()
    _node_id = get_public_key_b64()
    _port    = port
    _running = True

    # Start HTTP server
    _server = HTTPServer(("0.0.0.0", port), _Handler)
    _write_pid(port)

    # Start background sync thread
    st = threading.Thread(target=_sync_loop, daemon=True)
    st.start()

    # Start mDNS discovery
    from trustnet.network import discovery
    discovery.start(_node_id, port, _on_peer_found, _on_peer_removed)

    try:
        _server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        _running = False
        discovery.stop()
        _clear_pid(port)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--serve", action="store_true")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = ap.parse_args()
    if args.serve:
        _serve(args.port)
