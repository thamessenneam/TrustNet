#!/usr/bin/env bash
# TrustNet macOS Installer
# Adds TrustNet as a Quick Action (right-click → Quick Actions → TrustNet)
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
    echo "[TrustNet] ERROR: python3 not found. Install Python from python.org"
    exit 1
fi

SERVICES_DIR="$HOME/Library/Services"
mkdir -p "$SERVICES_DIR"

create_quick_action() {
    local NAME="$1"
    local COMMAND="$2"
    local WORKFLOW="$SERVICES_DIR/${NAME}.workflow"
    local CONTENTS="$WORKFLOW/Contents"

    mkdir -p "$CONTENTS"

    cat > "$CONTENTS/document.wflow" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>AMApplicationBuild</key>
    <string>521.1</string>
    <key>AMApplicationVersion</key>
    <string>2.10</string>
    <key>AMDocumentVersion</key>
    <string>2</string>
    <key>actions</key>
    <array>
        <dict>
            <key>action</key>
            <dict>
                <key>AMAccepts</key>
                <dict>
                    <key>Container</key>
                    <string>List</string>
                    <key>Optional</key>
                    <true/>
                    <key>Types</key>
                    <array><string>com.apple.cocoa.path</string></array>
                </dict>
                <key>AMActionVersion</key>
                <string>2.0.3</string>
                <key>AMApplication</key>
                <array><string>Finder</string></array>
                <key>AMParameterProperties</key>
                <dict>
                    <key>COMMAND_STRING</key>
                    <dict/>
                    <key>shell</key>
                    <dict/>
                    <key>source</key>
                    <dict/>
                </dict>
                <key>AMProvides</key>
                <dict>
                    <key>Container</key>
                    <string>List</string>
                    <key>Types</key>
                    <array><string>com.apple.cocoa.path</string></array>
                </dict>
                <key>ActionBundlePath</key>
                <string>/System/Library/Automator/Run Shell Script.action</string>
                <key>ActionName</key>
                <string>Run Shell Script</string>
                <key>ActionParameters</key>
                <dict>
                    <key>COMMAND_STRING</key>
                    <string>for f in "\$@"; do
    "$PYTHON" "$TRUSTNET_PY" $COMMAND "\$f"
done</string>
                    <key>shell</key>
                    <string>/bin/bash</string>
                    <key>source</key>
                    <string>pass-input</string>
                </dict>
                <key>BundleIdentifier</key>
                <string>com.apple.RunShellScript</string>
                <key>CFBundleVersion</key>
                <string>2.0.3</string>
                <key>CanShowSelectedItemsWhenRun</key>
                <false/>
                <key>CanShowWhenRun</key>
                <true/>
                <key>Category</key>
                <array><string>AMCategoryUtilities</string></array>
                <key>Class Name</key>
                <string>RunShellScriptAction</string>
                <key>InputUUID</key>
                <string>$(uuidgen)</string>
                <key>Keywords</key>
                <array><string>Shell</string><string>Script</string><string>Command</string><string>Run</string><string>Unix</string></array>
                <key>OutputUUID</key>
                <string>$(uuidgen)</string>
                <key>ShowWhenRun</key>
                <false/>
                <key>UUID</key>
                <string>$(uuidgen)</string>
                <key>UnlocalizedApplications</key>
                <array><string>Finder</string></array>
                <key>arguments</key>
                <dict>
                    <key>0</key>
                    <dict>
                        <key>default value</key>
                        <integer>0</integer>
                        <key>name</key>
                        <string>inputMethod</string>
                        <key>required</key>
                        <string>0</string>
                        <key>type</key>
                        <string>0</string>
                        <key>uuid</key>
                        <string>0</string>
                    </dict>
                </dict>
                <key>isViewVisible</key>
                <integer>1</integer>
                <key>location</key>
                <string>309.500000:339.000000</string>
                <key>nibPath</key>
                <string>/System/Library/Automator/Run Shell Script.action/Contents/Resources/English.lproj/main.nib</string>
            </dict>
            <key>isViewVisible</key>
            <integer>1</integer>
        </dict>
    </array>
    <key>connectors</key>
    <dict/>
    <key>workflowMetaData</key>
    <dict>
        <key>serviceInputTypeIdentifier</key>
        <string>com.apple.Automator.fileSystemObject</string>
        <key>serviceOutputTypeIdentifier</key>
        <string>com.apple.Automator.nothing</string>
        <key>serviceProcessesInput</key>
        <integer>0</integer>
        <key>workflowTypeIdentifier</key>
        <string>com.apple.Automator.servicesMenu</string>
    </dict>
</dict>
</plist>
EOF

    cat > "$CONTENTS/Info.plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>$NAME</string>
    <key>CFBundleIdentifier</key>
    <string>com.trustnet.${NAME// /}</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>NSServices</key>
    <array>
        <dict>
            <key>NSMenuItem</key>
            <dict>
                <key>default</key>
                <string>$NAME</string>
            </dict>
            <key>NSMessage</key>
            <string>runWorkflowAsService</string>
            <key>NSSendFileTypes</key>
            <array>
                <string>public.item</string>
            </array>
        </dict>
    </array>
</dict>
</plist>
EOF

    echo "  Created: $WORKFLOW"
}

echo "[TrustNet] Installing Quick Actions..."
create_quick_action "TrustNet Sign" "sign"
create_quick_action "TrustNet Verify" "verify"

# Reload services
/System/Library/CoreServices/pbs -update 2>/dev/null || true

echo ""
echo "[TrustNet] Installed successfully!"
echo "  Right-click any file or folder in Finder"
echo "  → Quick Actions → TrustNet Sign / TrustNet Verify"
echo ""
echo "  Note: You may need to enable the actions in:"
echo "  System Settings → Privacy & Security → Extensions → Finder"
