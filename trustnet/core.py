import base64
import hashlib
import json
import os
import sys
import threading
import time
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


def _try_publish(sign_result: dict) -> None:
    """Fire-and-forget: publish attestation to local node if it's running."""
    def _bg():
        try:
            from trustnet.network.protocol import build_attestation
            from trustnet.network.node import publish_attestation, is_running
            if not is_running():
                return
            node_id = get_public_key_b64()
            att = build_attestation(sign_result, node_id)
            publish_attestation(att)
        except Exception:
            pass
    threading.Thread(target=_bg, daemon=True).start()

VERSION = "1.0.0"
SIG_EXT = ".trustsig"


# ── Config directory (per platform) ──────────────────────────────────────────

def get_config_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
        return base / "TrustNet"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "TrustNet"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME", "")
        base = Path(xdg) if xdg else Path.home() / ".config"
        return base / "trustnet"


def _ensure_config() -> Path:
    d = get_config_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


# ── Key management ────────────────────────────────────────────────────────────

def _key_paths() -> tuple[Path, Path]:
    config = _ensure_config()
    return config / "private.key", config / "public.key"


def generate_keypair() -> None:
    private_path, public_path = _key_paths()
    if private_path.exists():
        return

    key = Ed25519PrivateKey.generate()

    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_raw = key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    private_path.write_bytes(private_pem)
    public_path.write_text(base64.b64encode(public_raw).decode())

    if sys.platform != "win32":
        os.chmod(private_path, 0o600)


def _load_private_key() -> Ed25519PrivateKey:
    private_path, _ = _key_paths()
    if not private_path.exists():
        generate_keypair()
    return serialization.load_pem_private_key(private_path.read_bytes(), password=None)


def get_public_key_b64() -> str:
    _, public_path = _key_paths()
    if not public_path.exists():
        generate_keypair()
    return public_path.read_text().strip()


def fingerprint(pub_b64: str) -> str:
    raw = base64.b64decode(pub_b64)
    h = hashlib.sha256(raw).hexdigest().upper()
    return ":".join(h[i : i + 4] for i in range(0, 24, 4))


# ── Hashing ───────────────────────────────────────────────────────────────────

def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_directory(path: Path) -> tuple[str, dict]:
    """Return (root_hash, {relative_path: hash}) for all files under path."""
    path = Path(path)
    file_hashes: dict[str, str] = {}

    for fp in sorted(path.rglob("*")):
        if fp.is_file() and fp.suffix != SIG_EXT and fp.name != "trustnet.manifest.json":
            rel = fp.relative_to(path).as_posix()
            file_hashes[rel] = hash_file(fp)

    combined = "\n".join(f"{v}  {k}" for k, v in sorted(file_hashes.items()))
    root_hash = hashlib.sha256(combined.encode()).hexdigest()
    return root_hash, file_hashes


# ── Signing ───────────────────────────────────────────────────────────────────

def _make_message(kind: str, name: str, content_hash: str) -> bytes:
    return f"trustnet:v1:{kind}:{name}:{content_hash}".encode()


def sign_file(file_path: Path) -> dict:
    file_path = Path(file_path).resolve()
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    private_key = _load_private_key()
    pub_b64 = get_public_key_b64()
    file_hash = hash_file(file_path)
    message = _make_message("file", file_path.name, file_hash)
    signature = base64.b64encode(private_key.sign(message)).decode()

    sig_data = {
        "trustnet_version": VERSION,
        "kind": "file",
        "file": file_path.name,
        "hash": file_hash,
        "hash_algorithm": "sha256",
        "signature": signature,
        "public_key": pub_b64,
        "timestamp": int(time.time()),
    }

    sig_path = file_path.parent / (file_path.name + SIG_EXT)
    sig_path.write_text(json.dumps(sig_data, indent=2))

    result = {
        "success": True,
        "file": str(file_path),
        "hash": file_hash,
        "sig_file": str(sig_path),
        "fingerprint": fingerprint(pub_b64),
        "timestamp": sig_data["timestamp"],
    }
    _try_publish(result)
    return result


def sign_directory(dir_path: Path) -> dict:
    dir_path = Path(dir_path).resolve()
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Not a directory: {dir_path}")

    private_key = _load_private_key()
    pub_b64 = get_public_key_b64()
    root_hash, file_hashes = hash_directory(dir_path)
    message = _make_message("dir", dir_path.name, root_hash)
    signature = base64.b64encode(private_key.sign(message)).decode()

    manifest = {
        "trustnet_version": VERSION,
        "kind": "directory",
        "directory": dir_path.name,
        "root_hash": root_hash,
        "hash_algorithm": "sha256",
        "file_count": len(file_hashes),
        "files": file_hashes,
        "signature": signature,
        "public_key": pub_b64,
        "timestamp": int(time.time()),
    }

    manifest_path = dir_path / "trustnet.manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    result = {
        "success": True,
        "directory": str(dir_path),
        "root_hash": root_hash,
        "file_count": len(file_hashes),
        "manifest_file": str(manifest_path),
        "fingerprint": fingerprint(pub_b64),
        "timestamp": manifest["timestamp"],
    }
    _try_publish(result)
    return result


# ── Verification ──────────────────────────────────────────────────────────────

