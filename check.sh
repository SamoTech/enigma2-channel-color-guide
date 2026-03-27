#!/bin/sh
#
# check.sh - Channel Colors Plugin - Pre-Install Checker
# Author: Ossama Hashim (SamoTech)
# License: MIT
# Usage: wget -q "--no-check-certificate" https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/check.sh -O - | sh
#

PASS=0
FAIL=0
WARN=0

# Use tput — works on OpenATV busybox ash without escape sequence issues
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

ok()   { echo "  ${GREEN}[PASS]${NC} $1"; PASS=$((PASS+1)); }
fail() { echo "  ${RED}[FAIL]${NC} $1"; FAIL=$((FAIL+1)); }
warn() { echo "  ${YELLOW}[WARN]${NC} $1"; WARN=$((WARN+1)); }
info() { echo "  ${CYAN}[INFO]${NC} $1"; }

echo ""
echo "------------------------------------------------------------------------"
echo "   Channel Colors Plugin - Pre-Install Checker"
echo "   github.com/SamoTech/enigma2-channel-color-guide"
echo "------------------------------------------------------------------------"
echo ""

# 1. Enigma2 installed
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

# 2. Image version — read only key lines via grep
echo ""
echo "[2] Image Info"
if [ -f "/etc/image-version" ]; then
    _distro=$(grep  '^distro='       /etc/image-version | cut -d= -f2)
    _ver=$(grep     '^imageversion=' /etc/image-version | cut -d= -f2)
    _machine=$(grep '^machine_name=' /etc/image-version | cut -d= -f2)
    _build=$(grep   '^imagebuild='   /etc/image-version | cut -d= -f2)
    info "Image  : ${_distro} ${_ver} (build ${_build})"
    info "Machine: ${_machine}"
    ok "Image version file found"
elif [ -f "/etc/os-release" ]; then
    _pretty=$(grep PRETTY_NAME /etc/os-release | cut -d= -f2 | tr -d '"')
    info "Image: ${_pretty}"
    ok "OS release file found"
else
    warn "Could not determine image version"
fi

# 3. Enigma2 process
echo ""
echo "[3] Enigma2 Process"
if ps 2>/dev/null | grep -q '[e]nigma2'; then
    ok "Enigma2 process is running"
else
    warn "Enigma2 process not detected (normal if restarting)"
fi

# 4. Python3
echo ""
echo "[4] Python 3"
if command -v python3 > /dev/null 2>&1; then
    PY=$(python3 --version 2>&1)
    ok "$PY"
else
    fail "Python3 not found - required for this plugin"
fi

# 5. Fury-FHD Skin
echo ""
echo "[5] Fury-FHD Skin"
if [ -d "/usr/share/enigma2/Fury-FHD" ]; then
    ok "Fury-FHD skin directory found"
else
    warn "Fury-FHD skin not found at /usr/share/enigma2/Fury-FHD"
fi
ACTIVE_SKIN=$(grep 'primary_skin' /etc/enigma2/settings 2>/dev/null | cut -d= -f2)
if echo "${ACTIVE_SKIN}" | grep -qi 'fury'; then
    ok "Active skin: ${ACTIVE_SKIN}"
elif [ -n "${ACTIVE_SKIN}" ]; then
    warn "Active skin is not Fury-FHD: ${ACTIVE_SKIN}"
else
    warn "No primary_skin entry in settings"
fi

# 6. Plugin slot
echo ""
echo "[6] Plugin Slot"
PLUGIN_DEST="/usr/lib/enigma2/python/Plugins/Extensions/ChannelColors"
if [ -d "${PLUGIN_DEST}" ]; then
    warn "ChannelColors already installed - will be overwritten"
else
    ok "Plugin slot is clean - ready for fresh install"
fi

# 7. wget
echo ""
echo "[7] wget Compatibility"
if command -v wget > /dev/null 2>&1; then
    ok "wget found"
    wget -q "--no-check-certificate" \
        https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/check.sh \
        -O /tmp/_ccg_test 2>/dev/null
    if [ $? -eq 0 ] && [ -s /tmp/_ccg_test ]; then
        ok "wget --no-check-certificate fetch from GitHub works"
    else
        fail "wget fetch from GitHub failed"
    fi
    rm -f /tmp/_ccg_test
else
    fail "wget not found"
fi

# 8. Internet
echo ""
echo "[8] Internet"
wget -q "--no-check-certificate" https://github.com -O /dev/null 2>/dev/null
if [ $? -eq 0 ]; then
    ok "github.com reachable"
else
    fail "Cannot reach github.com - check network"
fi

# 9. Disk space — use df -k and grep the mount point
echo ""
echo "[9] Disk Space"

# Get the filesystem line for a path robustly on busybox
df_avail() {
    # prints available KB for given path
    df -k "$1" 2>/dev/null | grep -v '^Filesystem' | tail -1 | awk '{print $4}'
}

PLUGIN_FREE=$(df_avail /usr/lib/enigma2)
BACKUP_FREE=$(df_avail /etc/enigma2)

if [ -n "${PLUGIN_FREE}" ] && [ "${PLUGIN_FREE}" -gt 200 ] 2>/dev/null; then
    ok "Plugin partition free: ${PLUGIN_FREE} KB"
else
    warn "Low space on plugin partition: ${PLUGIN_FREE} KB"
fi
if [ -n "${BACKUP_FREE}" ] && [ "${BACKUP_FREE}" -gt 100 ] 2>/dev/null; then
    ok "Backup partition free: ${BACKUP_FREE} KB"
else
    warn "Low space on backup partition: ${BACKUP_FREE} KB"
fi
info "$(df -h /usr/lib/enigma2 2>/dev/null | tail -1)"

# 10. NCam
echo ""
echo "[10] NCam / CA Emulator (optional)"
if ps 2>/dev/null | grep -q '[n]cam'; then
    ok "NCam process is running"
else
    warn "NCam not running - decrypted color test not possible yet"
fi
if [ -e "/tmp/camd.socket" ]; then
    ok "DVB-API socket: /tmp/camd.socket"
elif [ -e "/var/run/camd.socket" ]; then
    ok "DVB-API socket: /var/run/camd.socket"
else
    warn "No camd.socket - NCam DVB-API not active"
fi

# Summary
echo ""
echo "------------------------------------------------------------------------"
echo "  Results:  ${GREEN}${PASS} PASS${NC}   ${YELLOW}${WARN} WARN${NC}   ${RED}${FAIL} FAIL${NC}"
echo "------------------------------------------------------------------------"
echo ""

if [ "${FAIL}" -gt 0 ]; then
    echo "  ${RED}NOT READY${NC} - fix FAIL items above before installing."
elif [ "${WARN}" -gt 0 ]; then
    echo "  ${YELLOW}READY WITH WARNINGS${NC} - review WARN items above."
    echo ""
    echo "  ${GREEN}To install:${NC}"
    echo '  wget -q "--no-check-certificate" https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/install.sh -O - | sh'
else
    echo "  ${GREEN}ALL CHECKS PASSED - ready to install!${NC}"
    echo ""
    echo '  wget -q "--no-check-certificate" https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/install.sh -O - | sh'
fi
echo ""
