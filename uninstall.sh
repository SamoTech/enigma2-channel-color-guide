#!/bin/sh
#
# uninstall.sh — Channel Colors Plugin Uninstaller
# Enigma 2 | Author: Ossama Hashim (SamoTech)
#

DEST="/usr/lib/enigma2/python/Plugins/Extensions/ChannelColors"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "${YELLOW}================================================${NC}"
echo "${YELLOW}   Channel Colors Plugin — Uninstaller         ${NC}"
echo "${YELLOW}================================================${NC}"
echo ""

if [ ! -d "$DEST" ]; then
    echo "${YELLOW}[INFO] Plugin not found at $DEST — nothing to remove.${NC}"
    exit 0
fi

echo "${RED}[1/2] Removing plugin files from $DEST ...${NC}"
rm -rf "$DEST"

echo "${GREEN}[2/2] Restarting Enigma 2 GUI...${NC}"
if command -v init > /dev/null 2>&1; then
    init 4 && sleep 3 && init 3
else
    echo "${YELLOW}[WARN] Could not auto-restart. Please restart GUI manually.${NC}"
fi

echo ""
echo "${GREEN}Plugin removed successfully.${NC}"
echo ""
