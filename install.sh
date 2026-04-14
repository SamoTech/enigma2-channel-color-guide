#!/bin/sh
# Channel Colors Plugin - Install Script
# SamoTech - https://github.com/SamoTech/enigma2-channel-color-guide

VERSION="1.7.0"
BASE_URL="https://raw.githubusercontent.com/SamoTech/enigma2-channel-color-guide/main/plugin"
INSTALL_DIR="/usr/lib/enigma2/python/Plugins/Extensions/ChannelColors"

echo "================================"
echo " Channel Colors Plugin v$VERSION"
echo " SamoTech Installer"
echo "================================"

# Create install dir
mkdir -p "$INSTALL_DIR"

# Download files
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

# Verify version
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
echo "  After restart open: Menu -> Plugins -> Channel Colors v$VERSION"
echo "  Colors: White=FTA | Green=NCam | Red=Encrypted"
echo ""

# Restart enigma2
init 4 && sleep 2 && init 3