def _verify_signature(pub_b64: str, sig_b64: str, message: bytes) -> bool:
    try:
        pub_raw = base64.b64decode(pub_b64)
        pub_key = Ed25519PublicKey.from_public_bytes(pub_raw)
        pub_key.verify(base64.b64decode(sig_b64), message)
        return True
    except (InvalidSignature, Exception):
        return False


def verify_file(file_path: Path) -> dict:
    file_path = Path(file_path).resolve()

    if str(file_path).endswith(SIG_EXT):
        sig_path = file_path
        original_path = Path(str(file_path)[: -len(SIG_EXT)])
    else:
        sig_path = file_path.parent / (file_path.name + SIG_EXT)
        original_path = file_path

    if not sig_path.exists():
        return {"success": False, "status": "NO_SIGNATURE",
                "message": "No .trustsig file found alongside this file.",
                "file": str(original_path)}

    if not original_path.exists():
        return {"success": False, "status": "FILE_MISSING",
                "message": "Original file is missing.",
                "file": str(original_path)}

    try:
        sig_data = json.loads(sig_path.read_text())
    except json.JSONDecodeError:
        return {"success": False, "status": "CORRUPT_SIGNATURE",
                "message": "Signature file is corrupted or unreadable.",
                "file": str(original_path)}

    current_hash = hash_file(original_path)
    stored_hash = sig_data.get("hash", "")
    hash_ok = current_hash == stored_hash

    pub_b64 = sig_data.get("public_key", "")
    sig_b64 = sig_data.get("signature", "")
    message = _make_message("file", sig_data.get("file", original_path.name), stored_hash)
    sig_ok = _verify_signature(pub_b64, sig_b64, message)

    own_pub = get_public_key_b64()
    is_mine = pub_b64 == own_pub

    if hash_ok and sig_ok:
        status = "VERIFIED"
        success = True
        message_str = "File is authentic and untampered."
    elif not hash_ok:
        status = "TAMPERED"
        success = False
        message_str = "File content has changed since it was signed."
    else:
        status = "INVALID_SIGNATURE"
        success = False
        message_str = "Signature is invalid or was not made with the correct key."

    return {
        "success": success,
        "status": status,
        "message": message_str,
        "file": str(original_path),
        "hash_match": hash_ok,
        "signature_valid": sig_ok,
        "fingerprint": fingerprint(pub_b64) if pub_b64 else "unknown",
        "is_own_key": is_mine,
        "timestamp": sig_data.get("timestamp", 0),
        **_network_trust(stored_hash),
    }


def verify_directory(dir_path: Path) -> dict:
    dir_path = Path(dir_path).resolve()
    manifest_path = dir_path / "trustnet.manifest.json"

    if not manifest_path.exists():
        return {"success": False, "status": "NO_MANIFEST",
                "message": "No trustnet.manifest.json found in this directory.",
                "directory": str(dir_path)}

    try:
        manifest = json.loads(manifest_path.read_text())
    except json.JSONDecodeError:
        return {"success": False, "status": "CORRUPT_MANIFEST",
                "message": "Manifest file is corrupted.",
                "directory": str(dir_path)}

    current_root_hash, current_files = hash_directory(dir_path)
    stored_root_hash = manifest.get("root_hash", "")
    hash_ok = current_root_hash == stored_root_hash

    pub_b64 = manifest.get("public_key", "")
    sig_b64 = manifest.get("signature", "")
    message = _make_message("dir", manifest.get("directory", dir_path.name), stored_root_hash)
    sig_ok = _verify_signature(pub_b64, sig_b64, message)

    changed_files = []
    stored_files = manifest.get("files", {})
    for rel, stored_hash in stored_files.items():
        current = current_files.get(rel)
        if current != stored_hash:
            changed_files.append(rel)
    new_files = [f for f in current_files if f not in stored_files]

    if hash_ok and sig_ok:
        status = "VERIFIED"
        success = True
        message_str = f"All {len(stored_files)} files verified. Directory is untampered."
    elif not hash_ok:
        status = "TAMPERED"
        success = False
        message_str = f"{len(changed_files)} file(s) changed, {len(new_files)} new file(s) added."
    else:
        status = "INVALID_SIGNATURE"
        success = False
        message_str = "Directory signature is invalid."

    return {
        "success": success,
        "status": status,
        "message": message_str,
        "directory": str(dir_path),
        "hash_match": hash_ok,
        "signature_valid": sig_ok,
        "fingerprint": fingerprint(pub_b64) if pub_b64 else "unknown",
        "file_count": len(stored_files),
        "changed_files": changed_files,
        "new_files": new_files,
        "timestamp": manifest.get("timestamp", 0),
        **_network_trust(current_root_hash),
    }


def _network_trust(file_hash: str) -> dict:
    """Query local node for network attestations of this hash."""
    try:
        from trustnet.network.node import query_network
        from trustnet.network.protocol import verify_attestation, fingerprint as fp
        atts = query_network(file_hash)
        valid = [a for a in atts if verify_attestation(a)]
        signers = list({fp(a["public_key"]) for a in valid})
        return {
            "network_attestations": len(valid),
            "network_signers": signers,
            "network_online": True,
        }
    except Exception:
        return {
            "network_attestations": 0,
            "network_signers": [],
            "network_online": False,
        }
