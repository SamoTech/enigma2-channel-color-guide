#!/bin/sh
#
# install.sh — Channel Colors Plugin Installer
# Enigma 2 | Author: Ossama Hashim (SamoTech)
# Usage: wget -qO- https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/install.sh | sh
#

set -e

REPO="https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/plugin"
DEST="/usr/lib/enigma2/python/Plugins/Extensions/ChannelColors"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "${YELLOW}================================================${NC}"
echo "${YELLOW}   Channel Colors Plugin — Installer v1.0      ${NC}"
echo "${YELLOW}   github.com/SamoTech/enigma2-channel-color-guide ${NC}"
echo "${YELLOW}================================================${NC}"
echo ""

# ── Check we're on Enigma 2 ────────────────────────────────────────────────
if [ ! -d "/usr/lib/enigma2" ]; then
    echo "${RED}[ERROR] Enigma 2 not detected. Run this on your receiver.${NC}"
    exit 1
fi

# ── Check wget or curl ────────────────────────────────────────────────────
if command -v wget > /dev/null 2>&1; then
    FETCH="wget -qO"
elif command -v curl > /dev/null 2>&1; then
    FETCH="curl -fsSL -o"
else
    echo "${RED}[ERROR] Neither wget nor curl found.${NC}"
    exit 1
fi

# ── Backup existing installation ──────────────────────────────────────────
if [ -d "$DEST" ]; then
    BACKUP="${DEST}_backup_$(date +%Y%m%d_%H%M%S)"
    echo "${YELLOW}[INFO] Existing installation found. Backing up to:${NC}"
    echo "       $BACKUP"
    cp -r "$DEST" "$BACKUP"
fi

# ── Create destination directory ──────────────────────────────────────────
echo "${GREEN}[1/4] Creating plugin directory...${NC}"
mkdir -p "$DEST"

# ── Download plugin files ─────────────────────────────────────────────────
echo "${GREEN}[2/4] Downloading plugin files from GitHub...${NC}"

FILES="__init__.py plugin.py ChannelColorsSetup.py ColorApplier.py"

for FILE in $FILES; do
    echo "      → $FILE"
    $FETCH "${DEST}/${FILE}" "${REPO}/${FILE}"
done

# ── Set permissions ───────────────────────────────────────────────────────
echo "${GREEN}[3/4] Setting permissions...${NC}"
chmod 644 "${DEST}"/*.py
chown root:root "${DEST}"/*.py 2>/dev/null || true

# ── Restart Enigma 2 GUI ──────────────────────────────────────────────────
echo "${GREEN}[4/4] Restarting Enigma 2 GUI...${NC}"
if command -v init > /dev/null 2>&1; then
    init 4 && sleep 3 && init 3
else
    echo "${YELLOW}[WARN] Could not auto-restart. Please restart GUI manually.${NC}"
fi

echo ""
echo "${GREEN}================================================${NC}"
echo "${GREEN}  Installation complete!                       ${NC}"
echo "${GREEN}  Go to: Menu → Plugins → Channel Colors       ${NC}"
echo "${GREEN}================================================${NC}"
echo ""
