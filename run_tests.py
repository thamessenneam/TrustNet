"""TrustNet full network test suite."""
import time
from pathlib import Path
from trustnet.core import sign_file, verify_file, get_public_key_b64
from trustnet.network import client
from trustnet.network.protocol import verify_attestation, build_attestation
from trustnet.network.node import is_running

results = []

def test(name, passed, detail=""):
    results.append((name, passed))
    status = "PASS" if passed else "FAIL"
    suffix = f"  -- {detail}" if detail else ""
    print(f"  [{status}] {name}{suffix}")


print("=" * 55)
print("  TrustNet Network Test Suite")
print("=" * 55)

# ── 1. Node alive ─────────────────────────────────────────
print()
print("[1] Node connectivity")
info = client.get_info("127.0.0.1", 7337)
test("is_running() returns True",      is_running())
test("Node responding on port 7337",   info is not None)
test("Node reports version 1.0.0",     info is not None and info.get("version") == "1.0.0")
test("Node has node_id",               info is not None and bool(info.get("node_id")))

# ── 2. Sign and auto-publish ──────────────────────────────
print()
print("[2] Sign and auto-publish")
Path("suite_test.txt").write_text("TrustNet full test 2026 v3")
r = sign_file(Path("suite_test.txt"))
time.sleep(2)
atts = client.query_attestations("127.0.0.1", 7337, r["hash"])
test("File signed locally",                     r["success"])
test("Attestation auto-published to node",      len(atts) > 0, f"found {len(atts)}")
test("Published attestation signature valid",   len(atts) > 0 and verify_attestation(atts[0]))

# ── 3. Network verify ─────────────────────────────────────
print()
print("[3] Verify with network layer")
v = verify_file(Path("suite_test.txt"))
n_atts = v["network_attestations"]
n_sig  = v["network_signers"]
test("Local verify: VERIFIED",              v["status"] == "VERIFIED")
test("Network is online",                   v["network_online"])
test("Network shows >= 1 attestation",      n_atts >= 1, str(n_atts))
test("Network shows signer fingerprint",    len(n_sig) >= 1)

# ── 4. Security: reject fakes ─────────────────────────────
print()
print("[4] Security: reject invalid attestations")
att = build_attestation(r, get_public_key_b64())

bad_hash = dict(att); bad_hash["file_hash"] = "a" * 64
test("Tampered hash rejected",
     not client.submit_attestation("127.0.0.1", 7337, bad_hash))

bad_sig = dict(att); bad_sig["signature"] = "A" * 88 + "=="
test("Fake signature rejected",
     not client.submit_attestation("127.0.0.1", 7337, bad_sig))

fake = {
    "kind": "file", "filename": "evil.zip", "file_hash": "b" * 64,
    "signature": "C" * 88 + "==", "public_key": "D" * 44 + "==",
    "timestamp": 0, "node_id": "hacker",
}
test("Fabricated attestation rejected",
     not client.submit_attestation("127.0.0.1", 7337, fake))

# ── 5. Sync endpoint ──────────────────────────────────────
print()
print("[5] Peer sync protocol")
sync_all  = client.sync_since("127.0.0.1", 7337, 0)
sync_none = client.sync_since("127.0.0.1", 7337, int(time.time()) + 99999)
test("Sync returns all records",                    len(sync_all) > 0, f"{len(sync_all)} records")
test("All synced records cryptographically valid",  all(verify_attestation(a) for a in sync_all))
test("Future timestamp returns empty",              len(sync_none) == 0)

# ── 6. Ledger deduplication (via HTTP API) ────────────────
print()
print("[6] Ledger deduplication")
# Submit the same valid attestation twice via the HTTP API
r1 = client.submit_attestation("127.0.0.1", 7337, att)  # already exists
info_before = client.get_info("127.0.0.1", 7337)
r2 = client.submit_attestation("127.0.0.1", 7337, att)  # submit again
info_after  = client.get_info("127.0.0.1", 7337)
test("Duplicate attestation not double-stored",
     info_before["attestations"] == info_after["attestations"])

# ── 7. Peer management ────────────────────────────────────
print()
print("[7] Peer management")
ok    = client.register_peer("127.0.0.1", 7337, "10.0.0.99", 7337)
peers = client.get_peers("127.0.0.1", 7337)
test("Peer registration accepted",  ok)
test("Peer appears in peer list",   any(p["host"] == "10.0.0.99" for p in peers))

# ── 8. Tamper detection with network ──────────────────────
print()
print("[8] Tamper detection (local + network)")
Path("suite_test.txt").write_text("TAMPERED CONTENT — attacker modified this")
v2 = verify_file(Path("suite_test.txt"))
test("Tampered file caught locally",        v2["status"] == "TAMPERED")
test("Network still holds original record", v2.get("network_attestations", 0) >= 1)

# ── Summary ───────────────────────────────────────────────
print()
print("=" * 55)
passed = sum(1 for _, p in results if p)
total  = len(results)
print(f"  Result: {passed}/{total} tests passed")
if passed == total:
    print("  All systems operational.")
else:
    print("  FAILURES:")
    for name, p in results:
        if not p:
            print(f"    - {name}")
print("=" * 55)
