#!/bin/sh
# uninstall.sh - Channel Colors Plugin Uninstaller
# Author: Ossama Hashim (SamoTech)
#
# Usage:
#   wget -q "--no-check-certificate" https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/uninstall.sh -O - | sh
#

PLUGIN_NAME="ChannelColors"

# Auto-detect enigma2 base path
if [ -d "/usr/lib/enigma2" ]; then
    BASE=""
else
    BASE=$(ls -d /media/hdd/ImageBoot/*/  2>/dev/null | head -1 | sed 's|/$||')
fi

DEST="$BASE/usr/lib/enigma2/python/Plugins/Extensions/$PLUGIN_NAME"
SETTINGS="$BASE/etc/enigma2/settings"

echo ""
echo "=== Channel Colors Uninstaller ==="

# Remove plugin
if [ -d "$DEST" ]; then
    rm -rf "$DEST"
    echo "[OK] Plugin removed: $DEST"
else
    echo "[INFO] Plugin not found at: $DEST"
fi

# Restore skin backup if exists
ACTIVE_SKIN=$(grep 'config.skin.primary_skin=' "$SETTINGS" 2>/dev/null | cut -d= -f2 | cut -d/ -f1)
if [ -n "$ACTIVE_SKIN" ]; then
    SKIN_BAK="$BASE/usr/share/enigma2/$ACTIVE_SKIN/skin.xml.bak"
    SKIN_XML="$BASE/usr/share/enigma2/$ACTIVE_SKIN/skin.xml"
    if [ -f "$SKIN_BAK" ]; then
        cp "$SKIN_BAK" "$SKIN_XML"
        echo "[OK] Skin restored from backup"
    else
        echo "[INFO] No skin backup found, skipping skin restore"
    fi
fi

echo ""
echo "[INFO] Restart enigma2: killall -9 enigma2"
