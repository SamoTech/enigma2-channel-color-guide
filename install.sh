#!/bin/sh
#
# install.sh — Channel Colors Plugin Installer
# Enigma 2 | Author: Ossama Hashim (SamoTech)
# License: MIT
# Usage: wget -q "--no-check-certificate" https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/install.sh -O - | sh
#

# NOTE: no 'set -e' — we handle errors manually so partial failures don't silently abort

# Colors via tput — works on OpenATV busybox ash
if command -v tput > /dev/null 2>&1 && tput setaf 1 > /dev/null 2>&1; then
    GREEN=$(tput setaf 2)
    RED=$(tput setaf 1)
    YELLOW=$(tput setaf 3)
    CYAN=$(tput setaf 6)
    NC=$(tput sgr0)
else
    GREEN=''
    RED=''
    YELLOW=''
    CYAN=''
    NC=''
fi

# ── Config ────────────────────────────────────────────────────────────────────
REPO="https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/plugin"
DEST="/usr/lib/enigma2/python/Plugins/Extensions/ChannelColors"
BACKUP_ROOT="/etc/enigma2/channelcolors_backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="${BACKUP_ROOT}/${TIMESTAMP}"
MANIFEST="${BACKUP_DIR}/manifest.txt"

TARGET_FILES="
/etc/enigma2/settings
/etc/enigma2/skin.xml
"

# ── Banner ────────────────────────────────────────────────────────────────────
echo ""
echo "${YELLOW}------------------------------------------------------------------------${NC}"
echo "${YELLOW}         Channel Colors Plugin - Installer v1.3                        ${NC}"
echo "${YELLOW}         github.com/SamoTech/enigma2-channel-color-guide               ${NC}"
echo "${YELLOW}------------------------------------------------------------------------${NC}"
echo ""

# ── Guard: must run on Enigma 2 ───────────────────────────────────────────
if [ ! -d "/usr/lib/enigma2" ]; then
    echo "${RED}[ERROR] Enigma 2 not detected. Run this on your receiver.${NC}"
    exit 1
fi

if ! command -v wget > /dev/null 2>&1; then
    echo "${RED}[ERROR] wget not found.${NC}"
    exit 1
fi

fetch() {
    wget -q "--no-check-certificate" "$2" -O "$1"
}

# ────────────────────────────────────────────────────────────────────
# STEP 1 — BACKUP
# ────────────────────────────────────────────────────────────────────
echo "${CYAN}[1/5] Creating backup - snapshot: ${TIMESTAMP}${NC}"
mkdir -p "${BACKUP_DIR}/plugin" "${BACKUP_DIR}/config"

cat > "${MANIFEST}" <<EOF
# Channel Colors Plugin - Backup Manifest
# Created : ${TIMESTAMP}
EOF

if [ -d "${DEST}" ]; then
    cp -r "${DEST}/" "${BACKUP_DIR}/plugin/"
    echo "plugin_backup=yes" >> "${MANIFEST}"
    echo "      -> Plugin dir backed up"
else
    echo "plugin_backup=no" >> "${MANIFEST}"
    echo "      -> No previous plugin found"
fi

for FILE in ${TARGET_FILES}; do
    if [ -f "${FILE}" ]; then
        SAFE_NAME="$(echo ${FILE} | tr '/' '_')"
        cp "${FILE}" "${BACKUP_DIR}/config/${SAFE_NAME}"
        echo "file=${FILE}" >> "${MANIFEST}"
        echo "      -> Backed up: ${FILE}"
    fi
done

cat > "${BACKUP_DIR}/restore.sh" <<RESTORE_EOF
#!/bin/sh
if command -v tput > /dev/null 2>&1 && tput setaf 1 > /dev/null 2>&1; then
    GREEN=\$(tput setaf 2); RED=\$(tput setaf 1); YELLOW=\$(tput setaf 3); NC=\$(tput sgr0)
else
    GREEN=''; RED=''; YELLOW=''; NC=''
fi
SCRIPT_DIR="\$(cd "\$(dirname "\$0")" && pwd)"
MANIFEST="\${SCRIPT_DIR}/manifest.txt"
PLUGIN_DEST="/usr/lib/enigma2/python/Plugins/Extensions/ChannelColors"
echo ""
echo "\${YELLOW}--- Channel Colors Restore ---\${NC}"
echo ""
rm -rf "\${PLUGIN_DEST}"
PLUGIN_BACKED=\$(grep '^plugin_backup=' "\${MANIFEST}" | cut -d= -f2)
if [ "\${PLUGIN_BACKED}" = "yes" ]; then
    cp -r "\${SCRIPT_DIR}/plugin/" "\${PLUGIN_DEST}/"
    echo "\${GREEN}Plugin restored.\${NC}"
fi
grep '^file=' "\${MANIFEST}" | cut -d= -f2 | while read ORIG_FILE; do
    SAFE_NAME="\$(echo \${ORIG_FILE} | tr '/' '_')"
    BACKED="\${SCRIPT_DIR}/config/\${SAFE_NAME}"
    [ -f "\${BACKED}" ] && cp "\${BACKED}" "\${ORIG_FILE}" && echo "\${GREEN}Restored: \${ORIG_FILE}\${NC}"
done
killall -9 enigma2 2>/dev/null || true
echo "\${GREEN}Restore complete.\${NC}"
RESTORE_EOF

chmod +x "${BACKUP_DIR}/restore.sh"
echo "      -> restore.sh written"
echo "      -> Backup: ${BACKUP_DIR}"

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
    if [ $? -ne 0 ] || [ ! -s "${DEST}/${FILE}" ]; then
        echo "${RED}[ERROR] Failed to download ${FILE}${NC}"
        exit 1
    fi
done

# ────────────────────────────────────────────────────────────────────
# STEP 4 — PERMISSIONS
# ────────────────────────────────────────────────────────────────────
echo "${GREEN}[4/5] Setting permissions...${NC}"
chmod 644 "${DEST}"/*.py
chown root:root "${DEST}"/*.py 2>/dev/null || true

# ────────────────────────────────────────────────────────────────────
# STEP 5 — RESTART
# ────────────────────────────────────────────────────────────────────
echo "${GREEN}[5/5] Restarting Enigma2...${NC}"
killall -9 enigma2 2>/dev/null || true

sleep 1
echo ""
echo "${GREEN}------------------------------------------------------------------------${NC}"
echo "${GREEN}   Installation complete! v1.3                                         ${NC}"
echo "${GREEN}   Menu -> Plugins -> Channel Colors                                   ${NC}"
echo "${GREEN}   Backup : ${BACKUP_DIR}${NC}"
echo "${GREEN}   Restore: sh ${BACKUP_DIR}/restore.sh${NC}"
echo "${GREEN}------------------------------------------------------------------------${NC}"
echo ""
