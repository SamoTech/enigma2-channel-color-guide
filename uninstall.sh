#!/bin/sh
#
# uninstall.sh - Channel Colors Plugin Uninstaller
# Enigma 2 | Author: Ossama Hashim (SamoTech)
# License: MIT
# Usage: wget -q "--no-check-certificate" https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/uninstall.sh -O - | sh
#

DEST="/usr/lib/enigma2/python/Plugins/Extensions/ChannelColors"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "${YELLOW}------------------------------------------------------------------------${NC}"
echo "${YELLOW}         Channel Colors Plugin - Uninstaller                           "
echo "${YELLOW}------------------------------------------------------------------------${NC}"
echo ""

if [ ! -d "$DEST" ]; then
    echo "${YELLOW}[INFO] Plugin not found at $DEST - nothing to remove.${NC}"
    exit 0
fi

echo "${RED}[1/2] Removing plugin files from $DEST ...${NC}"
rm -rf "$DEST"

echo "${GREEN}[2/2] Restarting Enigma 2 GUI...${NC}"
killall -9 enigma2 2>/dev/null || true

echo ""
echo "${GREEN}Plugin removed successfully.${NC}"
echo ""
