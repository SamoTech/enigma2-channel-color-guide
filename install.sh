#!/bin/sh
# Channel Colors Plugin - Install Script
# SamoTech - https://github.com/SamoTech/enigma2-channel-color-guide

VERSION="1.9.2"
BASE_URL="https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/plugin"
INSTALL_DIR="/usr/lib/enigma2/python/Plugins/Extensions/ChannelColors"

echo "================================"
echo " Channel Colors Plugin v$VERSION"
echo " SamoTech Installer"
echo "================================"

mkdir -p "$INSTALL_DIR"

for FILE in __init__.py plugin.py ColorApplier.py ChannelColorsSetup.py; do
    echo "Downloading $FILE..."
    wget -q --no-check-certificate \
        "$BASE_URL/$FILE" \
        -O "$INSTALL_DIR/$FILE"
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to download $FILE"
        exit 1
    fi
done

INSTALLED_VER=$(grep -m1 "^VERSION" "$INSTALL_DIR/ColorApplier.py" | grep -oE "[0-9]+\.[0-9]+\.[0-9]+")
echo ""
echo "Installed version: v$INSTALLED_VER"

if [ "$INSTALLED_VER" = "$VERSION" ]; then
    echo "Version check: OK"
else
    echo "WARNING: Version mismatch (expected $VERSION, got $INSTALLED_VER)"
fi

echo ""
echo "Done! Restarting enigma2..."
echo "  Colors : White=FTA | Green=NCam | Red=Encrypted"
echo "  Update : Menu -> Plugins -> Channel Colors -> Blue button"
echo ""

init 4 && sleep 2 && init 3
