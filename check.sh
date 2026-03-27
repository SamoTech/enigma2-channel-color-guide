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

# printf-based colors — compatible with busybox ash /bin/sh on OpenATV
GREEN=$(printf '\033[0;32m')
RED=$(printf '\033[0;31m')
YELLOW=$(printf '\033[1;33m')
CYAN=$(printf '\033[0;36m')
NC=$(printf '\033[0m')

ok()   { printf "${GREEN}  [PASS]${NC} %s\n" "$1"; PASS=$((PASS+1)); }
fail() { printf "${RED}  [FAIL]${NC} %s\n" "$1"; FAIL=$((FAIL+1)); }
warn() { printf "${YELLOW}  [WARN]${NC} %s\n" "$1"; WARN=$((WARN+1)); }
info() { printf "${CYAN}  [INFO]${NC} %s\n" "$1"; }

printf "\n"
printf "------------------------------------------------------------------------\n"
printf "         Channel Colors Plugin - Pre-Install Checker                   \n"
printf "         github.com/SamoTech/enigma2-channel-color-guide               \n"
printf "------------------------------------------------------------------------\n"
printf "\n"

# 1. Enigma2 installed
printf "[1] Enigma2 Environment\n"
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

# 2. Image version
printf "\n[2] Image Info\n"
if [ -f "/etc/image-version" ]; then
    # Extract just the key fields — not the full multiline dump
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

# 3. Enigma2 process running
printf "\n[3] Enigma2 Process\n"
if ps 2>/dev/null | grep -q '[e]nigma2'; then
    ok "Enigma2 process is running"
else
    warn "Enigma2 process not detected (normal if GUI crashed or restarting)"
fi

# 4. Python3
printf "\n[4] Python 3\n"
if command -v python3 > /dev/null 2>&1; then
    PY=$(python3 --version 2>&1)
    ok "Python3 found: $PY"
else
    fail "Python3 not found - required for this plugin"
fi

# 5. Fury-FHD Skin
printf "\n[5] Fury-FHD Skin\n"
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

# 6. Plugin slot
printf "\n[6] Plugin Slot\n"
PLUGIN_DEST="/usr/lib/enigma2/python/Plugins/Extensions/ChannelColors"
if [ -d "${PLUGIN_DEST}" ]; then
    warn "ChannelColors already installed - install.sh will overwrite it"
else
    ok "Plugin slot is clean - ready for fresh install"
fi

# 7. wget --no-check-certificate
printf "\n[7] wget Compatibility\n"
if command -v wget > /dev/null 2>&1; then
    ok "wget found"
    wget -q "--no-check-certificate" \
        https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/check.sh \
        -O /tmp/_ccg_test 2>/dev/null
    if [ $? -eq 0 ] && [ -s /tmp/_ccg_test ]; then
        ok "wget --no-check-certificate fetch from GitHub works"
    else
        fail "wget fetch from GitHub failed - check internet connection"
    fi
    rm -f /tmp/_ccg_test
else
    fail "wget not found - required for installer"
fi

# 8. Internet connectivity
printf "\n[8] Internet\n"
wget -q "--no-check-certificate" https://github.com -O /dev/null 2>/dev/null
if [ $? -eq 0 ]; then
    ok "Internet connection to github.com works"
else
    fail "Cannot reach github.com - check network/DNS"
fi

# 9. Disk space — busybox df outputs differently, use tail+tr to normalize
printf "\n[9] Disk Space\n"

# Get available KB — busybox df may wrap long lines, so join and take last numeric field before %
PLUGIN_FREE=$(df /usr/lib/enigma2 2>/dev/null | tail -1 | tr -s ' ' | cut -d' ' -f4)
BACKUP_FREE=$(df /etc/enigma2   2>/dev/null | tail -1 | tr -s ' ' | cut -d' ' -f4)

# Strip any non-numeric characters (e.g. trailing K)
PLUGIN_FREE=$(printf '%s' "${PLUGIN_FREE}" | tr -cd '0-9')
BACKUP_FREE=$(printf '%s' "${BACKUP_FREE}" | tr -cd '0-9')

if [ -n "${PLUGIN_FREE}" ] && [ "${PLUGIN_FREE}" -gt 200 ] 2>/dev/null; then
    ok "Plugin partition free: ${PLUGIN_FREE} KB"
else
    warn "Low or unknown space on plugin partition: ${PLUGIN_FREE} KB"
fi

if [ -n "${BACKUP_FREE}" ] && [ "${BACKUP_FREE}" -gt 100 ] 2>/dev/null; then
    ok "Backup partition free: ${BACKUP_FREE} KB"
else
    warn "Low or unknown space on backup partition: ${BACKUP_FREE} KB"
fi

# Also print human-readable df for reference
info "df /usr/lib/enigma2 : $(df -h /usr/lib/enigma2 2>/dev/null | tail -1 | tr -s ' ')"
info "df /etc/enigma2     : $(df -h /etc/enigma2 2>/dev/null | tail -1 | tr -s ' ')"

# 10. NCam (optional)
printf "\n[10] NCam / CA Emulator (optional)\n"
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

# Summary
printf "\n"
printf "------------------------------------------------------------------------\n"
printf "  Results:  ${GREEN}%s PASS${NC}   ${YELLOW}%s WARN${NC}   ${RED}%s FAIL${NC}\n" "${PASS}" "${WARN}" "${FAIL}"
printf "------------------------------------------------------------------------\n"
printf "\n"

if [ "${FAIL}" -gt 0 ]; then
    printf "${RED}NOT READY - fix the FAIL items above before installing.${NC}\n"
elif [ "${WARN}" -gt 0 ]; then
    printf "${YELLOW}READY WITH WARNINGS - review WARN items above.${NC}\n"
    printf "${GREEN}To install run:${NC}\n"
    printf '  wget -q "--no-check-certificate" https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/install.sh -O - | sh\n'
else
    printf "${GREEN}ALL CHECKS PASSED - ready to install!${NC}\n"
    printf "\n"
    printf '  wget -q "--no-check-certificate" https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/install.sh -O - | sh\n'
fi

printf "\n"
