#!/bin/sh
#
# install.sh — Channel Colors Plugin Installer
# Enigma 2 | Author: Ossama Hashim (SamoTech)
# License: MIT
# Usage: wget -q "--no-check-certificate" https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/install.sh -O - | sh
#

set -e

# ── Config ────────────────────────────────────────────────────────────
REPO="https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/plugin"
DEST="/usr/lib/enigma2/python/Plugins/Extensions/ChannelColors"
BACKUP_ROOT="/etc/enigma2/channelcolors_backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${BACKUP_ROOT}/${TIMESTAMP}"
MANIFEST="${BACKUP_DIR}/manifest.txt"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# ── Files that may be modified by this plugin ───────────────────────────
TARGET_FILES="
/etc/enigma2/settings
/etc/enigma2/skin.xml
"

# ── Banner ──────────────────────────────────────────────────────────
echo ""
echo "${YELLOW}------------------------------------------------------------------------${NC}"
echo "${YELLOW}         Channel Colors Plugin - Installer v1.2                        "
echo "${YELLOW}         github.com/SamoTech/enigma2-channel-color-guide               "
echo "${YELLOW}------------------------------------------------------------------------${NC}"
echo ""

# ── Guard: must run on Enigma 2 ─────────────────────────────────────────
if [ ! -d "/usr/lib/enigma2" ]; then
    echo "${RED}[ERROR] Enigma 2 not detected. Run this script on your receiver.${NC}"
    exit 1
fi

# ── Downloader: always use wget --no-check-certificate (Enigma2 standard) ──
if ! command -v wget > /dev/null 2>&1; then
    echo "${RED}[ERROR] wget not found. Cannot continue.${NC}"
    exit 1
fi

# Download function — matches Enigma2 receiver wget style
fetch() {
    wget -q "--no-check-certificate" "$2" -O "$1"
}

# ────────────────────────────────────────────────────────────────────
# STEP 1 — FULL BACKUP
# ────────────────────────────────────────────────────────────────────
echo "${CYAN}[1/5] Creating backup - snapshot: ${TIMESTAMP}${NC}"
mkdir -p "${BACKUP_DIR}/plugin" "${BACKUP_DIR}/config"

# Write manifest header
cat > "${MANIFEST}" <<EOF
# Channel Colors Plugin - Backup Manifest
# Created : ${TIMESTAMP}
# Restore : sh /etc/enigma2/channelcolors_backups/${TIMESTAMP}/restore.sh
# -------------------------------------------------------
EOF

# Backup existing plugin files (if any)
if [ -d "${DEST}" ]; then
    cp -r "${DEST}/" "${BACKUP_DIR}/plugin/"
    echo "plugin_backup=yes" >> "${MANIFEST}"
    echo "      -> Plugin dir backed up"
else
    echo "plugin_backup=no" >> "${MANIFEST}"
    echo "      -> No previous plugin installation found"
fi

# Backup config/skin files that may be modified
for FILE in ${TARGET_FILES}; do
    if [ -f "${FILE}" ]; then
        SAFE_NAME="$(echo ${FILE} | tr '/' '_')"
        cp "${FILE}" "${BACKUP_DIR}/config/${SAFE_NAME}"
        echo "file=${FILE}" >> "${MANIFEST}"
        echo "      -> Backed up: ${FILE}"
    fi
done

# Write restore script into the backup directory
cat > "${BACKUP_DIR}/restore.sh" <<'RESTORE_EOF'
#!/bin/sh
#
# restore.sh - Auto-generated restore script
# Run: sh /etc/enigma2/channelcolors_backups/<TIMESTAMP>/restore.sh
#

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MANIFEST="${SCRIPT_DIR}/manifest.txt"
PLUGIN_DEST="/usr/lib/enigma2/python/Plugins/Extensions/ChannelColors"

echo ""
echo "${YELLOW}------------------------------------------------------------------------${NC}"
echo "${YELLOW}         Channel Colors Plugin - Restore                               "
echo "${YELLOW}------------------------------------------------------------------------${NC}"
echo ""

if [ ! -f "${MANIFEST}" ]; then
    echo "${RED}[ERROR] manifest.txt not found in ${SCRIPT_DIR}${NC}"
    exit 1
