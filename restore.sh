#!/bin/sh
# restore.sh - Channel Colors Plugin - Skin Restore Tool
# Author: Ossama Hashim (SamoTech)
#
# Usage:
#   wget -q "--no-check-certificate" https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/restore.sh -O - | sh
#

SETTINGS_LIVE="/etc/enigma2/settings"

# Auto-detect enigma2 base path
if [ -d "/usr/lib/enigma2" ]; then
    BASE=""
    SETTINGS="$SETTINGS_LIVE"
else
    BASE=$(ls -d /media/hdd/ImageBoot/*/  2>/dev/null | head -1 | sed 's|/$||')
    SETTINGS="$BASE/etc/enigma2/settings"
fi

echo ""
echo "=== Channel Colors - Skin Restore Tool ==="

if [ ! -d "/usr/lib/enigma2" ] && [ -z "$BASE" ]; then
    echo "[ERROR] Enigma2 not detected."
    exit 1
fi

# Detect active skin
ACTIVE_SKIN=$(grep 'config.skin.primary_skin=' "$SETTINGS" 2>/dev/null | cut -d= -f2 | cut -d/ -f1)
if [ -z "$ACTIVE_SKIN" ]; then
    echo "[ERROR] Could not detect active skin from settings"
    exit 1
fi

SKIN_XML="$BASE/usr/share/enigma2/$ACTIVE_SKIN/skin.xml"
SKIN_BAK="$SKIN_XML.bak"

echo "[INFO] Active skin: $ACTIVE_SKIN"
echo "[INFO] Skin path:   $SKIN_XML"

if [ ! -f "$SKIN_BAK" ]; then
    echo "[ERROR] No backup found at: $SKIN_BAK"
    echo "        Run install.sh first to create a backup before patching."
    exit 1
fi

echo ""
echo "Restore skin from backup? (yes/no)"
read CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "[INFO] Restore cancelled."
    exit 0
fi

cp "$SKIN_BAK" "$SKIN_XML"
echo "[OK] Skin restored from: $SKIN_BAK"
echo ""
echo "[INFO] Restart enigma2: killall -9 enigma2"
