#!/bin/sh
#
# restore.sh — Channel Colors Plugin — Interactive Restore
# Lists all available backups and lets the user pick one to restore.
#
# Usage: wget -qO- https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/restore.sh | sh
# Or run locally: sh /path/to/restore.sh
#
# Author: Ossama Hashim (SamoTech) | License: MIT
#

BACKUP_ROOT="/etc/enigma2/channelcolors_backups"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo "${YELLOW}╔═════════════════════════════════════════════╗${NC}"
echo "${YELLOW}║  🔄 Channel Colors — Backup Restore Tool      ║${NC}"
echo "${YELLOW}╚═════════════════════════════════════════════╝${NC}"
echo ""

# ── Guard: Enigma 2 only ────────────────────────────────────────────
if [ ! -d "/usr/lib/enigma2" ]; then
    echo "${RED}[ERROR] Enigma 2 not detected.${NC}"
    exit 1
fi

# ── Check backup root exists ─────────────────────────────────────────
if [ ! -d "${BACKUP_ROOT}" ]; then
    echo "${RED}[ERROR] No backups found at ${BACKUP_ROOT}${NC}"
    echo "        Run install.sh first to create a backup."
    exit 1
fi

# ── List available backups ──────────────────────────────────────────
BACKUPS="$(ls -1 ${BACKUP_ROOT} 2>/dev/null)"

if [ -z "${BACKUPS}" ]; then
    echo "${RED}[ERROR] No backup snapshots found inside ${BACKUP_ROOT}${NC}"
    exit 1
fi

echo "${CYAN}Available backups:${NC}"
echo ""
I=1
for B in ${BACKUPS}; do
    MANIFEST_FILE="${BACKUP_ROOT}/${B}/manifest.txt"
    PLUGIN_BAK="no"
    FILE_COUNT=0
    if [ -f "${MANIFEST_FILE}" ]; then
        PLUGIN_BAK="$(grep '^plugin_backup=' ${MANIFEST_FILE} | cut -d= -f2)"
        FILE_COUNT="$(grep -c '^file=' ${MANIFEST_FILE} 2>/dev/null || echo 0)"
    fi
    echo "  ${I}) ${B}  [plugin=${PLUGIN_BAK}, config_files=${FILE_COUNT}]"
    I=$((I + 1))
done

echo ""
echo "${YELLOW}Enter the number of the backup to restore (or 0 to cancel):${NC}"
read CHOICE

if [ "${CHOICE}" = "0" ] || [ -z "${CHOICE}" ]; then
    echo "${YELLOW}Restore cancelled.${NC}"
    exit 0
fi

# ── Resolve chosen backup ────────────────────────────────────────────
I=1
SELECTED_DIR=""
for B in ${BACKUPS}; do
    if [ "${I}" = "${CHOICE}" ]; then
        SELECTED_DIR="${BACKUP_ROOT}/${B}"
        break
    fi
    I=$((I + 1))
done

if [ -z "${SELECTED_DIR}" ]; then
    echo "${RED}[ERROR] Invalid selection.${NC}"
    exit 1
fi

RESTORE_SCRIPT="${SELECTED_DIR}/restore.sh"
if [ ! -f "${RESTORE_SCRIPT}" ]; then
    echo "${RED}[ERROR] restore.sh not found in backup: ${SELECTED_DIR}${NC}"
    exit 1
fi

echo ""
echo "${YELLOW}Restoring from: ${SELECTED_DIR}${NC}"
sh "${RESTORE_SCRIPT}"