fi

# Step 1: Remove current plugin
echo "${GREEN}[1/3] Removing current plugin...${NC}"
rm -rf "${PLUGIN_DEST}"

# Step 2: Restore plugin files
PLUGIN_BACKED=$(grep '^plugin_backup=' "${MANIFEST}" | cut -d= -f2)
if [ "${PLUGIN_BACKED}" = "yes" ]; then
    echo "${GREEN}[2/3] Restoring plugin files...${NC}"
    cp -r "${SCRIPT_DIR}/plugin/" "${PLUGIN_DEST}/"
    chmod 644 "${PLUGIN_DEST}"/*.py 2>/dev/null || true
    echo "      -> Plugin restored to ${PLUGIN_DEST}"
else
    echo "${YELLOW}[2/3] No previous plugin to restore (fresh install was made).${NC}"
fi

# Step 3: Restore config/skin files
echo "${GREEN}[3/3] Restoring config files...${NC}"
grep '^file=' "${MANIFEST}" | cut -d= -f2 | while read ORIG_FILE; do
    SAFE_NAME="$(echo ${ORIG_FILE} | tr '/' '_')"
    BACKED_FILE="${SCRIPT_DIR}/config/${SAFE_NAME}"
    if [ -f "${BACKED_FILE}" ]; then
        cp "${BACKED_FILE}" "${ORIG_FILE}"
        echo "      -> Restored: ${ORIG_FILE}"
    else
        echo "${YELLOW}      [WARN] Backup file not found: ${BACKED_FILE}${NC}"
    fi
done

# Restart GUI
echo ""
echo "${GREEN}Restarting Enigma 2 GUI...${NC}"
killall -9 enigma2 2>/dev/null || true

echo ""
echo "${GREEN}Restore complete! System returned to previous state.${NC}"
echo ""
RESTORE_EOF

chmod +x "${BACKUP_DIR}/restore.sh"
echo "      -> restore.sh written"
echo "      -> Backup saved at: ${BACKUP_DIR}"

# ────────────────────────────────────────────────────────────────────
# STEP 2 — CREATE PLUGIN DIR
# ────────────────────────────────────────────────────────────────────
echo "${GREEN}[2/5] Creating plugin directory...${NC}"
mkdir -p "${DEST}"

# ────────────────────────────────────────────────────────────────────
# STEP 3 — DOWNLOAD PLUGIN FILES
# ────────────────────────────────────────────────────────────────────
echo "${GREEN}[3/5] Downloading plugin files from GitHub...${NC}"

FILES="__init__.py plugin.py ChannelColorsSetup.py ColorApplier.py"
for FILE in ${FILES}; do
    echo "      -> ${FILE}"
    fetch "${DEST}/${FILE}" "${REPO}/${FILE}"
    if [ $? -ne 0 ]; then
        echo "${RED}[ERROR] Failed to download ${FILE}${NC}"
        exit 1
    fi
done

# ────────────────────────────────────────────────────────────────────
# STEP 4 — SET PERMISSIONS
# ────────────────────────────────────────────────────────────────────
echo "${GREEN}[4/5] Setting permissions...${NC}"
chmod 644 "${DEST}"/*.py
chown root:root "${DEST}"/*.py 2>/dev/null || true

# ────────────────────────────────────────────────────────────────────
# STEP 5 — RESTART GUI
# ────────────────────────────────────────────────────────────────────
echo "${GREEN}[5/5] Restarting Enigma 2 GUI...${NC}"
killall -9 enigma2 2>/dev/null || true

# ── Done ─────────────────────────────────────────────────────────────────
sleep 1
echo ""
echo "${GREEN}------------------------------------------------------------------------${NC}"
echo "${GREEN}   Installation complete!                                              "
echo "${GREEN}   Go to : Menu -> Plugins -> Channel Colors                          "
echo "${GREEN}   Backup : ${BACKUP_DIR}                   "
echo "${GREEN}   Restore: sh ${BACKUP_DIR}/restore.sh     "
echo "${GREEN}------------------------------------------------------------------------${NC}"
echo ""
