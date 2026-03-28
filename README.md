# Enigma2 Channel Colors Plugin

> Colorize your Enigma2 channel list by encryption state — instantly see which channels are **FTA**, **encrypted**, or have **no signal**.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Enigma2-green.svg)
![Tested](https://img.shields.io/badge/tested-OpenATV%207.6-brightgreen.svg)

## Visual Result

| Color | State |
|-------|-------|
| 🟢 Green `#00C800` | Free-to-Air (FTA) |
| 🔴 Red `#FF3232` | Encrypted |
| ⚫ Gray `#888888` | No Signal |

All colors are fully configurable via the plugin settings menu.

## Compatibility

| Image | Status |
|-------|--------|
| OpenATV 7.x | ✅ Tested & Working |
| OpenPLi 9.x | ✅ Compatible |
| BlackHole 3.x | ⚠️ Untested |
| VTi 14.x | ⚠️ Untested |

## How It Works

- Hooks into `ChannelSelectionBase.__init__` at enigma2 startup
- Uses `eServiceCenter.info().isCrypted()` to detect FTA vs encrypted (reads from lamedb)
- Calls `eListbox.setForegroundColor(enc_col)` as base color for all rows
- Marks FTA channels with `addMarked()` → `markedForeground` renders them in FTA color
- Patches `applySkin()` to survive every `setRoot()` skin re-apply
- Removes skin's hardcoded `foregroundColor="white"` that overrides all color slots

## Installation

### Quick Install (Recommended)

```bash
# On your Enigma2 receiver via SSH/Telnet
cd /tmp
wget https://github.com/SamoTech/enigma2-channel-color-guide/archive/main.tar.gz
tar xzf main.tar.gz
cd enigma2-channel-color-guide-main
bash install.sh
killall -9 enigma2
```

### Manual Install

```bash
# Set your enigma2 base path
BASE=""  # or /media/hdd/ImageBoot/openatv-7.6 for ImageBoot
DEST="$BASE/usr/lib/enigma2/python/Plugins/Extensions/ChannelColors"

mkdir -p "$DEST"
cp plugin/*.py "$DEST/"
```

### ⚠️ Required Skin Patch

If your skin has `foregroundColor="white"` hardcoded in the channel list widget (e.g. **Fury-FHD**), you must remove it or colors won't show.

The `install.sh` script does this automatically. To do it manually:

```bash
SKIN="/usr/share/enigma2/YOUR_SKIN/skin.xml"
cp "$SKIN" "$SKIN.bak"   # backup first!

python3 << 'EOF'
path = '/usr/share/enigma2/YOUR_SKIN/skin.xml'
with open(path, 'r') as f:
    c = f.read()
c = c.replace('foregroundColor="white" foregroundColorSelected="#ffffff"',
              'foregroundColorSelected="#ffffff"', 1)
with open(path, 'w') as f:
    f.write(c)
print('Done')
EOF
```

## Configuration

After installation, go to:
**Menu → Plugins → Channel Colors**

Available settings:
- **Plugin Enabled** — Yes/No toggle
- **Encrypted Channel Color** — default `#FF3232` (red)
- **Decrypted Channel Color** — default `#FFD700` (gold, for future NCam integration)
- **Free-to-Air Channel Color** — default `#00C800` (green)

## Uninstall

```bash
bash uninstall.sh
killall -9 enigma2
```

## Technical Notes

### Key Discovery: Why `setColor(slot, color)` API

The correct API is `l.setColor(l.slotName, color)` not `l.setColor(index, color)`.
Slot constants are integer properties on the `eListboxServiceContent` object itself.

### Key Discovery: Skin Override

Fury-FHD skin has `foregroundColor="white"` on the service list widget which overrides
all `setColor()` calls. Must be removed. The `eListbox.setForegroundColor()` method
called directly on the widget bypasses this after `clearForegroundColor()` or removal.

### Key Discovery: applySkin Hook

`setRoot()` triggers `applySkin()` which resets the listbox foreground to the skin's
hardcoded white. Patching `sl.applySkin` to reapply our colors after every call
surprises this reset.

## Debug Log

```bash
cat /tmp/cc_debug.log
```

## License

MIT © [Ossama Hashim (SamoTech)](https://github.com/SamoTech)
