"""Append-only SQLite attestation ledger — thread-safe."""

import hashlib
import json
import sqlite3
import threading
import time
from pathlib import Path


def _db_path() -> Path:
    from trustnet.core import get_config_dir
    return get_config_dir() / "ledger.db"


class Ledger:
    def __init__(self):
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(_db_path()), check_same_thread=False, timeout=10)
        self._conn.row_factory = sqlite3.Row
        try:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
        except sqlite3.OperationalError:
            pass  # already in WAL or locked — fine
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS attestations (
                id          TEXT PRIMARY KEY,
                file_hash   TEXT NOT NULL,
                filename    TEXT NOT NULL,
                kind        TEXT NOT NULL DEFAULT 'file',
                signature   TEXT NOT NULL,
                public_key  TEXT NOT NULL,
                timestamp   INTEGER NOT NULL,
                node_id     TEXT NOT NULL DEFAULT '',
                version     TEXT NOT NULL DEFAULT '1.0.0',
                raw_json    TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_hash ON attestations(file_hash);
            CREATE INDEX IF NOT EXISTS idx_ts   ON attestations(timestamp);

            CREATE TABLE IF NOT EXISTS peers (
                host        TEXT NOT NULL,
                port        INTEGER NOT NULL DEFAULT 7337,
                last_seen   INTEGER NOT NULL DEFAULT 0,
                last_sync   INTEGER NOT NULL DEFAULT 0,
                node_id     TEXT NOT NULL DEFAULT '',
                PRIMARY KEY (host, port)
            );
        """)
        self._conn.commit()

    # ── Attestations ──────────────────────────────────────────────────────────

    @staticmethod
    def make_id(att: dict) -> str:
        raw = att.get("public_key", "") + att.get("file_hash", "") + att.get("signature", "")
        return hashlib.sha256(raw.encode()).hexdigest()

    def add(self, att: dict) -> bool:
        """Store attestation. Returns True if new, False if duplicate."""
        att_id = self.make_id(att)
        att["id"] = att_id
        with self._lock:
            try:
                self._conn.execute(
                    """INSERT INTO attestations
                       (id,file_hash,filename,kind,signature,public_key,timestamp,node_id,version,raw_json)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (
                        att_id,
                        att.get("file_hash", ""),
                        att.get("filename", ""),
                        att.get("kind", "file"),
                        att.get("signature", ""),
                        att.get("public_key", ""),
                        att.get("timestamp", int(time.time())),
                        att.get("node_id", ""),
                        att.get("trustnet_version", "1.0.0"),
                        json.dumps(att),
                    ),
                )
                self._conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def query(self, file_hash: str) -> list[dict]:
        cur = self._conn.execute(
            "SELECT raw_json FROM attestations WHERE file_hash=? ORDER BY timestamp DESC",
            (file_hash,),
        )
        return [json.loads(r[0]) for r in cur.fetchall()]

    def since(self, timestamp: int) -> list[dict]:
        cur = self._conn.execute(
            "SELECT raw_json FROM attestations WHERE timestamp>? ORDER BY timestamp ASC",
            (timestamp,),
        )
        return [json.loads(r[0]) for r in cur.fetchall()]

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM attestations").fetchone()[0]

    # ── Peers ─────────────────────────────────────────────────────────────────

    def add_peer(self, host: str, port: int, node_id: str = "") -> None:
        with self._lock:
            self._conn.execute(
                """INSERT INTO peers(host,port,last_seen,node_id)
                   VALUES(?,?,?,?)
                   ON CONFLICT(host,port) DO UPDATE SET last_seen=excluded.last_seen, node_id=excluded.node_id""",
                (host, port, int(time.time()), node_id),
            )
            self._conn.commit()

    def update_sync(self, host: str, port: int) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE peers SET last_sync=? WHERE host=? AND port=?",
                (int(time.time()), host, port),
            )
            self._conn.commit()

    def get_peers(self) -> list[dict]:
        cur = self._conn.execute("SELECT host,port,last_seen,last_sync,node_id FROM peers")
        return [dict(r) for r in cur.fetchall()]

    def remove_peer(self, host: str, port: int) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM peers WHERE host=? AND port=?", (host, port))
            self._conn.commit()
