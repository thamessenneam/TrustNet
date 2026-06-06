# TrustNet

**Decentralized cryptographic file & package trust network.**

Sign any file or folder. Share it. Anyone can verify it hasn't been tampered with — backed by a peer-to-peer network of independent witnesses.

---

## Download

| Platform | Download |
|---|---|
| Windows | [TrustNet-Windows.zip](https://github.com/thamessenneam/trustnet/releases/latest) |
| macOS   | [TrustNet-macOS.zip](https://github.com/thamessenneam/trustnet/releases/latest)   |
| Linux   | [TrustNet-Linux.zip](https://github.com/thamessenneam/trustnet/releases/latest)   |

Or install via pip:
```bash
pip install trustnet
```

---

## What it does

- **Sign** any file or folder with your personal Ed25519 key
- **Verify** files are untampered — locally and across the network
- **Detect** exactly which files in a folder were modified
- **Broadcast** your signatures to a decentralized P2P network
- **Works everywhere** — Windows, macOS, Linux, right-click context menu

---

## How to use

### Right-click (easiest)
After installing, right-click any file or folder in your file manager:

```
Any file or folder
└── TrustNet
    ├── Sign File      ← creates a .trustsig alongside it
    └── Verify File    ← checks if it was tampered
```

### Command line
```bash
trustnet sign   myfile.zip          # sign a file
trustnet verify myfile.zip          # verify a file
trustnet sign   my_project/         # sign an entire folder
trustnet verify my_project/         # verify all files in a folder
trustnet pubkey                     # show your public key
```

### Run the P2P node
```bash
trustnet node start     # starts the background node (port 7337)
trustnet node status    # check if it's running
trustnet node peers     # list connected peers
trustnet node add <ip>  # connect to a remote peer
trustnet node stop      # stop the node
```

Once your node is running, every file you sign is automatically broadcast to all peers. When anyone verifies a file, they see how many independent nodes have attested to it.

---

## How it works

```
You sign a file
  → Ed25519 signature saved to .trustsig
  → attestation published to your local node
  → node propagates to all known peers

Someone verifies the file
  → local: hash re-computed, signature checked
  → network: node queried for independent attestations
  → result: VERIFIED (N signers) or TAMPERED
```

Every attestation is cryptographically signed. Nodes reject any attestation with an invalid signature — it's impossible to fake one without the signer's private key.

---

## Install

### Windows
1. Download `TrustNet-Windows.zip`
2. Extract it
3. Right-click `install.py` → **Run as administrator**
4. Done — right-click any file to see TrustNet

### macOS
```bash
unzip TrustNet-macOS.zip
cd TrustNet-macOS
./install.sh
```

### Linux
```bash
unzip TrustNet-Linux.zip
cd TrustNet-Linux
./install.sh
```

### Via pip (developers)
```bash
pip install trustnet
trustnet keygen    # generate your key
```

---

## First time setup
```bash
trustnet keygen
```
This creates your personal Ed25519 keypair. Your private key stays on your machine — never shared. Your public key is what others use to verify your signatures.

---

## License
MIT — free to use, modify, and distribute.
