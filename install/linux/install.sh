#!/usr/bin/env bash
# TrustNet Linux Installer
# Adds right-click context menu to Nautilus (GNOME), Thunar (XFCE), Dolphin (KDE)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TRUSTNET_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TRUSTNET_PY="$TRUSTNET_ROOT/trustnet.py"
PYTHON="$(which python3)"

if [ ! -f "$TRUSTNET_PY" ]; then
    echo "[TrustNet] ERROR: trustnet.py not found at $TRUSTNET_PY"
    exit 1
fi

if [ -z "$PYTHON" ]; then
    echo "[TrustNet] ERROR: python3 not found."
    exit 1
fi

echo "[TrustNet] Detecting desktop environment..."

INSTALLED=0

# ── Nautilus (GNOME / Ubuntu) ─────────────────────────────────────────────────
install_nautilus() {
    local SCRIPTS_DIR="$HOME/.local/share/nautilus/scripts"
    mkdir -p "$SCRIPTS_DIR"

    cat > "$SCRIPTS_DIR/TrustNet Sign" <<EOF
#!/usr/bin/env bash
for f in \$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS; do
    "$PYTHON" "$TRUSTNET_PY" sign "\$f"
done
EOF

    cat > "$SCRIPTS_DIR/TrustNet Verify" <<EOF
#!/usr/bin/env bash
for f in \$NAUTILUS_SCRIPT_SELECTED_FILE_PATHS; do
    "$PYTHON" "$TRUSTNET_PY" verify "\$f"
done
EOF

    chmod +x "$SCRIPTS_DIR/TrustNet Sign"
    chmod +x "$SCRIPTS_DIR/TrustNet Verify"
    echo "  [Nautilus] Scripts installed at: $SCRIPTS_DIR"
    INSTALLED=1
}

# ── Thunar (XFCE) ─────────────────────────────────────────────────────────────
install_thunar() {
    # Thunar uses XML config for custom actions
    local CONFIG="$HOME/.config/Thunar/uca.xml"
    mkdir -p "$(dirname "$CONFIG")"

    if [ ! -f "$CONFIG" ]; then
        cat > "$CONFIG" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<actions>
</actions>
EOF
    fi

    # Inject actions if not already present
    if ! grep -q "TrustNet" "$CONFIG" 2>/dev/null; then
        local TMP=$(mktemp)
        sed '/<\/actions>/i\
    <action>\
        <icon>security-high</icon>\
        <name>TrustNet Sign</name>\
        <unique-id>trustnet-sign-1</unique-id>\
        <command>'"$PYTHON"' '"$TRUSTNET_PY"' sign %f</command>\
        <description>Sign with TrustNet</description>\
        <patterns>*</patterns>\
        <directories/>\
        <audio-files/>\
        <image-files/>\
        <other-files/>\
        <text-files/>\
        <video-files/>\
    </action>\
    <action>\
        <icon>security-high</icon>\
        <name>TrustNet Verify</name>\
        <unique-id>trustnet-verify-1</unique-id>\
        <command>'"$PYTHON"' '"$TRUSTNET_PY"' verify %f</command>\
        <description>Verify with TrustNet</description>\
        <patterns>*</patterns>\
        <directories/>\
        <audio-files/>\
        <image-files/>\
        <other-files/>\
        <text-files/>\
        <video-files/>\
    </action>' "$CONFIG" > "$TMP" && mv "$TMP" "$CONFIG"
    fi

    echo "  [Thunar] Custom actions installed at: $CONFIG"
    INSTALLED=1
}

# ── Dolphin (KDE) ─────────────────────────────────────────────────────────────
install_dolphin() {
    local SERVICES_DIR="$HOME/.local/share/kio/servicemenus"
    mkdir -p "$SERVICES_DIR"

    cat > "$SERVICES_DIR/trustnet.desktop" <<EOF
[Desktop Entry]
Type=Service
ServiceTypes=KonqPopupMenu/Plugin
MimeType=all/all;
Actions=trustnet_sign;trustnet_verify;
X-KDE-Priority=TopLevel

[Desktop Action trustnet_sign]
Name=TrustNet Sign
Icon=security-high
Exec=$PYTHON $TRUSTNET_PY sign %F

[Desktop Action trustnet_verify]
Name=TrustNet Verify
Icon=security-high
Exec=$PYTHON $TRUSTNET_PY verify %F
EOF

    echo "  [Dolphin] Service menu installed at: $SERVICES_DIR/trustnet.desktop"
    INSTALLED=1
}

# ── .desktop file (universal fallback) ───────────────────────────────────────
install_desktop_file() {
    local APP_DIR="$HOME/.local/share/applications"
    mkdir -p "$APP_DIR"

    cat > "$APP_DIR/trustnet.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=TrustNet
Comment=Sign and verify files with TrustNet
Exec=$PYTHON $TRUSTNET_PY %F
Icon=security-high
Terminal=false
Categories=Utility;Security;
MimeType=application/octet-stream;
EOF

    update-desktop-database "$APP_DIR" 2>/dev/null || true
    echo "  [Desktop] Application entry installed: $APP_DIR/trustnet.desktop"
}

# ── Install based on what's available ────────────────────────────────────────
if command -v nautilus &>/dev/null || [ -d "$HOME/.local/share/nautilus" ]; then
    install_nautilus
fi

if command -v thunar &>/dev/null || [ -f "$HOME/.config/Thunar/uca.xml" ]; then
    install_thunar
fi

if command -v dolphin &>/dev/null || [ -d "$HOME/.local/share/kio" ]; then
    install_dolphin
fi

install_desktop_file

if [ "$INSTALLED" -eq 0 ]; then
    echo "[TrustNet] No supported file manager found."
    echo "  TrustNet is still available via command line:"
    echo "    python3 $TRUSTNET_PY sign <file>"
    echo "    python3 $TRUSTNET_PY verify <file>"
else
    echo ""
    echo "[TrustNet] Installed! Restart your file manager to see the menu."
    echo "  CLI also available: python3 $TRUSTNET_PY sign/verify <file>"
fi

# ── Optional: add to PATH ────────────────────────────────────────────────────
WRAPPER="/usr/local/bin/trustnet"
if [ -w "/usr/local/bin" ] || sudo -n true 2>/dev/null; then
    echo ""
    read -p "Add 'trustnet' command to /usr/local/bin? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo tee "$WRAPPER" > /dev/null <<EOF
#!/usr/bin/env bash
$PYTHON $TRUSTNET_PY "\$@"
EOF
        sudo chmod +x "$WRAPPER"
        echo "  Added: trustnet command available globally"
    fi
fi
