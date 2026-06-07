#!/usr/bin/env bash
# Builds trustnet_1.0.0_amd64.deb for Debian/Ubuntu
set -e

VERSION="1.0.0"
ARCH="amd64"
PACKAGE="trustnet"
BINARY="../../dist/trustnet"
OUT="../../dist/${PACKAGE}_${VERSION}_${ARCH}.deb"

if [ ! -f "$BINARY" ]; then
    echo "ERROR: Binary not found at $BINARY"
    exit 1
fi

STAGE=$(mktemp -d)

# ── Directory structure ───────────────────────────────────────────────────────
mkdir -p "$STAGE/DEBIAN"
mkdir -p "$STAGE/usr/local/bin"
mkdir -p "$STAGE/usr/share/applications"
mkdir -p "$STAGE/usr/share/doc/trustnet"
mkdir -p "$STAGE/usr/share/nautilus-python/extensions" 2>/dev/null || true

# ── Binary ────────────────────────────────────────────────────────────────────
cp "$BINARY" "$STAGE/usr/local/bin/trustnet"
chmod 755 "$STAGE/usr/local/bin/trustnet"

# ── .desktop file ─────────────────────────────────────────────────────────────
cat > "$STAGE/usr/share/applications/trustnet.desktop" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=TrustNet
Comment=Sign and verify files with TrustNet
Exec=trustnet %F
Icon=security-high
Terminal=false
Categories=Utility;Security;
MimeType=application/octet-stream;
Actions=Sign;Verify;

[Desktop Action Sign]
Name=Sign with TrustNet
Exec=trustnet sign %F

[Desktop Action Verify]
Name=Verify with TrustNet
Exec=trustnet verify %F
EOF

# ── Nautilus right-click scripts ──────────────────────────────────────────────
mkdir -p "$STAGE/etc/skel/.local/share/nautilus/scripts"

cat > "$STAGE/etc/skel/.local/share/nautilus/scripts/TrustNet Sign" << 'EOF'
#!/bin/bash
for f in $NAUTILUS_SCRIPT_SELECTED_FILE_PATHS; do
    trustnet sign "$f"
done
EOF

cat > "$STAGE/etc/skel/.local/share/nautilus/scripts/TrustNet Verify" << 'EOF'
#!/bin/bash
for f in $NAUTILUS_SCRIPT_SELECTED_FILE_PATHS; do
    trustnet verify "$f"
done
EOF

chmod +x \
    "$STAGE/etc/skel/.local/share/nautilus/scripts/TrustNet Sign" \
    "$STAGE/etc/skel/.local/share/nautilus/scripts/TrustNet Verify"

# ── Debian control file ───────────────────────────────────────────────────────
cat > "$STAGE/DEBIAN/control" << EOF
Package: $PACKAGE
Version: $VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: Thames Senneam <thamessenneam@github.com>
Homepage: https://github.com/thamessenneam/TrustNet
Description: Decentralized cryptographic file trust network
 Sign any file or folder with Ed25519 cryptography.
 Verify files are untampered locally and across a P2P network.
 Integrates with Nautilus, Thunar, and Dolphin file managers.
EOF

# ── postinst ──────────────────────────────────────────────────────────────────
cat > "$STAGE/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e

# Generate keys for the installing user
if [ -n "$SUDO_USER" ]; then
    sudo -u "$SUDO_USER" trustnet keygen
    sudo -u "$SUDO_USER" trustnet node start
else
    trustnet keygen
    trustnet node start
fi

# Install Nautilus scripts for current user
if [ -n "$SUDO_USER" ]; then
    USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)
    SCRIPTS="$USER_HOME/.local/share/nautilus/scripts"
    mkdir -p "$SCRIPTS"
    cp "/etc/skel/.local/share/nautilus/scripts/TrustNet Sign" "$SCRIPTS/"
    cp "/etc/skel/.local/share/nautilus/scripts/TrustNet Verify" "$SCRIPTS/"
    chmod +x "$SCRIPTS/TrustNet Sign" "$SCRIPTS/TrustNet Verify"
    chown "$SUDO_USER":"$SUDO_USER" "$SCRIPTS/TrustNet Sign" "$SCRIPTS/TrustNet Verify"
fi

update-desktop-database /usr/share/applications 2>/dev/null || true
exit 0
EOF

# ── prerm ─────────────────────────────────────────────────────────────────────
cat > "$STAGE/DEBIAN/prerm" << 'EOF'
#!/bin/bash
trustnet node stop 2>/dev/null || true
exit 0
EOF

chmod 755 "$STAGE/DEBIAN/postinst" "$STAGE/DEBIAN/prerm"

# ── Build .deb ────────────────────────────────────────────────────────────────
dpkg-deb --build --root-owner-group "$STAGE" "$OUT"
rm -rf "$STAGE"

echo ""
echo "Built: $OUT"
echo "Install with: sudo dpkg -i ${PACKAGE}_${VERSION}_${ARCH}.deb"
