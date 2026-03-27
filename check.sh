#!/bin/sh
#
# check.sh - Channel Colors Plugin - Pre-Install Checker
# Author: Ossama Hashim (SamoTech)
# License: MIT
# Usage: wget -q "--no-check-certificate" https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/check.sh -O - | sh
#

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

ok()   { echo "${GREEN}  [PASS] $1${NC}"; PASS=$((PASS+1)); }
fail() { echo "${RED}  [FAIL] $1${NC}"; FAIL=$((FAIL+1)); }
warn() { echo "${YELLOW}  [WARN] $1${NC}"; WARN=$((WARN+1)); }
info() { echo "${CYAN}  [INFO] $1${NC}"; }

echo ""
echo "------------------------------------------------------------------------"
echo "         Channel Colors Plugin - Pre-Install Checker                   "
echo "         github.com/SamoTech/enigma2-channel-color-guide               "
echo "------------------------------------------------------------------------"
echo ""

# ── 1. Enigma2 installed ────────────────────────────────────────────────────
echo "[1] Enigma2 Environment"
if [ -d "/usr/lib/enigma2" ]; then
    ok "Enigma2 directory found at /usr/lib/enigma2"
else
    fail "Enigma2 not found - run this on your receiver"
fi

if [ -f "/etc/enigma2/settings" ]; then
    ok "Settings file found at /etc/enigma2/settings"
else
    fail "Settings file missing at /etc/enigma2/settings"
fi

# ── 2. Image version ────────────────────────────────────────────────────────
echo ""
echo "[2] Image Info"
if [ -f "/etc/image-version" ]; then
    IMAGE=$(cat /etc/image-version)
    info "Image : $IMAGE"
    ok "Image version file found"
elif [ -f "/etc/os-release" ]; then
    IMAGE=$(grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '"')
    info "Image : $IMAGE"
    ok "OS release file found"
else
    warn "Could not determine image version"
fi

# ── 3. Enigma2 process running ──────────────────────────────────────────────
echo ""
echo "[3] Enigma2 Process"
if ps 2>/dev/null | grep -q '[e]nigma2'; then
    ok "Enigma2 process is running"
else
    warn "Enigma2 process not detected (may still work)"
fi

# ── 4. Python3 ──────────────────────────────────────────────────────────────
echo ""
echo "[4] Python 3"
if command -v python3 > /dev/null 2>&1; then
    PY=$(python3 --version 2>&1)
    ok "Python3 found: $PY"
else
    fail "Python3 not found - required for this plugin"
fi

# ── 5. Fury-FHD Skin ────────────────────────────────────────────────────────
echo ""
echo "[5] Fury-FHD Skin"
if [ -d "/usr/share/enigma2/Fury-FHD" ]; then
    ok "Fury-FHD skin directory found"
else
    warn "Fury-FHD skin not found at /usr/share/enigma2/Fury-FHD"
fi

ACTIVE_SKIN=$(grep 'primary_skin' /etc/enigma2/settings 2>/dev/null | cut -d= -f2)
if echo "${ACTIVE_SKIN}" | grep -qi 'fury'; then
    ok "Fury-FHD is the active skin: ${ACTIVE_SKIN}"
elif [ -n "${ACTIVE_SKIN}" ]; then
    warn "Active skin is not Fury-FHD: ${ACTIVE_SKIN}"
else
    warn "No primary_skin entry found in settings"
fi

# ── 6. Plugin slot ──────────────────────────────────────────────────────────
echo ""
echo "[6] Plugin Slot"
PLUGIN_DEST="/usr/lib/enigma2/python/Plugins/Extensions/ChannelColors"
if [ -d "${PLUGIN_DEST}" ]; then
    warn "ChannelColors already installed - install.sh will overwrite it"
else
    ok "Plugin slot is clean - ready for fresh install"
fi

# ── 7. wget --no-check-certificate ──────────────────────────────────────────
echo ""
echo "[7] wget Compatibility"
if command -v wget > /dev/null 2>&1; then
    ok "wget found"
    wget -q "--no-check-certificate" \
        https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/check.sh \
        -O /tmp/_ccg_test 2>/dev/null
    if [ $? -eq 0 ] && [ -s /tmp/_ccg_test ]; then
        ok "wget --no-check-certificate fetch from GitHub works"
        rm -f /tmp/_ccg_test
    else
        fail "wget fetch from GitHub failed - check internet connection"
        rm -f /tmp/_ccg_test
    fi
else
    fail "wget not found - required for installer"
fi

# ── 8. Internet connectivity ─────────────────────────────────────────────────
echo ""
echo "[8] Internet"
wget -q "--no-check-certificate" https://github.com -O /dev/null 2>/dev/null
if [ $? -eq 0 ]; then
    ok "Internet connection to github.com works"
else
    fail "Cannot reach github.com - check network/DNS"
fi

# ── 9. Disk space ────────────────────────────────────────────────────────────
echo ""
echo "[9] Disk Space"
PLUGIN_FREE=$(df /usr/lib/enigma2 2>/dev/null | awk 'NR==2{print $4}')
BACKUP_FREE=$(df /etc/enigma2 2>/dev/null | awk 'NR==2{print $4}')

if [ -n "${PLUGIN_FREE}" ] && [ "${PLUGIN_FREE}" -gt 200 ] 2>/dev/null; then
    ok "Plugin partition free: ${PLUGIN_FREE}KB"
else
    warn "Low space on plugin partition: ${PLUGIN_FREE}KB"
fi

if [ -n "${BACKUP_FREE}" ] && [ "${BACKUP_FREE}" -gt 100 ] 2>/dev/null; then
    ok "Backup partition free: ${BACKUP_FREE}KB"
else
    warn "Low space for backup partition: ${BACKUP_FREE}KB"
fi

# ── 10. NCam (optional) ──────────────────────────────────────────────────────
echo ""
echo "[10] NCam / CA Emulator (optional)"
if ps 2>/dev/null | grep -q '[n]cam'; then
    ok "NCam process is running"
else
    warn "NCam not running - decrypted color test will not be possible"
fi

if [ -e "/tmp/camd.socket" ]; then
    ok "DVB-API socket found: /tmp/camd.socket"
elif [ -e "/var/run/camd.socket" ]; then
    ok "DVB-API socket found: /var/run/camd.socket"
else
    warn "No camd.socket found - NCam DVB-API not active"
fi

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo "------------------------------------------------------------------------"
echo "  Results:  ${GREEN}${PASS} PASS${NC}   ${YELLOW}${WARN} WARN${NC}   ${RED}${FAIL} FAIL${NC}"
echo "------------------------------------------------------------------------"
echo ""

if [ "${FAIL}" -gt 0 ]; then
    echo "${RED}NOT READY - fix the FAIL items above before installing.${NC}"
elif [ "${WARN}" -gt 0 ]; then
    echo "${YELLOW}READY WITH WARNINGS - review WARN items above.${NC}"
    echo "${GREEN}To install run:${NC}"
    echo "  wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/install.sh -O - | sh"
else
    echo "${GREEN}ALL CHECKS PASSED - ready to install!${NC}"
    echo ""
    echo "  wget -q \"--no-check-certificate\" https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/install.sh -O - | sh"
fi

echo ""
