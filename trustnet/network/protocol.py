"""Attestation schema and cryptographic verification."""

import base64
import hashlib
import time

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from trustnet.core import _make_message


def build_attestation(sign_result: dict, node_id: str) -> dict:
    """Convert a core.sign_file/sign_directory result into a network attestation."""
    # sign_result contains: file, hash, sig_file, fingerprint, timestamp
    # We need to read the .trustsig file to get signature + public_key
    import json
    from pathlib import Path

    sig_path = Path(sign_result.get("sig_file", ""))
    if not sig_path.exists():
        # Directory manifest path
        directory = sign_result.get("directory", "")
        if directory:
            sig_path = Path(directory) / "trustnet.manifest.json"

    if not sig_path.exists():
        raise FileNotFoundError(f"Signature file not found: {sig_path}")

    sig_data = json.loads(sig_path.read_text())

    kind = sig_data.get("kind", "file")
    if kind == "directory":
        filename = sig_data.get("directory", "")
        file_hash = sig_data.get("root_hash", "")
    else:
        filename = sig_data.get("file", "")
        file_hash = sig_data.get("hash", "")

    return {
        "trustnet_version": "1.0.0",
        "kind": kind,
        "filename": filename,
        "file_hash": file_hash,
        "signature": sig_data.get("signature", ""),
        "public_key": sig_data.get("public_key", ""),
        "timestamp": sig_data.get("timestamp", int(time.time())),
        "node_id": node_id,
    }


def verify_attestation(att: dict) -> bool:
    """Verify the Ed25519 signature inside an attestation dict."""
    try:
        pub_b64 = att.get("public_key", "")
        sig_b64 = att.get("signature", "")
        kind     = att.get("kind", "file")
        filename = att.get("filename", "")
        file_hash = att.get("file_hash", "")

        if not all([pub_b64, sig_b64, filename, file_hash]):
            return False

        message = _make_message(kind, filename, file_hash)
        pub_raw = base64.b64decode(pub_b64)
        pub_key = Ed25519PublicKey.from_public_bytes(pub_raw)
        pub_key.verify(base64.b64decode(sig_b64), message)
        return True
    except (InvalidSignature, Exception):
        return False


def fingerprint(pub_b64: str) -> str:
    raw = base64.b64decode(pub_b64)
    h = hashlib.sha256(raw).hexdigest().upper()
    return ":".join(h[i: i + 4] for i in range(0, 24, 4))
