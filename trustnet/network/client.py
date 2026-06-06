"""HTTP client for talking to TrustNet peer nodes."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from trustnet.network import DEFAULT_PORT

TIMEOUT = 5  # seconds


def _get(host: str, port: int, path: str) -> dict | None:
    try:
        url = f"http://{host}:{port}{path}"
        with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def _post(host: str, port: int, path: str, data: dict) -> dict | None:
    try:
        url = f"http://{host}:{port}{path}"
        body = json.dumps(data).encode()
        req = urllib.request.Request(
            url, data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def get_info(host: str, port: int = DEFAULT_PORT) -> dict | None:
    return _get(host, port, "/info")


def query_attestations(host: str, port: int, file_hash: str) -> list[dict]:
    result = _get(host, port, f"/attestations?hash={file_hash}")
    if result:
        return result.get("attestations", [])
    return []


def submit_attestation(host: str, port: int, att: dict) -> bool:
    result = _post(host, port, "/attestation", att)
    return bool(result and result.get("ok"))


def register_peer(host: str, port: int, my_host: str, my_port: int) -> bool:
    result = _post(host, port, "/peer", {"host": my_host, "port": my_port})
    return bool(result and result.get("ok"))


def get_peers(host: str, port: int = DEFAULT_PORT) -> list[dict]:
    result = _get(host, port, "/peers")
    if result:
        return result.get("peers", [])
    return []


def sync_since(host: str, port: int, since: int) -> list[dict]:
    result = _get(host, port, f"/sync?since={since}")
    if result:
        return result.get("attestations", [])
    return []


def is_alive(host: str, port: int = DEFAULT_PORT) -> bool:
    return get_info(host, port) is not None
