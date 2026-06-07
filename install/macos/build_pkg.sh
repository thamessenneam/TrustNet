#!/usr/bin/env bash
# Builds TrustNet-1.0.0.pkg for macOS
# Run on a Mac after PyInstaller builds the binary
set -e

VERSION="1.0.0"
IDENTIFIER="com.thamessenneam.trustnet"
BINARY="../../dist/trustnet"
OUT="../../dist/TrustNet-${VERSION}.pkg"

if [ ! -f "$BINARY" ]; then
    echo "ERROR: Binary not found at $BINARY"
    echo "Run PyInstaller first: pyinstaller --onefile --noconsole trustnet.py"
    exit 1
fi

# Build staging directory
STAGE=$(mktemp -d)
INSTALL_ROOT="$STAGE/root"
SCRIPTS_DIR="$STAGE/scripts"

mkdir -p "$INSTALL_ROOT/usr/local/bin"
mkdir -p "$INSTALL_ROOT/Library/Services/TrustNet Sign.workflow/Contents"
mkdir -p "$INSTALL_ROOT/Library/Services/TrustNet Verify.workflow/Contents"
mkdir -p "$SCRIPTS_DIR"

# Copy binary
cp "$BINARY" "$INSTALL_ROOT/usr/local/bin/trustnet"
chmod +x "$INSTALL_ROOT/usr/local/bin/trustnet"

# Create Quick Action: Sign
cat > "$INSTALL_ROOT/Library/Services/TrustNet Sign.workflow/Contents/document.wflow" << 'WFLOW'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>actions</key>
    <array>
        <dict>
            <key>action</key>
            <dict>
                <key>ActionBundlePath</key>
                <string>/System/Library/Automator/Run Shell Script.action</string>
                <key>ActionParameters</key>
                <dict>
                    <key>COMMAND_STRING</key>
                    <string>for f in "$@"; do /usr/local/bin/trustnet sign "$f"; done</string>
                    <key>shell</key>
                    <string>/bin/bash</string>
                    <key>source</key>
                    <string>pass-input</string>
                </dict>
            </dict>
        </dict>
    </array>
    <key>workflowMetaData</key>
    <dict>
        <key>serviceInputTypeIdentifier</key>
        <string>com.apple.Automator.fileSystemObject</string>
        <key>serviceOutputTypeIdentifier</key>
        <string>com.apple.Automator.nothing</string>
        <key>workflowTypeIdentifier</key>
        <string>com.apple.Automator.servicesMenu</string>
    </dict>
</dict>
</plist>
WFLOW

# Create Quick Action: Verify
sed 's/sign/verify/g' \
    "$INSTALL_ROOT/Library/Services/TrustNet Sign.workflow/Contents/document.wflow" \
    > "$INSTALL_ROOT/Library/Services/TrustNet Verify.workflow/Contents/document.wflow"

# postinstall script — generates keys, starts node
cat > "$SCRIPTS_DIR/postinstall" << 'SCRIPT'
#!/bin/bash
/usr/local/bin/trustnet keygen
/usr/local/bin/trustnet node start

# Create LaunchAgent so node auto-starts on login
PLIST="$HOME/Library/LaunchAgents/com.thamessenneam.trustnet-node.plist"
cat > "$PLIST" << PLIST_CONTENT
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.thamessenneam.trustnet-node</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/trustnet</string>
        <string>node</string>
        <string>start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
PLIST_CONTENT

launchctl load "$PLIST" 2>/dev/null || true
exit 0
SCRIPT

cat > "$SCRIPTS_DIR/preremove" << 'SCRIPT'
#!/bin/bash
/usr/local/bin/trustnet node stop 2>/dev/null || true
launchctl unload "$HOME/Library/LaunchAgents/com.thamessenneam.trustnet-node.plist" 2>/dev/null || true
rm -f "$HOME/Library/LaunchAgents/com.thamessenneam.trustnet-node.plist"
exit 0
SCRIPT

chmod +x "$SCRIPTS_DIR/postinstall" "$SCRIPTS_DIR/preremove"

# Build the .pkg
pkgbuild \
    --root "$INSTALL_ROOT" \
    --scripts "$SCRIPTS_DIR" \
    --identifier "$IDENTIFIER" \
    --version "$VERSION" \
    --install-location "/" \
    "$OUT"

rm -rf "$STAGE"
echo ""
echo "Built: $OUT"
echo "Users install by double-clicking TrustNet-${VERSION}.pkg"
