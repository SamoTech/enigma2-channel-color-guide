#!/bin/bash
# install.sh - Channel Colors Plugin Installer
# Author: Ossama Hashim (SamoTech)
# Tested on: OpenATV 7.6 with Fury-FHD skin

set -e

PLUGIN_SRC="./plugin"
PLUGIN_NAME="ChannelColors"

# Auto-detect enigma2 base path
if [ -d "/usr/lib/enigma2" ]; then
    BASE=""
elif [ -d "/media/hdd/ImageBoot" ]; then
    # Find first ImageBoot image
    BASE=$(ls -d /media/hdd/ImageBoot/*/  2>/dev/null | head -1 | sed 's|/$||')
    if [ -z "$BASE" ]; then
        echo "ERROR: No ImageBoot image found"
        exit 1
    fi
    echo "Using ImageBoot: $BASE"
else
    echo "ERROR: Cannot find enigma2 installation"
    exit 1
fi

DEST="$BASE/usr/lib/enigma2/python/Plugins/Extensions/$PLUGIN_NAME"
SKIN_DIR="$BASE/usr/share/enigma2"
SETTINGS="$BASE/etc/enigma2/settings"

echo "=== Channel Colors Installer ==="
echo "Destination: $DEST"

# Create plugin directory
mkdir -p "$DEST"

# Copy plugin files
cp "$PLUGIN_SRC/"*.py "$DEST/"
echo "[OK] Plugin files copied"

# Fix default FTA color in saved settings if white
if [ -f "$SETTINGS" ]; then
    if grep -q 'channelcolors.fta_color=#FFFFFF' "$SETTINGS" 2>/dev/null; then
        sed -i 's/config.plugins.channelcolors.fta_color=#FFFFFF/config.plugins.channelcolors.fta_color=#00C800/' "$SETTINGS"
        echo "[OK] Fixed FTA color in settings (white -> green)"
    fi
fi

# Patch active skin: remove hardcoded foregroundColor=white from channel list widget
# This is required for color changes to take effect
ACTIVE_SKIN=$(grep 'config.skin.primary_skin=' "$SETTINGS" 2>/dev/null | cut -d= -f2 | cut -d/ -f1)
if [ -n "$ACTIVE_SKIN" ]; then
    SKIN_XML="$SKIN_DIR/$ACTIVE_SKIN/skin.xml"
    if [ -f "$SKIN_XML" ]; then
        # Backup skin
        cp "$SKIN_XML" "$SKIN_XML.bak"
        echo "[OK] Skin backed up: $SKIN_XML.bak"

        # Remove foregroundColor=white from service list widget
        python3 << PYEOF
import sys
path = '$SKIN_XML'
try:
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    # Remove foregroundColor="white" only from service list widget (has serviceItemHeight)
    old = 'foregroundColor="white" foregroundColorSelected="#ffffff"'
    new = 'foregroundColorSelected="#ffffff"'
    if old in content:
        content = content.replace(old, new, 1)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print('[OK] Removed foregroundColor=white from skin service list widget')
    else:
        print('[INFO] Skin patch not needed or already applied')
except Exception as e:
    print('[WARN] Skin patch failed: ' + str(e))
PYEOF
    else
        echo "[WARN] Skin XML not found: $SKIN_XML"
    fi
else
    echo "[WARN] Could not detect active skin from settings"
fi

echo ""
echo "=== Installation Complete ==="
echo "Restart enigma2 to activate: killall -9 enigma2"
echo ""
echo "Colors (configurable via Plugins -> Channel Colors):"
echo "  Green  #00C800 = FTA (free-to-air)"
echo "  Red    #FF3232 = Encrypted"
echo "  Gray   #888888 = No signal"
