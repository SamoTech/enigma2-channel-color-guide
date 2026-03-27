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

# Colors via tput
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

# 2. Image version
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
if pidof enigma2 > /dev/null 2>&1; then
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

# 9. CA Emulator detection
# Uses /proc/*/exe symlinks - handles versioned binaries like ncam-15.7
echo ""
echo "[9] CA Emulator (for decryption color)"

EMU_FOUND=0
EMU_NAME=""
EMU_BIN=""

for _p in /proc/[0-9]*/exe; do
    _target=$(readlink "$_p" 2>/dev/null | tr 'A-Z' 'a-z')
    [ -z "$_target" ] && continue
    case "$_target" in
        *ncam*)  EMU_NAME="NCam";  EMU_BIN="$_target"; EMU_FOUND=1; break ;;
        *oscam*) EMU_NAME="OSCam"; EMU_BIN="$_target"; EMU_FOUND=1; break ;;
        *cccam*) EMU_NAME="CCcam"; EMU_BIN="$_target"; EMU_FOUND=1; break ;;
        *mgcamd*)EMU_NAME="MGcamd";EMU_BIN="$_target"; EMU_FOUND=1; break ;;
        *gbox*)  EMU_NAME="Gbox";  EMU_BIN="$_target"; EMU_FOUND=1; break ;;
    esac
done

if [ "${EMU_FOUND}" -eq 1 ]; then
    ok "CA emulator running: ${EMU_NAME} (${EMU_BIN})"
else
    warn "No CA emulator detected (NCam/OSCam/CCcam/MGcamd/Gbox)"
    info "Install an emulator for the decrypted channel color to work"
fi

# DVB-API check: first try socket file, then fall back to config parsing
DVBAPI_OK=0

# 1) Check known socket paths
for _sock in /tmp/camd.socket /var/run/camd.socket /tmp/.ncam/camd.socket /tmp/.oscam/camd.socket; do
    if [ -e "$_sock" ]; then
        ok "DVB-API active: socket found at ${_sock}"
        DVBAPI_OK=1
        break
    fi
done

# 2) If no socket, check config files directly for enabled=1
if [ "${DVBAPI_OK}" -eq 0 ]; then
    for _conf in /etc/ncam/ncam.conf /etc/NCam/ncam.conf /etc/oscam/oscam.conf; do
        if [ -f "$_conf" ]; then
            # Check [dvbapi] section has enabled=1
            _dvb_enabled=$(awk '/\[dvbapi\]/{f=1} f && /enabled/{print;exit}' "$_conf" 2>/dev/null | grep -c 'enabled.*=.*1')
            if [ "${_dvb_enabled}" -gt 0 ]; then
                ok "DVB-API enabled in config: ${_conf}"
                info "Socket not yet created - will appear after first channel tune"
                DVBAPI_OK=1
                break
            fi
        fi
    done
fi

# 3) Still nothing
if [ "${DVBAPI_OK}" -eq 0 ]; then
    if [ "${EMU_FOUND}" -eq 1 ]; then
        warn "DVB-API not enabled - set enabled=1 in ${EMU_NAME} dvbapi config"
    else
        warn "DVB-API not configured"
    fi
fi

# Config dir hint
if [ "${EMU_FOUND}" -eq 1 ]; then
    _emu_lower=$(echo "${EMU_NAME}" | tr 'A-Z' 'a-z')
    for _dir in "/etc/${_emu_lower}" "/etc/NCam" "/etc/ncam" "/etc/oscam"; do
        if [ -d "$_dir" ]; then
            info "Config dir: ${_dir}"
            break
        fi
    done
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
